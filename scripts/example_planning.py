# Copyright (c) 2026 Daniel Ari Friedman
"""Actual blocked-kernel replay and numerical resource failure controls."""

from importlib.metadata import version

import numpy as np

from antropy_hd.complexity import ComplexityConfig, estimate_complexity
from antropy_hd.embedding import paired_templates
from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.models import EmbeddingConfig, MatchConfig
from antropy_hd.orchestration import array_sha256
from antropy_hd.pairs import pair_blocks
from antropy_hd.template_entropy import hdse
from scripts.example_models import PlanningPlan
from scripts.example_reports import BlockCase, ObservedBudgetFailure, PlanningReport


def run_planning(plan: PlanningPlan) -> PlanningReport:
    """Compare allocation-free estimates with real work and estimator diagnostics."""
    field = np.random.default_rng(plan.seed).normal(
        plan.field.mean, plan.field.standard_deviation, size=plan.input_shape
    )
    cases: list[BlockCase] = []
    for block_size in plan.block_sizes:
        matching = MatchConfig.model_validate(plan.match.model_dump() | {"block_size": block_size})
        estimate = estimate_complexity(
            field.shape, ComplexityConfig(embedding=plan.embedding, match=matching)
        )
        observed = hdse(field, embedding=plan.embedding, match=matching)
        templates = paired_templates(field, plan.embedding)
        cells, blocks = 0, 0
        eligible_counts: list[int] = []
        for current, other in (
            (templates.base, templates.extended),
            (templates.extended, templates.base),
        ):
            eligible_pairs = 0
            for distances, eligible in pair_blocks(
                current, plan.embedding, matching, live_bytes=other.values.nbytes
            ):
                cells += distances.size
                blocks += 1
                eligible_pairs += int(np.count_nonzero(eligible))
            eligible_counts.append(eligible_pairs)
        below = EmbeddingConfig.model_validate(
            plan.embedding.model_dump()
            | {"max_memory_bytes": estimate.guard_peak_bytes - plan.below_guard_bytes}
        )
        try:
            _ = hdse(field, embedding=below, match=matching)
        except ResourceError as error:
            failure = ObservedBudgetFailure(
                budget_bytes=below.max_memory_bytes, parameter=error.parameter, reason=error.reason
            )
        else:
            raise ParameterError("max_memory_bytes", "below-guard control unexpectedly completed")
        cases.append(
            BlockCase(
                estimate=estimate,
                feasible=estimate.feasible,
                guard_peak_bytes=estimate.guard_peak_bytes,
                planned_distance_cells=estimate.computed_distance_cells,
                replayed_distance_cells=cells,
                replayed_blocks=blocks,
                replayed_eligible_pairs_per_stage=tuple(eligible_counts),
                observed_hdse=observed,
                rejected_budget=failure,
            )
        )
    large = estimate_complexity(plan.large_shape, plan.large_config)
    return PlanningReport(
        package_version=version("antropy-hd"),
        seed=plan.seed,
        input_sha256=array_sha256(field),
        cases=tuple(cases),
        large_shape_plan=large,
        large_shape_feasible=large.feasible,
    )
