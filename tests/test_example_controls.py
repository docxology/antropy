# Copyright (c) 2026 Daniel Ari Friedman
"""Fail-closed YAML and numerical preflight controls for real examples."""

from pathlib import Path

import pytest
import yaml
from pydantic import JsonValue, ValidationError

from antropy_hd.errors import ParameterError
from scripts.example_models import (
    AlphabetPlan,
    ExampleKind,
    InferencePlan,
    PlanningPlan,
    SpatialPlan,
)
from scripts.example_runners import read_example_yaml, run_example

CONFIGS = Path(__file__).resolve().parents[1] / "examples/configs"


@pytest.mark.parametrize(
    "source",
    [
        "seed: 1\nseed: 2\n",
        "field:\n  mean: 0\n  mean: 1\n",
        "cases:\n- field:\n    mean: 0\n    mean: 1\n",
        "value: &shared [1, 2]\nother: *shared\n",
        "[broken",
        "1: value\n",
    ],
)
def test_invalid_yaml_is_rejected_with_typed_error(source: str, tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    _ = path.write_text(source)
    with pytest.raises(ParameterError, match="plan"):
        read_example_yaml(path)


def test_empty_yaml_rejects_a_vacuous_plan(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    _ = path.write_text("")
    assert read_example_yaml(path) is None
    with pytest.raises(ValidationError):
        run_example(ExampleKind.SPATIAL, path)


@pytest.mark.parametrize(
    "changes",
    [
        {"seed": True},
        {"seed": -1},
        {"max_cases": 1},
        {"max_input_elements": 1},
        {"entropy_base": 1.0},
        {
            "field": {
                "mean": 0.0,
                "standard_deviation": 0.25,
                "sine_axis": 5,
                "sine_amplitude": 1.0,
                "sine_divisor": 2.0,
                "trend_slope": 0.2,
            }
        },
        {
            "field": {
                "mean": True,
                "standard_deviation": 0.25,
                "sine_axis": 0,
                "sine_amplitude": 1.0,
                "sine_divisor": 2.0,
                "trend_slope": 0.2,
            }
        },
        {"max_pattern_length": 2},
        {"weighted_permutation_normalize": "true"},
    ],
)
def test_invalid_spatial_controls_fail(changes: dict[str, JsonValue]) -> None:
    plan = yaml.safe_load((CONFIGS / "spatial.yaml").read_text())
    with pytest.raises(ValidationError):
        SpatialPlan.model_validate(plan | changes)


def test_spatial_duplicate_geometry_and_resource_preflight() -> None:
    plan = SpatialPlan.model_validate(yaml.safe_load((CONFIGS / "spatial.yaml").read_text()))
    data = plan.model_dump()
    with pytest.raises(ValidationError):
        SpatialPlan.model_validate(data | {"cases": (data["cases"][0], data["cases"][0])})
    case = data["cases"][0]
    case["embedding"]["max_memory_bytes"] = 1024
    with pytest.raises(ValidationError, match="resource"):
        SpatialPlan.model_validate(data | {"cases": (case,)})


@pytest.mark.parametrize(
    "changes",
    [
        {"input_shape": (0, 2)},
        {"input_shape": (1000, 1000)},
        {"overrides": ({"index": (0, 0), "value": 1.0}, {"index": (0, 0), "value": 2.0})},
        {"overrides": ({"index": (12, 0), "value": 1.0},)},
        {"overrides": ({"index": (0,), "value": 1.0},)},
        {"symbolization": {"cuts": (0.0, 0.0), "side": "right"}},
        {"entropy_base": 3.0},
    ],
)
def test_invalid_alphabet_controls_fail(changes: dict[str, JsonValue]) -> None:
    plan = yaml.safe_load((CONFIGS / "alphabet.yaml").read_text())
    with pytest.raises(ValidationError):
        AlphabetPlan.model_validate(plan | changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"block_sizes": (0,)},
        {"block_sizes": (1, 1)},
        {"block_sizes": (4097,)},
        {"below_guard_bytes": 1000000},
        {"input_shape": (0, 2)},
        {"large_shape": (0, 2)},
        {"max_input_elements": 1},
    ],
)
def test_invalid_planning_controls_fail(changes: dict[str, JsonValue]) -> None:
    plan = yaml.safe_load((CONFIGS / "planning.yaml").read_text())
    with pytest.raises(ValidationError):
        PlanningPlan.model_validate(plan | changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"first": (True, 1.0)},
        {"additional_p_values": (float("nan"),)},
        {"additional_p_values": (1.1,)},
        {"additional_p_values": (True,)},
        {"binomial": {"successes": 3, "total": 2, "confidence_level": 0.95}},
    ],
)
def test_invalid_inference_controls_fail(changes: dict[str, JsonValue]) -> None:
    plan = yaml.safe_load((CONFIGS / "inference.yaml").read_text())
    with pytest.raises(ValidationError):
        InferencePlan.model_validate(plan | changes)
