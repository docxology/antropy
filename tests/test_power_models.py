# Copyright (c) 2026 Daniel Ari Friedman
"""Noncoercing prospective-design and explicit missing-decision model contracts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import JsonValue, ValidationError

from antropy_hd.errors import ParameterError
from antropy_hd.inference import permutation_test
from antropy_hd.inference_models import Pairing, PermutationConfig
from scripts.power_fields import replacement_field, stream_seed
from scripts.power_models import PowerDecision
from scripts.power_plan import PowerPlan, PowerScenario

# This export is the real producer fixture used by the artifact controls.
from tests.power_validation_fixtures import small_power as small_power  # noqa: PLC0414


@pytest.fixture
def power_plan(small_power: Path) -> PowerPlan:
    return PowerPlan.model_validate(yaml.safe_load((small_power / "power_plan.yaml").read_text()))


@pytest.fixture
def available_decision() -> PowerDecision:
    test = permutation_test([0.0, 0.0], [1.0, 1.0], config=PermutationConfig(seed=7))
    return PowerDecision(
        scenario_id="contrast",
        shape=(8,),
        sample_size=2,
        replicate=0,
        analysis_id="entropy",
        status="available",
        undefined_first=0,
        undefined_second=0,
        infinite_first=0,
        infinite_second=0,
        mean_difference=test.effect,
        p_value=test.p_value,
        adjusted_p_value=test.p_value,
        raw_rejected=False,
        rejected=False,
        test=test,
    )


@pytest.fixture
def unavailable_decision() -> PowerDecision:
    return PowerDecision(
        scenario_id="contrast",
        shape=(8,),
        sample_size=2,
        replicate=0,
        analysis_id="entropy",
        status="unavailable",
        undefined_first=1,
        undefined_second=0,
        infinite_first=0,
        infinite_second=1,
        mean_difference=None,
        p_value=None,
        adjusted_p_value=None,
        raw_rejected=False,
        rejected=False,
        test=None,
    )


@pytest.mark.parametrize("field", ["mean_difference", "p_value", "adjusted_p_value", "test"])
def test_available_decision_requires_retained_inference(
    available_decision: PowerDecision, field: str
) -> None:
    # Given a real complete exact test.
    data = available_decision.model_dump() | {field: None}
    # When an inference value is absent.
    # Then the model rejects an available comparison with missing evidence.
    with pytest.raises(ValidationError):
        _ = PowerDecision.model_validate(data)


@pytest.mark.parametrize("field", ["mean_difference", "p_value", "adjusted_p_value"])
def test_unavailable_decision_cannot_impute_a_zero(
    unavailable_decision: PowerDecision, field: str
) -> None:
    data = unavailable_decision.model_dump() | {field: 0.0}
    with pytest.raises(ValidationError):
        _ = PowerDecision.model_validate(data)


@pytest.mark.parametrize("field", ["rejected", "raw_rejected"])
def test_unavailable_decision_cannot_claim_rejection(
    unavailable_decision: PowerDecision, field: str
) -> None:
    data = unavailable_decision.model_dump() | {field: True}
    with pytest.raises(ValidationError):
        _ = PowerDecision.model_validate(data)


@pytest.mark.parametrize("field", ["rejected", "raw_rejected"])
def test_decision_flags_do_not_coerce_numeric_boolean(
    available_decision: PowerDecision, field: str
) -> None:
    data = available_decision.model_dump() | {field: 0}
    with pytest.raises(ValidationError):
        _ = PowerDecision.model_validate(data)


@pytest.mark.parametrize(
    "field", ["undefined_first", "infinite_second", "sample_size", "replicate"]
)
def test_decision_counts_do_not_coerce_boolean(
    available_decision: PowerDecision, field: str
) -> None:
    data = available_decision.model_dump() | {field: False}
    with pytest.raises(ValidationError):
        _ = PowerDecision.model_validate(data)


@pytest.mark.parametrize("field", ["mean_difference", "p_value", "sample_size"])
def test_available_values_must_equal_the_actual_retained_test(
    available_decision: PowerDecision, field: str
) -> None:
    data = available_decision.model_dump()
    data[field] += 1 if field != "p_value" else 0.1
    with pytest.raises(ValidationError):
        _ = PowerDecision.model_validate(data)


def test_nonfinite_counts_cannot_exceed_the_group(unavailable_decision: PowerDecision) -> None:
    data = unavailable_decision.model_dump() | {"undefined_first": 2, "infinite_first": 1}
    with pytest.raises(ValidationError):
        _ = PowerDecision.model_validate(data)


@pytest.mark.parametrize(
    "change",
    [
        {"shapes": [[12], [12]]},
        {"sample_sizes": [2, 2]},
        {"sample_sizes": [1]},
        {"shapes": [list[int]()]},
        {"shapes": [[0]]},
        {"shapes": [[101]]},
        {"repetitions": True},
        {"seed": False},
        {"max_fields": 1},
        {"symbol_range": [3, -3]},
        {"period": float("inf")},
        {"unused_control": 17},
    ],
)
def test_power_plan_rejects_unconsumed_or_incoherent_design(
    power_plan: PowerPlan, change: dict[str, JsonValue]
) -> None:
    data = power_plan.model_dump() | change
    with pytest.raises((ParameterError, ValidationError)):
        _ = PowerPlan.model_validate(data)


def test_generator_does_not_accept_paired_inference(power_plan: PowerPlan) -> None:
    data = power_plan.model_dump() | {
        "test": power_plan.test.model_dump() | {"pairing": Pairing.PAIRED}
    }
    with pytest.raises(ValidationError):
        _ = PowerPlan.model_validate(data)


@pytest.mark.parametrize(
    ("role", "first", "second"),
    [("null", 0.25, 0.5), ("alternative", 0.25, 0.25)],
)
def test_scenario_label_cannot_change_the_generating_hypothesis(
    role: str, first: float, second: float
) -> None:
    with pytest.raises(ValidationError):
        _ = PowerScenario.model_validate(
            {
                "id": "trial",
                "label": "Trial",
                "role": role,
                "first_probability": first,
                "second_probability": second,
            }
        )


def test_null_groups_have_separate_subject_streams(power_plan: PowerPlan) -> None:
    scenario = power_plan.scenarios[0]
    first = replacement_field(power_plan, scenario, (64,), 0, "first", 0)
    second = replacement_field(power_plan, scenario, (64,), 0, "second", 0)
    assert not np.array_equal(first, second)


def test_scenario_order_preserves_each_subject_seed(power_plan: PowerPlan) -> None:
    scenario = power_plan.scenarios[0]
    reordered = power_plan.model_copy(update={"scenarios": tuple(reversed(power_plan.scenarios))})
    actual = replacement_field(reordered, scenario, (64,), 0, "first", 0)
    expected = replacement_field(power_plan, scenario, (64,), 0, "first", 0)
    np.testing.assert_array_equal(actual, expected)


def test_subject_and_semantic_namespaces_separate_seed_streams(power_plan: PowerPlan) -> None:
    seeds = {
        stream_seed(power_plan, namespace, (12,), replicate, subject)
        for namespace in ("field/null/first", "field/null/second", "inference/null/hdse")
        for replicate in range(2)
        for subject in range(2)
    }
    assert len(seeds) == 12
