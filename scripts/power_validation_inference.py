# Copyright (c) 2026 Daniel Ari Friedman
"""Replay tests and family decisions from authenticated whole-field observations."""

from __future__ import annotations

import statistics
from collections import defaultdict
from itertools import product
from typing import assert_never

from antropy_hd.errors import ParameterError
from antropy_hd.inference import binomial_interval, holm_adjust, permutation_test
from antropy_hd.inference_models import PermutationConfig
from antropy_hd.models import Status
from scripts.power_fields import stream_seed
from scripts.power_models import PowerDecision, PowerReport, PowerSummary
from scripts.power_plan import PowerPlan
from scripts.power_preflight import inference_schedule
from scripts.power_validation_fields import FieldIndex
from scripts.result_replay import numeric_equivalent

type DecisionKey = tuple[str, tuple[int, ...], int, int, str]


def _decision(report: PowerReport, key: DecisionKey, fields: FieldIndex) -> PowerDecision:
    """Reconstruct one raw decision; missing results remain unavailable and unrejected."""
    scenario_id, shape, size, replicate, analysis_id = key
    plan = report.plan
    a = fields.groups[(scenario_id, shape, replicate, "first")][:size]
    b = fields.groups[(scenario_id, shape, replicate, "second")][:size]
    counts = tuple(
        sum(field.results[analysis_id].status is status for field in group)
        for status in (Status.UNDEFINED, Status.INFINITE)
        for group in (a, b)
    )
    test = None
    if sum(counts) == 0:
        seed = stream_seed(
            plan, f"inference/{plan.test.seed}/{scenario_id}/{analysis_id}", shape, replicate, size
        )
        config = PermutationConfig.model_validate(plan.test.model_dump() | {"seed": seed})
        test = permutation_test(
            [field.results[analysis_id].as_float() for field in a],
            [field.results[analysis_id].as_float() for field in b],
            config=config,
        )
    return PowerDecision(
        scenario_id=scenario_id,
        shape=shape,
        sample_size=size,
        replicate=replicate,
        analysis_id=analysis_id,
        status="available" if test is not None else "unavailable",
        undefined_first=counts[0],
        undefined_second=counts[1],
        infinite_first=counts[2],
        infinite_second=counts[3],
        mean_difference=test.effect if test is not None else None,
        p_value=test.p_value if test is not None else None,
        adjusted_p_value=test.p_value if test is not None else None,
        raw_rejected=test is not None and test.p_value <= plan.alpha,
        rejected=test is not None and test.p_value <= plan.alpha,
        test=test,
    )


def validate_decisions(report: PowerReport, fields: FieldIndex) -> None:
    """Require every comparison and independently recompute its inclusive tail and fixed family."""
    plan = report.plan
    expected = {
        (scenario.id, shape, size, replicate, analysis.spec.id)
        for scenario, shape, size, replicate, analysis in product(
            plan.scenarios,
            plan.shapes,
            plan.sample_sizes,
            range(plan.repetitions),
            plan.analyses,
        )
    }
    keys = [
        (row.scenario_id, row.shape, row.sample_size, row.replicate, row.analysis_id)
        for row in report.experiments
    ]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ParameterError("power", "Decision design matrix is incomplete or duplicated")
    stored = dict(zip(keys, report.experiments, strict=True))
    for scenario, shape, size, replicate in product(
        plan.scenarios, plan.shapes, plan.sample_sizes, range(plan.repetitions)
    ):
        family_keys = [
            (scenario.id, shape, size, replicate, analysis.spec.id) for analysis in plan.analyses
        ]
        raw = [_decision(report, key, fields) for key in family_keys]
        match plan.multiplicity:
            case "none":
                adjusted = tuple(row.p_value for row in raw)
            case "holm":
                adjusted = holm_adjust(
                    [row.p_value if row.p_value is not None else 1.0 for row in raw]
                )
            case unreachable:
                assert_never(unreachable)
        for key, row, correction in zip(family_keys, raw, adjusted, strict=True):
            available = row.p_value is not None
            expected_row = row.model_copy(
                update={
                    "adjusted_p_value": correction if available else None,
                    "rejected": available and correction is not None and correction <= plan.alpha,
                }
            )
            if not numeric_equivalent(
                stored[key].model_dump(mode="json"), expected_row.model_dump(mode="json")
            ):
                raise ParameterError(
                    "power", "Decision fails actual inference or fixed-family replay"
                )


def _summary(plan: PowerPlan, rows: tuple[PowerDecision, ...]) -> PowerSummary:
    """Derive each denominator and identification range directly from authenticated outcomes."""
    first = rows[0]
    total = len(rows)
    available = sum(row.p_value is not None for row in rows)
    unavailable = total - available
    rejected = sum(row.rejected for row in rows)
    effects = [row.mean_difference for row in rows if row.mean_difference is not None]
    scenario = next(scenario for scenario in plan.scenarios if scenario.id == first.scenario_id)
    return PowerSummary(
        scenario_id=first.scenario_id,
        role=scenario.role,
        shape=first.shape,
        sample_size=first.sample_size,
        analysis_id=first.analysis_id,
        attempted=total,
        available=available,
        unavailable=unavailable,
        rejected=rejected,
        raw_rejected=sum(row.raw_rejected for row in rows),
        conditional_rejection=binomial_interval(
            rejected, available, confidence_level=plan.confidence_level
        ),
        unconditional_rejection=binomial_interval(
            rejected, total, confidence_level=plan.confidence_level
        ),
        availability=binomial_interval(available, total, confidence_level=plan.confidence_level),
        missing_decision_lower=rejected / total,
        missing_decision_upper=(rejected + unavailable) / total,
        mean_difference_mean=statistics.mean(effects) if effects else None,
        mean_difference_sd=statistics.stdev(effects) if len(effects) > 1 else None,
        minimum_p_resolution=inference_schedule(plan, first.sample_size).resolution,
    )


def validate_summaries(report: PowerReport) -> None:
    """Reconstruct pointwise Wilson intervals without censoring unavailable comparisons."""
    groups: defaultdict[tuple[str, tuple[int, ...], int, str], list[PowerDecision]] = defaultdict(
        list
    )
    for row in report.experiments:
        groups[(row.scenario_id, row.shape, row.sample_size, row.analysis_id)].append(row)
    keys = [
        (row.scenario_id, row.shape, row.sample_size, row.analysis_id) for row in report.summaries
    ]
    if len(keys) != len(set(keys)) or set(keys) != groups.keys():
        raise ParameterError("power", "Summary design matrix is incomplete or duplicated")
    for key, row in zip(keys, report.summaries, strict=True):
        expected = _summary(report.plan, tuple(groups[key]))
        if not numeric_equivalent(row.model_dump(mode="json"), expected.model_dump(mode="json")):
            raise ParameterError("power", "Summary fails complete denominators or interval replay")
