# Copyright (c) 2026 Daniel Ari Friedman
"""Estimator-specific work and resource plans without allocating input arrays."""

from math import prod
from typing import assert_never

from antropy_hd._complexity import (
    PAIR_MEASURES,
    ComplexityConfig,
    ComplexityEstimate,
    ComplexityMeasure,
    ComputationStage,
    InputShape,
    Lattice,
    ResourceRequirement,
    WorkTerm,
    computation_stage,
    embedding_memory,
    lattice,
    memory_requirement,
    pair_memory,
    population_requirements,
)
from antropy_hd.embedding import extended_shape, resolve_geometry
from antropy_hd.errors import ParameterError

__all__ = ["ComplexityConfig", "ComplexityEstimate", "ComplexityMeasure", "estimate_complexity"]


def _paired_plan(
    input_shape: tuple[int, ...], config: ComplexityConfig
) -> tuple[tuple[ComputationStage, ...], tuple[ResourceRequirement, ...]]:
    """Plan nested common-origin kernels with their simultaneous template storage."""
    shape = resolve_geometry(config.embedding.shape, len(input_shape), "shape")
    larger = extended_shape(shape, config.embedding.extend_axes)
    extended = lattice(input_shape, larger, config.embedding)
    if extended.count < 2:
        raise ParameterError("shape", "at least two common origins are required")
    base = Lattice(shape, extended.counts, extended.stride)
    resources = population_requirements("paired_templates", extended, config)
    resources.append(
        memory_requirement(
            "paired_extraction",
            embedding_memory(extended, base.features + extended.features),
            config,
        )
    )
    if config.measure is not ComplexityMeasure.FUZZY or config.match.tolerance:
        for name, current, other in (("base", base, extended), ("extended", extended, base)):
            extra = other.count * other.features * 8
            if config.measure is ComplexityMeasure.FUZZY:
                extra += current.count * (current.features * 24 + 32)
            resources.append(
                memory_requirement(name + "_kernel", pair_memory(current, config, extra), config)
            )
    return (
        computation_stage("base", base, config),
        computation_stage("extended", extended, config),
    ), tuple(resources)


def _approximate_plan(
    input_shape: tuple[int, ...], config: ComplexityConfig
) -> tuple[tuple[ComputationStage, ...], tuple[ResourceRequirement, ...]]:
    """Plan separate full-origin populations, released between ApEn passes."""
    shape = resolve_geometry(config.embedding.shape, len(input_shape), "shape")
    stages: list[ComputationStage] = []
    resources: list[ResourceRequirement] = []
    for name, current_shape in (
        ("base", shape),
        ("extended", extended_shape(shape, config.embedding.extend_axes)),
    ):
        grid = lattice(input_shape, current_shape, config.embedding)
        stages.append(computation_stage(name, grid, config))
        resources.extend(population_requirements(name, grid, config))
        resources.append(
            memory_requirement(name + "_extraction", embedding_memory(grid, grid.features), config)
        )
        resources.append(
            memory_requirement(name + "_kernel", pair_memory(grid, config, grid.count * 8), config)
        )
    return tuple(stages), tuple(resources)


def _local_plan(
    input_shape: tuple[int, ...], config: ComplexityConfig
) -> tuple[tuple[ComputationStage, ...], tuple[ResourceRequirement, ...], tuple[WorkTerm, ...]]:
    """Plan local ordinal, SVD or two-pass distribution kernels."""
    shape = resolve_geometry(config.embedding.shape, len(input_shape), "shape")
    grid = lattice(input_shape, shape, config.embedding)
    stage = computation_stage("local", grid, config)
    resources = population_requirements("local", grid, config)
    extraction = embedding_memory(grid, grid.features)
    terms: tuple[WorkTerm, ...] = ()
    stages = (stage,)
    match config.measure:
        case ComplexityMeasure.DISTRIBUTION:
            histogram = config.bins * 64 + 4096
            resources.extend(
                (
                    memory_requirement("histogram_workspace", histogram + 1024, config),
                    memory_requirement("local_extraction", extraction + histogram, config),
                    memory_requirement(
                        "distance_kernel", pair_memory(grid, config, 0) + histogram, config
                    ),
                )
            )
            stages = (
                computation_stage("distance_maximum", grid, config),
                computation_stage("distance_histogram", grid, config),
            )
            terms = (WorkTerm("histogram_bins", config.bins, "exact_scheduled_count"),)
        case ComplexityMeasure.PERMUTATION | ComplexityMeasure.WEIGHTED_PERMUTATION:
            resources.extend(
                (
                    memory_requirement("local_extraction", extraction, config),
                    memory_requirement(
                        "ordinal_workspace",
                        stage.template_value_bytes * 6 + stage.origin_bytes,
                        config,
                    ),
                    ResourceRequirement(
                        "ordinal_alphabet",
                        "max_pattern_length",
                        grid.features,
                        config.max_pattern_length,
                    ),
                )
            )
            terms = (
                WorkTerm(
                    "ordinal_sort_elements", grid.count * grid.features, "exact_scheduled_count"
                ),
                WorkTerm(
                    "ordinal_sort_N_k_log2k",
                    grid.count * grid.features * (grid.features - 1).bit_length(),
                    "asymptotic_size_term",
                ),
                WorkTerm(
                    "ordinal_unique_N_k_log2N",
                    grid.count * grid.features * (grid.count - 1).bit_length(),
                    "asymptotic_size_term",
                ),
            )
        case ComplexityMeasure.SVD:
            rank_size = min(grid.count, grid.features)
            resources.extend(
                (
                    memory_requirement("local_extraction", extraction, config),
                    memory_requirement(
                        "svd_workspace",
                        stage.template_value_bytes * 6 + stage.origin_bytes + rank_size**2 * 8,
                        config,
                    ),
                )
            )
            terms = (
                WorkTerm(
                    "dense_svd_N_k_minNk",
                    grid.count * grid.features * rank_size,
                    "asymptotic_size_term",
                ),
            )
        case (
            ComplexityMeasure.HDSE
            | ComplexityMeasure.SAMPLE
            | ComplexityMeasure.APPROXIMATE
            | ComplexityMeasure.FUZZY
            | ComplexityMeasure.SPECTRAL
        ):
            raise ParameterError("measure", "local plan requires a local estimator")
        case unreachable:
            assert_never(unreachable)
    return stages, tuple(resources), terms


