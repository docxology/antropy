# Copyright (c) 2026 Daniel Ari Friedman
"""Pointwise simulation uncertainty without discarding failures or asserting observed power."""

from __future__ import annotations

import statistics
from collections import defaultdict

from antropy_hd.inference import binomial_interval
from scripts.power_models import PowerDecision, PowerSummary
from scripts.power_plan import PowerPlan
from scripts.power_preflight import inference_schedule


def summarize_power(
    plan: PowerPlan, decisions: tuple[PowerDecision, ...]
) -> tuple[PowerSummary, ...]:
    """Report K/V, K/R, V/R and missing-decision identification bounds separately."""
    groups: defaultdict[tuple[str, tuple[int, ...], int, str], list[PowerDecision]] = defaultdict(
        list
    )
    for decision in decisions:
        groups[
            (decision.scenario_id, decision.shape, decision.sample_size, decision.analysis_id)
        ].append(decision)
    scenarios = {scenario.id: scenario for scenario in plan.scenarios}
    summaries: list[PowerSummary] = []
    for (scenario_id, shape, size, analysis_id), rows in sorted(groups.items()):
        total = len(rows)
        available = sum(row.status == "available" for row in rows)
        unavailable = total - available
        rejected = sum(row.rejected for row in rows)
        raw_rejected = sum(row.raw_rejected for row in rows)
        effects = [row.mean_difference for row in rows if row.mean_difference is not None]
        summaries.append(
            PowerSummary(
                scenario_id=scenario_id,
                role=scenarios[scenario_id].role,
                shape=shape,
                sample_size=size,
                analysis_id=analysis_id,
                attempted=total,
                available=available,
                unavailable=unavailable,
                rejected=rejected,
                raw_rejected=raw_rejected,
                conditional_rejection=binomial_interval(
                    rejected, available, confidence_level=plan.confidence_level
                ),
                unconditional_rejection=binomial_interval(
                    rejected, total, confidence_level=plan.confidence_level
                ),
                availability=binomial_interval(
                    available, total, confidence_level=plan.confidence_level
                ),
                missing_decision_lower=rejected / total,
                missing_decision_upper=(rejected + unavailable) / total,
                mean_difference_mean=statistics.mean(effects) if effects else None,
                mean_difference_sd=statistics.stdev(effects) if len(effects) > 1 else None,
                minimum_p_resolution=inference_schedule(plan, size).resolution,
            )
        )
    return tuple(summaries)
