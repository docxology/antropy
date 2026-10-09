# Copyright (c) 2026 Daniel Ari Friedman
"""Real-file adversarial controls for complete numerical trial replay."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
import yaml
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from scripts.result_replay import numeric_equivalent
from scripts.run_study import execute_study
from scripts.study_analysis import record_rows, summarize
from scripts.study_models import StudyReport, StudySummary
from scripts.study_plot_helpers import CurveAppearance, draw_summary
from scripts.validate_study import validate_study


@pytest.fixture(scope="module")
def small_study(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("replicated-study")
    source = Path(__file__).resolve().parents[1] / "study_plan.yaml"
    plan = yaml.safe_load(source.read_text())
    plan.update(
        shapes=[[12], [5, 6]],
        mixing_probabilities=[0.0, 1.0],
        controls=["constant", "gaussian"],
        replicates=2,
        radii=[1.5, 2.0],
    )
    (root / "study_plan.yaml").write_text(yaml.safe_dump(plan))
    report = execute_study(root, root / "study_plan.yaml")
    expected_rows = sum(len(record_rows(record)) for record in report.records)
    assert validate_study(root) == expected_rows
    return root


@pytest.fixture
def study_files(tmp_path: Path, small_study: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(small_study, root)
    return root


def save_report(root: Path, payload: dict[str, JsonValue]) -> None:
    (root / "output/study/report.json").write_text(json.dumps(payload))


def test_removing_trial_fails_even_with_coherent_tables(study_files: Path) -> None:
    path = study_files / "output/study/report.json"
    payload = json.loads(path.read_text())
    payload["records"].pop()
    save_report(study_files, payload)
    report = StudyReport.model_validate(payload)
    rows = [row for record in report.records for row in record_rows(record)]
    with (study_files / "output/study/results.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].model_dump()))
        writer.writeheader()
        writer.writerows(row.model_dump(mode="json") for row in rows)
    (study_files / "output/study/summary.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in summarize(rows)])
    )
    with pytest.raises(ParameterError, match="matrix"):
        validate_study(study_files)


def test_changed_entropy_fails_real_kernel_replay(study_files: Path) -> None:
    path = study_files / "output/study/report.json"
    payload = json.loads(path.read_text())
    payload["records"][0]["symbols"]["results"]["shannon"]["value"] += 0.1
    save_report(study_files, payload)
    with pytest.raises(ParameterError, match="numerical replay"):
        validate_study(study_files)


def test_duplicate_trial_fails(study_files: Path) -> None:
    path = study_files / "output/study/report.json"
    payload = json.loads(path.read_text())
    payload["records"][1] = payload["records"][0]
    save_report(study_files, payload)
    with pytest.raises(ParameterError, match="matrix"):
        validate_study(study_files)


def test_wrong_flattened_input_hash_fails(study_files: Path) -> None:
    path = study_files / "output/study/report.json"
    payload = json.loads(path.read_text())
    payload["records"][0]["flattened"]["input_sha256"] = "0" * 64
    save_report(study_files, payload)
    with pytest.raises(ParameterError, match="Transformed"):
        validate_study(study_files)


def test_aggregate_cannot_invent_undefined_trials(study_files: Path) -> None:
    path = study_files / "output/study/summary.json"
    summary = json.loads(path.read_text())
    summary[0]["n_undefined"] += 1
    path.write_text(json.dumps(summary))
    with pytest.raises(ParameterError, match="Aggregates"):
        validate_study(study_files)


def test_summary_boolean_cannot_stand_for_zero_count(study_files: Path) -> None:
    path = study_files / "output/study/summary.json"
    summary = json.loads(path.read_text())
    record = next(row for row in summary if row["n_undefined"] == 0)
    record["n_undefined"] = False
    path.write_text(json.dumps(summary))
    with pytest.raises(ParameterError, match="Aggregates"):
        validate_study(study_files)


def test_duplicate_identical_csv_column_is_rejected(study_files: Path) -> None:
    path = study_files / "output/study/results.csv"
    with path.open(newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows[0][0] == "case_id"
    with path.open("w", newline="") as stream:
        csv.writer(stream).writerows([[row[0], *row] for row in rows])
    with pytest.raises(ParameterError, match="header"):
        validate_study(study_files)


def test_cost_plan_cannot_invent_component_counts(study_files: Path) -> None:
    path = study_files / "output/study/complexity.json"
    report = json.loads(path.read_text())
    report["records"][0]["distance_component_visits"] = 1
    path.write_text(json.dumps(report))
    with pytest.raises(ParameterError, match="Computational"):
        validate_study(study_files)


def test_infeasible_study_creates_no_partial_outputs(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[1] / "study_plan.yaml"
    plan = yaml.safe_load(source.read_text())
    plan["max_memory_bytes"] = 1024
    path = tmp_path / "study_plan.yaml"
    path.write_text(yaml.safe_dump(plan))
    with pytest.raises(ParameterError, match="Infeasible"):
        execute_study(tmp_path, path)
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(("left", "right"), [(True, 1), (1, True), (1, 1.0), (None, 0), ("1", 1)])
def test_discrete_evidence_cannot_change_type(left: JsonValue, right: JsonValue) -> None:
    assert not numeric_equivalent(left, right)


def test_singleton_has_no_errorbar_and_absent_mean_breaks_line() -> None:
    common = {
        "shape": "8",
        "dimension": 1,
        "family": "mix",
        "geometry": "native",
        "analysis_id": "hdse",
        "measure": "hdse",
        "radius": 2.0,
        "n_total": 2,
        "n_infinite": 0,
    }
    rows = [
        StudySummary.model_validate(
            common
            | {
                "mixing": 0.0,
                "n_finite": 1,
                "n_undefined": 1,
                "finite_mean": 1.0,
                "finite_sample_sd": None,
            }
        ),
        StudySummary.model_validate(
            common
            | {
                "mixing": 0.5,
                "n_finite": 0,
                "n_undefined": 2,
                "finite_mean": None,
                "finite_sample_sd": None,
            }
        ),
        StudySummary.model_validate(
            common
            | {
                "mixing": 1.0,
                "n_finite": 2,
                "n_undefined": 0,
                "finite_mean": 2.0,
                "finite_sample_sd": 0.5,
            }
        ),
    ]
    figure, axis = plt.subplots()
    draw_summary(axis, rows, CurveAppearance("#0072B2", "example"))
    assert np.isnan(axis.lines[0].get_ydata()[1])
    assert [text.get_text() for text in axis.texts] == ["n=1"]
    assert len(axis.collections[0].get_segments()) == 1
    plt.close(figure)
