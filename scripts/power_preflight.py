# Copyright (c) 2026 Daniel Ari Friedman
"""Bound every whole-field kernel and inner permutation request before creating outputs."""

from __future__ import annotations

import math
from typing import assert_never

import numpy as np

from antropy_hd.complexity import ComplexityConfig, estimate_complexity
from antropy_hd.errors import ParameterError
from antropy_hd.inference_models import Mode
from antropy_hd.orchestration import METHODS, analyze, prepared_parameters
from scripts.power_models import InferenceSchedule, PowerPreflight
from scripts.power_plan import PowerPlan


def inference_schedule(plan: PowerPlan, sample_size: int) -> InferenceSchedule:
    """Keep exact allocation multiplicity, actual draw count and conservative scalar visits separate."""
    config = plan.test
    total = 2 * sample_size
    if total > config.max_samples:
        raise ParameterError(
            "max_samples", "A field comparison exceeds the configured inference population"
        )
    allocations = math.comb(total, sample_size)
    exact_fits = (
        allocations <= config.max_exact_allocations
        and allocations * total <= config.max_resampling_work
    )
    match config.mode:
        case Mode.AUTO:
            exact = exact_fits
        case Mode.EXACT:
            if not exact_fits:
                raise ParameterError(
                    "exact", "Exhaustive inference exceeds its configured work or allocation guard"
                )
            exact = True
        case Mode.MONTE_CARLO:
            exact = False
        case unreachable:
            assert_never(unreachable)
    evaluated = allocations if exact else config.resamples
    work = total * evaluated
    if work > config.max_resampling_work:
        raise ParameterError(
            "max_resampling_work", "A resampling request exceeds its configured guard"
        )
    return InferenceSchedule(
        sample_size=sample_size,
        allocations=allocations,
        evaluated=evaluated,
        method="exact" if exact else "monte_carlo",
        work=work,
        resolution=1 / (evaluated if exact else evaluated + 1),
    )


def preflight_power(plan: PowerPlan) -> PowerPreflight:
    """Account once for each generated field; increasing n reuses pool prefixes."""
    visits_per_shape = 0
    for shape in plan.shapes:
        for analysis in plan.analyses:
            _ = prepared_parameters(analysis.spec)
            probability_input = "probabilities" in METHODS[analysis.spec.measure].input_kind
            if (
                probability_input != (analysis.geometry == "symbols")
                or analysis.spec.measure == "multiscale_entropy"
            ):
                raise ParameterError(
                    "geometry",
                    "This scalar design requires an explicit matching input transformation",
                )
            match analysis.geometry:
                case "symbols":
                    # Validate probability-specific axes, bases, reference shapes and
                    # alphabet controls on the actual declared vector geometry.
                    _ = analyze(np.full(plan.symbol_bins, 1 / plan.symbol_bins), analysis.spec)
                    continue
                case "native":
                    actual_shape = shape
                case "flattened":
                    actual_shape = (math.prod(shape),)
                case unreachable:
                    assert_never(unreachable)
            parameters = analysis.spec.parameters
            defaults = ComplexityConfig()
            config = ComplexityConfig.model_validate(
                {
                    "measure": analysis.spec.measure,
                    "embedding": parameters.get(
                        "embedding",
                        {
                            "max_memory_bytes": parameters.get(
                                "max_memory_bytes", defaults.embedding.max_memory_bytes
                            )
                        },
                    ),
                    "match": parameters.get("match", {}),
                    "bins": parameters.get("bins", plan.symbol_bins),
                    "max_pattern_length": parameters.get(
                        "max_pattern_length", defaults.max_pattern_length
                    ),
                }
            )
            estimate = estimate_complexity(actual_shape, config)
            if not estimate.feasible:
                raise ParameterError(
                    "power",
                    f"Infeasible field estimator {analysis.spec.id}: {estimate.resource_violations}",
                )
            visits_per_shape += estimate.distance_component_visits
    visits = visits_per_shape * len(plan.scenarios) * plan.repetitions * 2 * max(plan.sample_sizes)
    schedules = tuple(inference_schedule(plan, n) for n in sorted(plan.sample_sizes))
    work = (
        sum(item.work for item in schedules)
        * len(plan.shapes)
        * len(plan.scenarios)
        * plan.repetitions
        * len(plan.analyses)
    )
    peak_pool_bytes = (
        2 * max(plan.sample_sizes) * max(math.prod(shape) for shape in plan.shapes) * 8
    )
    if peak_pool_bytes > plan.max_pool_bytes:
        raise ParameterError(
            "max_pool_bytes", "Two live field pools exceed the declared array budget"
        )
    if visits > plan.max_distance_component_visits or work > plan.max_inference_work:
        raise ParameterError(
            "power", "Whole-design distance or inference work exceeds the declared budget"
        )
    return PowerPreflight(
        fields=plan.field_count,
        experiments=plan.experiment_count,
        distance_component_visits=visits,
        inference_work=work,
        peak_pool_bytes=peak_pool_bytes,
        schedules=schedules,
        worst_case_mc_standard_error=math.sqrt(0.25 / plan.repetitions),
    )
