# Copyright (c) 2026 Daniel Ari Friedman
"""Actual configured power execution and early infeasible-request controls."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.inference_models import Alternative, Mode
from antropy_hd.orchestration import AnalysisSpec
from scripts.power_plan import PowerPlan
from scripts.run_power import run_power
from scripts.validate_power import validate_power
from tests.power_validation_fixtures import small_power as small_power  # noqa: PLC0414


def _plan(root: Path) -> PowerPlan:
    return PowerPlan.model_validate(yaml.safe_load((root / "power_plan.yaml").read_text()))


def test_unadjusted_one_sided_monte_carlo_design_replays(small_power: Path, tmp_path: Path) -> None:
    # Given an explicitly unadjusted directional whole-field design.
    plan = _plan(small_power)
    configured = PowerPlan.model_validate(
        plan.model_dump()
        | {
            "multiplicity": "none",
            "test": plan.test.model_dump()
            | {"alternative": Alternative.GREATER, "mode": Mode.MONTE_CARLO},
        }
    )
    path = tmp_path / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(configured.model_dump(mode="json")))
    _ = run_power(tmp_path, path)
    # When the actual fields, tails and decisions are independently authenticated.
    report = validate_power(tmp_path)
    # Then every available decision retains its directional Monte Carlo policy.
    assert all(
        row.test is None
        or (
            row.p_value == row.adjusted_p_value
            and row.test.config.alternative is Alternative.GREATER
            and row.test.effective_mode is Mode.MONTE_CARLO
        )
        for row in report.experiments
    )


@pytest.mark.parametrize(
    "settings",
    [
        {"max_samples": 4},
        {"mode": "exact"},
        {"max_resampling_work": 20},
    ],
)
def test_inference_resource_failure_precedes_output_creation(
    small_power: Path, tmp_path: Path, settings: dict[str, JsonValue]
) -> None:
    plan = _plan(small_power)
    configured = PowerPlan.model_validate(
        plan.model_dump() | {"test": plan.test.model_dump() | settings}
    )
    path = tmp_path / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(configured.model_dump(mode="json")))
    with pytest.raises(ParameterError):
        _ = run_power(tmp_path, path)
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("measure", ["conditional_entropy", "mutual_information"])
def test_joint_axes_rejected_before_creating_any_pool(
    small_power: Path, tmp_path: Path, measure: str
) -> None:
    plan = _plan(small_power)
    analysis = plan.analyses[-1].model_copy(
        update={
            "spec": AnalysisSpec(id="joint", measure=measure),
        }
    )
    configured = plan.model_copy(update={"analyses": (analysis,)})
    path = tmp_path / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(configured.model_dump(mode="json")))
    with pytest.raises(ParameterError, match="axes"):
        _ = run_power(tmp_path, path)
    assert not (tmp_path / "output").exists()


def test_probability_reference_shape_checked_before_outputs(
    small_power: Path, tmp_path: Path
) -> None:
    plan = _plan(small_power)
    analysis = plan.analyses[-1].model_copy(
        update={
            "spec": AnalysisSpec(
                id="js", measure="jensen_shannon_divergence", parameters={"q": [0.5, 0.5]}
            ),
        }
    )
    configured = plan.model_copy(update={"analyses": (analysis,)})
    path = tmp_path / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(configured.model_dump(mode="json")))
    with pytest.raises(ParameterError, match="shape"):
        _ = run_power(tmp_path, path)
    assert not (tmp_path / "output").exists()


def test_observation_measure_cannot_consume_symbol_probabilities(
    small_power: Path, tmp_path: Path
) -> None:
    plan = _plan(small_power)
    analysis = plan.analyses[0].model_copy(update={"geometry": "symbols"})
    configured = plan.model_copy(update={"analyses": (analysis, *plan.analyses[1:])})
    path = tmp_path / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(configured.model_dump(mode="json")))
    with pytest.raises(ParameterError, match="input transformation"):
        _ = run_power(tmp_path, path)
    assert not (tmp_path / "output").exists()
