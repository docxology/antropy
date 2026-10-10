# Copyright (c) 2026 Daniel Ari Friedman
"""Tensor custody, path confinement and interval corruption controls using real files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Literal, assert_never

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import array_sha256, canonical_json
from scripts.artifact_io import digest
from scripts.power_models import PowerReport
from scripts.power_serialization import decision_csv, summary_csv
from scripts.validate_power import validate_power
from tests.power_validation_fixtures import power_files as power_files  # noqa: PLC0414
from tests.power_validation_fixtures import small_power as small_power  # noqa: PLC0414


def _report(root: Path) -> PowerReport:
    return PowerReport.model_validate_json((root / "output/power/report.json").read_bytes())


def _save(root: Path, report: PowerReport) -> None:
    _ = (root / "output/power/report.json").write_text(
        canonical_json(report.model_dump(mode="json"))
    )
    _ = (root / "output/power/decisions.csv").write_text(decision_csv(report.experiments).text())
    _ = (root / "output/power/summary.csv").write_text(summary_csv(report.summaries).text())


@pytest.mark.parametrize("kind", ["dtype", "shape", "nonfinite"])
def test_rehashed_tensor_must_keep_declared_representation(
    power_files: Path, kind: Literal["dtype", "shape", "nonfinite"]
) -> None:
    report = _report(power_files)
    pool = report.pools[0]
    path = power_files / pool.input_file
    array = np.load(path, allow_pickle=False)
    match kind:
        case "dtype":
            changed = array.astype(np.float32)
        case "shape":
            changed = array.reshape(-1)
        case "nonfinite":
            changed = array.copy()
            changed[0, ...] = np.nan
        case unreachable:
            assert_never(unreachable)
    np.save(path, changed, allow_pickle=False)
    replacement = pool.model_copy(
        update={"file_sha256": digest(path), "array_sha256": array_sha256(changed)}
    )
    _save(power_files, report.model_copy(update={"pools": (replacement, *report.pools[1:])}))
    with pytest.raises(ParameterError, match="tensor shape"):
        _ = validate_power(power_files)


@pytest.mark.parametrize("which", ["file_sha256", "array_sha256"])
def test_tensor_hash_claims_bind_actual_bytes(power_files: Path, which: str) -> None:
    report = _report(power_files)
    changed = report.pools[0].model_copy(update={which: "0" * 64})
    _save(power_files, report.model_copy(update={"pools": (changed, *report.pools[1:])}))
    with pytest.raises(ParameterError, match="hash differs"):
        _ = validate_power(power_files)


@pytest.mark.parametrize("which", ["field_id", "input_sha256", "results"])
def test_subject_identity_and_analysis_coverage_bind_real_input(
    power_files: Path, which: str
) -> None:
    report = _report(power_files)
    field = report.estimates[0]
    updates = {
        "field_id": "unknown-subject",
        "input_sha256": "0" * 64,
        "results": {key: value for key, value in field.results.items() if key != "shannon"},
    }
    changed = field.model_copy(update={which: updates[which]})
    _save(power_files, report.model_copy(update={"estimates": (changed, *report.estimates[1:])}))
    with pytest.raises(ParameterError, match="Subject identity"):
        _ = validate_power(power_files)


def test_pool_symlink_cannot_escape_project(power_files: Path, tmp_path: Path) -> None:
    report = _report(power_files)
    path = power_files / report.pools[0].input_file
    outside = tmp_path / "outside.npy"
    _ = shutil.copyfile(path, outside)
    path.unlink()
    path.symlink_to(outside)
    with pytest.raises(ParameterError, match="escapes repository"):
        _ = validate_power(power_files)


def test_extra_tensor_cannot_enter_scientific_artifact_set(power_files: Path) -> None:
    report = _report(power_files)
    _ = shutil.copyfile(
        power_files / report.pools[0].input_file, power_files / "output/power/pools/undeclared.npy"
    )
    with pytest.raises(ParameterError, match="undeclared"):
        _ = validate_power(power_files)


@pytest.mark.parametrize(
    "field", ["scenario_id", "shape", "replicate", "group", "subjects", "input_file"]
)
def test_pool_metadata_must_equal_the_prespecified_unit(power_files: Path, field: str) -> None:
    report = _report(power_files)
    updates = {
        "scenario_id": "other",
        "shape": (2, 6),
        "replicate": 9,
        "group": "second",
        "subjects": 5,
        "input_file": "../escape.npy",
    }
    changed = report.pools[0].model_copy(update={field: updates[field]})
    _save(power_files, report.model_copy(update={"pools": (changed, *report.pools[1:])}))
    with pytest.raises(ParameterError, match="Pool identity"):
        _ = validate_power(power_files)


def test_preflight_counts_cannot_be_invented(power_files: Path) -> None:
    report = _report(power_files)
    changed = report.resources.model_copy(update={"fields": report.resources.fields + 1})
    _save(power_files, report.model_copy(update={"resources": changed}))
    with pytest.raises(ParameterError, match="resource preflight"):
        _ = validate_power(power_files)


def test_changed_consumed_plan_hash_is_rejected(power_files: Path) -> None:
    report = _report(power_files)
    _save(power_files, report.model_copy(update={"plan_sha256": "0" * 64}))
    with pytest.raises(ParameterError, match="byte snapshot"):
        _ = validate_power(power_files)


def test_rejection_flags_cannot_change_the_actual_test(power_files: Path) -> None:
    report = _report(power_files)
    index = next(i for i, row in enumerate(report.experiments) if row.status == "available")
    changed = report.experiments[index].model_copy(update={"raw_rejected": True, "rejected": True})
    rows = tuple(changed if i == index else row for i, row in enumerate(report.experiments))
    _save(power_files, report.model_copy(update={"experiments": rows}))
    with pytest.raises(ParameterError, match="inference or fixed-family replay"):
        _ = validate_power(power_files)


def test_summary_pointwise_interval_is_recomputed(power_files: Path) -> None:
    report = _report(power_files)
    summary = report.summaries[0]
    interval = summary.unconditional_rejection.model_copy(update={"upper": 0.987})
    changed = summary.model_copy(update={"unconditional_rejection": interval})
    _save(power_files, report.model_copy(update={"summaries": (changed, *report.summaries[1:])}))
    with pytest.raises(ParameterError, match="interval replay"):
        _ = validate_power(power_files)


@pytest.mark.parametrize("format_", ["png", "pdf"])
def test_invalid_physical_plot_signature_fails(power_files: Path, format_: str) -> None:
    path = power_files / f"output/power/figures/rejection-rates.{format_}"
    _ = path.write_bytes(b"corrupt physical figure")
    with pytest.raises(ParameterError, match="format signature"):
        _ = validate_power(power_files)


def test_summary_count_cannot_be_a_boolean(power_files: Path) -> None:
    path = power_files / "output/power/report.json"
    data = json.loads(path.read_text())
    data["summaries"][0]["unavailable"] = False
    _ = path.write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        _ = validate_power(power_files)


def test_validator_applies_report_byte_budget_before_parsing(power_files: Path) -> None:
    path = power_files / "output/power/report.json"
    with path.open("a") as stream:
        _ = stream.write(" " * 2000001)
    with pytest.raises(ParameterError, match="byte budget"):
        _ = validate_power(power_files)


def test_real_fixture_contains_finite_infinite_and_undefined_fields(small_power: Path) -> None:
    report = validate_power(small_power)
    statuses = {
        result.status.value for field in report.estimates for result in field.results.values()
    }
    assert statuses == {"finite", "infinite", "undefined"}
