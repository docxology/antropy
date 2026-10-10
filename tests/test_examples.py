# Copyright (c) 2026 Daniel Ari Friedman
"""Real example wrapper, configuration-consumption and numerical result checks."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from antropy_hd.inference import (
    binomial_interval,
    bootstrap_interval,
    holm_adjust,
    permutation_test,
)
from antropy_hd.inference_models import Mode
from scripts.example_alphabet import run_alphabet
from scripts.example_models import AlphabetPlan, ExampleKind, PlanningPlan, SpatialPlan
from scripts.example_planning import run_planning
from scripts.example_reports import AlphabetReport, InferenceReport, PlanningReport, SpatialReport
from scripts.example_runners import run_example
from scripts.example_spatial import run_spatial

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "examples/configs"


@pytest.mark.parametrize(
    ("kind", "script"),
    [
        (ExampleKind.SPATIAL, "spatial_embeddings"),
        (ExampleKind.ALPHABET, "fixed_alphabet"),
        (ExampleKind.PLANNING, "planning_and_counts"),
        (ExampleKind.INFERENCE, "replicate_inference"),
    ],
)
def test_real_wrappers_from_another_working_directory(
    kind: ExampleKind, script: str, tmp_path: Path
) -> None:
    expected = run_example(kind, CONFIGS / f"{kind.value}.yaml")
    default = subprocess.run(  # noqa: S603 - fixed interpreter and test-owned paths; no shell.
        [sys.executable, str(ROOT / "examples" / f"{script}.py")],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    explicit = subprocess.run(  # noqa: S603 - fixed interpreter and test-owned paths; no shell.
        [
            sys.executable,
            str(ROOT / "examples" / f"{script}.py"),
            "--plan",
            str(CONFIGS / f"{kind.value}.yaml"),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert default.stderr == explicit.stderr == ""
    assert default.stdout == explicit.stdout == expected.model_dump_json() + "\n"
    assert json.loads(default.stdout)["schema_version"] == 1


def test_spatial_default_geometry_and_input_identity() -> None:
    report = run_example(ExampleKind.SPATIAL, CONFIGS / "spatial.yaml")
    assert isinstance(report, SpatialReport)
    assert [case.input_shape for case in report.cases] == [(8, 9), (6, 7, 8)]
    assert [case.hdse.n_observations for case in report.cases] == [20, 36]
    assert [case.hdse.diagnostics["eligible_pairs"] for case in report.cases] == [175, 216]
    assert all(
        case.hdse.parameters["embedding"] == case.embedding.model_dump(mode="json")
        for case in report.cases
    )
    assert report.cases[0].match.exclusion != report.cases[1].match.exclusion
    assert all(case.hdse.value is not None for case in report.cases)
    assert all(case.weighted_permutation.value is not None for case in report.cases)
    assert all(case.svd.value is not None for case in report.cases)


def test_spatial_yaml_seed_and_measure_controls_are_consumed() -> None:
    original = SpatialPlan.model_validate(yaml.safe_load((CONFIGS / "spatial.yaml").read_text()))
    changed = SpatialPlan.model_validate(
        original.model_dump()
        | {
            "seed": original.seed + 1,
            "svd_demean": False,
            "weighted_permutation_normalize": False,
            "entropy_base": 3.0,
        }
    )
    baseline, modified = run_spatial(original), run_spatial(changed)
    assert all(
        a.input_sha256 != b.input_sha256
        for a, b in zip(baseline.cases, modified.cases, strict=True)
    )
    for case in modified.cases:
        assert case.svd.parameters["demean"] is False
        assert case.svd.parameters["base"] == 3.0
        assert case.weighted_permutation.parameters["normalize"] is False


def test_alphabet_full_counts_tail_bins_and_reference_values() -> None:
    report = run_example(ExampleKind.ALPHABET, CONFIGS / "alphabet.yaml")
    assert isinstance(report, AlphabetReport)
    assert len(report.counts) == len(report.probabilities) == 16
    assert sum(report.counts) == 168
    assert report.counts[0] == report.counts[-1] == 1
    assert len(report.unoccupied_categories) == 7
    assert report.unoccupied_categories == tuple(
        i for i, value in enumerate(report.counts) if value == 0
    )
    assert report.uniform_reference_complexity.value == report.delta_reference_complexity.value == 0
    assert report.categories[0] == "x < -2.0"
    assert report.categories[-1] == "x >= 2.0"


def test_shared_symbolizer_equality_policy_and_overrides_are_consumed() -> None:
    plan = AlphabetPlan.model_validate(yaml.safe_load((CONFIGS / "alphabet.yaml").read_text()))
    controlled = plan.model_dump() | {
        "input_shape": (2, 2),
        "field": {"mean": 0.0, "standard_deviation": 0.0},
        "overrides": [{"index": (0, 0), "value": -1.0}, {"index": (0, 1), "value": 1.0}],
        "symbolization": {"cuts": (-1.0, 0.0, 1.0), "side": "right"},
    }
    right = run_alphabet(AlphabetPlan.model_validate(controlled))
    left = run_alphabet(
        AlphabetPlan.model_validate(
            controlled | {"symbolization": {"cuts": (-1.0, 0.0, 1.0), "side": "left"}}
        )
    )
    assert right.counts == (0, 1, 2, 1)
    assert left.counts == (1, 2, 1, 0)
    assert left.categories == ("x <= -1.0", "-1.0 < x <= 0.0", "0.0 < x <= 1.0", "x > 1.0")
    assert right.input_sha256 == left.input_sha256


def test_planning_work_replay_and_real_negative_controls() -> None:
    report = run_example(ExampleKind.PLANNING, CONFIGS / "planning.yaml")
    assert isinstance(report, PlanningReport)
    assert [case.planned_distance_cells for case in report.cases] == [342, 392, 648]
    for case in report.cases:
        assert case.planned_distance_cells == case.replayed_distance_cells
        assert case.replayed_eligible_pairs_per_stage == (70, 70)
        assert case.observed_hdse.diagnostics["eligible_pairs"] == 70
        assert case.rejected_budget.parameter == "max_memory_bytes"
        assert case.rejected_budget.budget_bytes == case.guard_peak_bytes - 1
        assert case.rejected_budget.reason
    assert len({case.observed_hdse.value for case in report.cases}) == 1
    assert report.large_shape_feasible is False


def test_planning_controls_change_schedule_without_changing_pair_population() -> None:
    plan = PlanningPlan.model_validate(yaml.safe_load((CONFIGS / "planning.yaml").read_text()))
    adjusted = PlanningPlan.model_validate(
        plan.model_dump() | {"block_sizes": (2, 3), "below_guard_bytes": 2}
    )
    report = run_planning(adjusted)
    assert [case.estimate.config.match.block_size for case in report.cases] == [2, 3]
    assert all(
        case.rejected_budget.budget_bytes == case.guard_peak_bytes - 2 for case in report.cases
    )
    assert all(case.replayed_eligible_pairs_per_stage == (70, 70) for case in report.cases)


def test_inference_report_uses_actual_library_results_and_declared_family() -> None:
    report = run_example(ExampleKind.INFERENCE, CONFIGS / "inference.yaml")
    assert isinstance(report, InferenceReport)
    plan = report.plan
    assert report.permutation == permutation_test(plan.first, plan.second, config=plan.permutation)
    assert report.bootstrap == bootstrap_interval(plan.first, plan.second, config=plan.bootstrap)
    assert report.binomial == binomial_interval(
        plan.binomial.successes,
        plan.binomial.total,
        confidence_level=plan.binomial.confidence_level,
    )
    assert report.family_p_values == (report.permutation.p_value, *plan.additional_p_values)
    assert report.holm_adjusted == holm_adjust(report.family_p_values)
    assert report.permutation.effective_mode is Mode.EXACT
    assert report.bootstrap.resamples == plan.bootstrap.resamples


def test_cli_invalid_plan_fails_before_emitting_json(tmp_path: Path) -> None:
    plan = tmp_path / "bad.yaml"
    _ = plan.write_text((CONFIGS / "spatial.yaml").read_text() + "unknown_setting: 123\n")
    result = subprocess.run(  # noqa: S603 - fixed interpreter and test-owned paths; no shell.
        [sys.executable, str(ROOT / "examples/spatial_embeddings.py"), "--plan", str(plan)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert "unknown_setting" in result.stderr
