# Copyright (c) 2026 Daniel Ari Friedman
"""Real retained-field corruption controls for the independent prospective-power gate."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import ValidationError

from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.orchestration import array_sha256, canonical_json
from scripts.artifact_io import digest
from scripts.power_models import PowerReport
from scripts.power_plan import PowerPlan
from scripts.power_serialization import decision_csv, summary_csv
from scripts.run_power import run_power
from scripts.validate_power import validate_power
from tests.power_validation_fixtures import power_files as power_files  # noqa: PLC0414
from tests.power_validation_fixtures import small_power as small_power  # noqa: PLC0414


def load_report(root: Path) -> PowerReport:
    return PowerReport.model_validate_json((root / "output/power/report.json").read_bytes())


def write_report(root: Path, report: PowerReport) -> None:
    """Alter a complete coherent snapshot, including both canonical CSV projections."""
    _ = (root / "output/power/report.json").write_text(
        canonical_json(report.model_dump(mode="json"))
    )
    _ = (root / "output/power/decisions.csv").write_text(decision_csv(report.experiments).text())
    _ = (root / "output/power/summary.csv").write_text(summary_csv(report.summaries).text())


def test_complete_real_power_design_replays(small_power: Path) -> None:
    # Given a real small prospective run.
    # When all persisted fields and decisions are independently replayed.
    report = validate_power(small_power)
    # Then both inference modes and unavailable comparisons remain explicit.
    assert {schedule.method for schedule in report.resources.schedules} == {"exact", "monte_carlo"}
    assert {row.status for row in report.experiments} == {"available", "unavailable"}


@pytest.mark.parametrize("collection", ["pools", "estimates", "experiments", "summaries"])
def test_coherently_omitted_matrix_cell_fails(power_files: Path, collection: str) -> None:
    report = load_report(power_files)
    data = report.model_dump(mode="json")
    data[collection].pop()
    changed = PowerReport.model_validate(data)
    write_report(power_files, changed)
    with pytest.raises(ParameterError, match="matrix"):
        _ = validate_power(power_files)


@pytest.mark.parametrize("collection", ["pools", "estimates", "experiments", "summaries"])
def test_duplicate_matrix_cell_fails(power_files: Path, collection: str) -> None:
    data = load_report(power_files).model_dump(mode="json")
    data[collection][1] = data[collection][0]
    write_report(power_files, PowerReport.model_validate(data))
    with pytest.raises(ParameterError, match="duplicated"):
        _ = validate_power(power_files)


def test_coherently_rehashed_pool_cannot_replace_seeded_fields(power_files: Path) -> None:
    report = load_report(power_files)
    pool = report.pools[0]
    path = power_files / pool.input_file
    array = np.load(path, allow_pickle=False)
    array[0, ...] += 0.1
    np.save(path, array, allow_pickle=False)
    changed_pool = pool.model_copy(
        update={"file_sha256": digest(path), "array_sha256": array_sha256(array)}
    )
    changed_field = report.estimates[0].model_copy(update={"input_sha256": array_sha256(array[0])})
    write_report(
        power_files,
        report.model_copy(
            update={
                "pools": (changed_pool, *report.pools[1:]),
                "estimates": (changed_field, *report.estimates[1:]),
            }
        ),
    )
    with pytest.raises(ParameterError, match="seeded design replay"):
        _ = validate_power(power_files)


def test_changed_entropy_cannot_be_hidden_by_coherent_csv(power_files: Path) -> None:
    report = load_report(power_files)
    field = report.estimates[0]
    entropy = field.results["shannon"].model_copy(update={"value": 0.123})
    changed = field.model_copy(update={"results": field.results | {"shannon": entropy}})
    write_report(
        power_files, report.model_copy(update={"estimates": (changed, *report.estimates[1:])})
    )
    with pytest.raises(ParameterError, match="kernel replay"):
        _ = validate_power(power_files)


def test_adjusted_p_value_cannot_select_a_smaller_family(power_files: Path) -> None:
    report = load_report(power_files)
    index = next(
        i for i, row in enumerate(report.experiments) if row.p_value is not None and row.p_value < 1
    )
    row = report.experiments[index]
    changed = row.model_copy(update={"adjusted_p_value": row.p_value})
    decisions = tuple(changed if i == index else item for i, item in enumerate(report.experiments))
    write_report(power_files, report.model_copy(update={"experiments": decisions}))
    with pytest.raises(ParameterError, match="inference or fixed-family replay"):
        _ = validate_power(power_files)


@pytest.mark.parametrize("seed", ["seed", "inner_seed"])
def test_changed_consumed_seed_cannot_be_rehashed_away(power_files: Path, seed: str) -> None:
    report = load_report(power_files)
    path = power_files / "power_plan.yaml"
    data = yaml.safe_load(path.read_text())
    if seed == "seed":
        data["seed"] += 1
    else:
        data["test"]["seed"] += 1
    _ = path.write_text(yaml.safe_dump(data, sort_keys=False))
    changed = PowerPlan.model_validate(data)
    write_report(
        power_files, report.model_copy(update={"plan": changed, "plan_sha256": digest(path)})
    )
    with pytest.raises(
        ParameterError, match=r"seeded design replay|inference or fixed-family replay"
    ):
        _ = validate_power(power_files)


@pytest.mark.parametrize("operation", ["header", "row", "value"])
def test_csv_projection_cannot_drop_or_duplicate_evidence(
    power_files: Path, operation: str
) -> None:
    path = power_files / "output/power/decisions.csv"
    with path.open(newline="") as stream:
        rows = list(csv.reader(stream))
    if operation == "header":
        rows = [[row[0], *row] for row in rows]
    elif operation == "row":
        _ = rows.pop()
    else:
        rows[1][-1] = "null"
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerows(rows)
    with pytest.raises(ParameterError, match="CSV"):
        _ = validate_power(power_files)


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "1e999"])
def test_nonfinite_json_fails_before_typed_projection(power_files: Path, literal: str) -> None:
    path = power_files / "output/power/report.json"
    _ = path.write_text(
        path.read_text().replace('"schema_version":1', f'"hidden":{literal},"schema_version":1', 1)
    )
    with pytest.raises(ParameterError, match="JSON"):
        _ = validate_power(power_files)


def test_duplicate_json_key_fails(power_files: Path) -> None:
    path = power_files / "output/power/report.json"
    _ = path.write_text(
        path.read_text().replace('"schema_version":1', '"schema_version":1,"schema_version":1', 1)
    )
    with pytest.raises(ParameterError, match="duplicate JSON"):
        _ = validate_power(power_files)


@pytest.mark.parametrize(
    "field", ["max_distance_component_visits", "max_inference_work", "max_pool_bytes"]
)
def test_preflight_budget_failure_creates_no_partial_outputs(
    tmp_path: Path, small_power: Path, field: str
) -> None:
    data = yaml.safe_load((small_power / "power_plan.yaml").read_text())
    data[field] = 1024 if field == "max_pool_bytes" else 1
    path = tmp_path / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(data))
    with pytest.raises(ParameterError):
        _ = run_power(tmp_path, path)
    assert not (tmp_path / "output").exists()


def test_report_budget_failure_preserves_failed_pool_evidence(
    tmp_path: Path, small_power: Path
) -> None:
    data = yaml.safe_load((small_power / "power_plan.yaml").read_text())
    data["max_report_bytes"] = 1024
    path = tmp_path / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(data))
    with pytest.raises(ResourceError):
        _ = run_power(tmp_path, path)
    assert tuple((tmp_path / "output/power/pools").glob("*.npy"))
    assert not (tmp_path / "output/power/report.json").exists()


@pytest.mark.parametrize(
    "relative",
    [
        "output/power/summary.csv",
        "output/power/figures/rejection-rates.pdf",
        "output/power/figures/availability-calibration.png",
    ],
)
def test_missing_required_power_artifact_fails(power_files: Path, relative: str) -> None:
    (power_files / relative).unlink()
    with pytest.raises(ParameterError, match="missing"):
        _ = validate_power(power_files)


def test_report_boolean_cannot_stand_for_a_count(power_files: Path) -> None:
    path = power_files / "output/power/report.json"
    data = json.loads(path.read_text())
    data["experiments"][0]["replicate"] = False
    _ = path.write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        _ = validate_power(power_files)
