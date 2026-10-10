# Copyright (c) 2026 Daniel Ari Friedman
"""Whole-field tests, fixed-family multiplicity and explicit unavailable-decision policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

import numpy as np
from numpy.typing import NDArray

from antropy_hd.errors import ParameterError
from antropy_hd.inference import holm_adjust, permutation_test
from antropy_hd.inference_models import PermutationConfig
from antropy_hd.models import EntropyResult, Status
from antropy_hd.orchestration import analyze
from scripts.power_fields import fixed_probabilities, stream_seed
from scripts.power_models import FieldEstimate, PowerDecision
from scripts.power_plan import PowerPlan, PowerScenario


@dataclass(frozen=True, slots=True)
class ExperimentIdentity:
    """The scenario and independent outer repetition; sample sizes share pool prefixes."""

    scenario: PowerScenario
    shape: tuple[int, ...]
    replicate: int


def evaluate_field(array: NDArray[np.float64], plan: PowerPlan) -> dict[str, EntropyResult]:
    """Compute every configured scalar once, before any label permutation."""
    symbols = fixed_probabilities(array, plan)
    results: dict[str, EntropyResult] = {}
    for analysis in plan.analyses:
        match analysis.geometry:
            case "native":
                transformed = array
            case "flattened":
                transformed = array.ravel(order="C")
            case "symbols":
                transformed = symbols
            case unreachable:
                assert_never(unreachable)
        result = analyze(transformed, analysis.spec)
        match result:
            case EntropyResult():
                results[analysis.spec.id] = result
            case tuple():
                raise ParameterError(
                    "power", "A configured power estimator returned nonscalar results"
                )
            case unreachable:
                assert_never(unreachable)
    return results


def one_decision(
    plan: PowerPlan,
    identity: ExperimentIdentity,
    sample_size: int,
    analysis_id: str,
    first: tuple[FieldEstimate, ...],
    second: tuple[FieldEstimate, ...],
) -> PowerDecision:
    """Require all whole-field observations finite; retain every nonfinite cause."""
    a = [field.results[analysis_id] for field in first[:sample_size]]
    b = [field.results[analysis_id] for field in second[:sample_size]]
    undefined_first = sum(item.status is Status.UNDEFINED for item in a)
    undefined_second = sum(item.status is Status.UNDEFINED for item in b)
    infinite_first = sum(item.status is Status.INFINITE for item in a)
    infinite_second = sum(item.status is Status.INFINITE for item in b)
    available = not (undefined_first + undefined_second + infinite_first + infinite_second)
    test = None
    if available:
        seed = stream_seed(
            plan,
            f"inference/{plan.test.seed}/{identity.scenario.id}/{analysis_id}",
            identity.shape,
            identity.replicate,
            sample_size,
        )
        config = PermutationConfig.model_validate(plan.test.model_dump() | {"seed": seed})
        test = permutation_test(
            [item.as_float() for item in a], [item.as_float() for item in b], config=config
        )
    return PowerDecision(
        scenario_id=identity.scenario.id,
        shape=identity.shape,
        sample_size=sample_size,
        replicate=identity.replicate,
        analysis_id=analysis_id,
        status="available" if available else "unavailable",
        undefined_first=undefined_first,
        undefined_second=undefined_second,
        infinite_first=infinite_first,
        infinite_second=infinite_second,
        mean_difference=None if test is None else test.effect,
        p_value=None if test is None else test.p_value,
        adjusted_p_value=None if test is None else test.p_value,
        raw_rejected=test is not None and test.p_value <= plan.alpha,
        rejected=test is not None and test.p_value <= plan.alpha,
        test=test,
    )


def experiment_decisions(
    plan: PowerPlan,
    identity: ExperimentIdentity,
    sample_size: int,
    first: tuple[FieldEstimate, ...],
    second: tuple[FieldEstimate, ...],
) -> tuple[PowerDecision, ...]:
    """Apply a fixed declared family; missing tests contribute conservative nonrejection only."""
    decisions = tuple(
        one_decision(plan, identity, sample_size, analysis.spec.id, first, second)
        for analysis in plan.analyses
    )
    match plan.multiplicity:
        case "none":
            return decisions
        case "holm":
            # Missing entropy results remain null. A bookkeeping p=1 prevents an
            # unavailable family member from shrinking the declared Holm family.
            adjusted = holm_adjust(
                [
                    decision.p_value if decision.p_value is not None else 1.0
                    for decision in decisions
                ]
            )
            return tuple(
                decision.model_copy(
                    update={
                        "adjusted_p_value": value if decision.status == "available" else None,
                        "rejected": decision.status == "available" and value <= plan.alpha,
                    }
                )
                for decision, value in zip(decisions, adjusted, strict=True)
            )
        case unreachable:
            assert_never(unreachable)