def estimate_complexity(
    input_shape: tuple[int, ...], config: ComplexityConfig | None = None
) -> ComplexityEstimate:
    """Plan the current estimator's complete path without constructing any arrays.

    Eligible unordered pairs differ from computed block cells. Kernels compute
    full diagonal blocks and all masked cells. Memory quantities mirror current
    conservative guards and exclude input allocation, Python/runtime overhead
    beyond guard allowances, and vendor-specific FFT/SVD internals. Numerical
    failures can terminate work early; feasibility never certifies a finite result.
    """
    options = ComplexityConfig() if config is None else config
    parsed_shape = InputShape(shape=input_shape).shape
    elements = prod(parsed_shape)
    if options.measure is ComplexityMeasure.SAMPLE and len(parsed_shape) != 1:
        raise ParameterError("input_shape", "sample entropy requires one input axis")
    if (
        options.measure in PAIR_MEASURES
        and options.measure is not ComplexityMeasure.DISTRIBUTION
        and options.match.ddof >= elements
    ):
        raise ParameterError("ddof", "must be smaller than the number of input elements")
    terms: tuple[WorkTerm, ...] = ()
    match options.measure:
        case ComplexityMeasure.HDSE | ComplexityMeasure.SAMPLE | ComplexityMeasure.FUZZY:
            stages, resources = _paired_plan(parsed_shape, options)
        case ComplexityMeasure.APPROXIMATE:
            stages, resources = _approximate_plan(parsed_shape, options)
        case (
            ComplexityMeasure.DISTRIBUTION
            | ComplexityMeasure.PERMUTATION
            | ComplexityMeasure.WEIGHTED_PERMUTATION
            | ComplexityMeasure.SVD
        ):
            stages, resources, terms = _local_plan(parsed_shape, options)
        case ComplexityMeasure.SPECTRAL:
            stages = ()
            resources = (memory_requirement("fft_workspace", elements * 80, options),)
            terms = (
                WorkTerm(
                    "fft_N_sum_log2_axes",
                    elements * sum((size - 1).bit_length() for size in parsed_shape),
                    "asymptotic_size_term",
                ),
            )
        case unreachable:
            assert_never(unreachable)
    assumptions = (
        "Complete execution path; numerical domain/range errors can terminate it early.",
        "Memory figures reproduce conservative estimator guards, not measured process RSS.",
        "Asymptotic size terms are not operation counts, FLOPs or wall-clock predictions.",
    )
    if options.measure is ComplexityMeasure.FUZZY and options.match.tolerance:
        assumptions += (
            "Fuzzy kernel work requires positive resolved radius; constant relative input skips kernels.",
        )
    components = sum(stage.templates * stage.features for stage in stages)
    if options.measure is ComplexityMeasure.DISTRIBUTION:
        components //= 2
    terms += (
        WorkTerm("input_elements", elements, "exact_scheduled_count"),
        WorkTerm(
            "template_index_components", components * len(parsed_shape), "exact_scheduled_count"
        ),
        WorkTerm(
            "extracted_template_components",
            components,
            "exact_scheduled_count",
        ),
    )
    return ComplexityEstimate(
        config=options,
        input_shape=parsed_shape,
        input_elements=elements,
        input_float64_bytes=elements * 8,
        stages=stages,
        resources=resources,
        terms=terms,
        assumptions=assumptions,
    )
