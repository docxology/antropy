# Copyright (c) 2026 Daniel Ari Friedman
"""Typed planning records and exact lattice/block combinatorics without arrays."""

from dataclasses import dataclass
from enum import StrEnum
from math import prod
from typing import ClassVar, Final, Literal, assert_never

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from antropy_hd.embedding import resolve_geometry
from antropy_hd.errors import ParameterError
from antropy_hd.models import EmbeddingConfig, Exclusion, MatchConfig


class ComplexityMeasure(StrEnum):
    """Observation estimators whose current implementation is modeled explicitly."""

    HDSE = "hdse"
    SAMPLE = "sample_entropy"
    APPROXIMATE = "approximate_entropy"
    FUZZY = "fuzzy_entropy"
    DISTRIBUTION = "distribution_entropy"
    PERMUTATION = "permutation_entropy"
    WEIGHTED_PERMUTATION = "weighted_permutation_entropy"
    SPECTRAL = "spectral_entropy"
    SVD = "svd_entropy"


class ComplexityConfig(BaseModel):
    """Estimator geometry, blocked kernel and applicable algorithm resource settings.

    Spectral planning maps embedding.max_memory_bytes to spectral_entropy's
    max_memory_bytes argument; its other geometry fields have no spectral effect.
    Non-pair measures have no radius or origin-exclusion kernel.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    measure: ComplexityMeasure = ComplexityMeasure.HDSE
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    match: MatchConfig = Field(default_factory=MatchConfig)
    bins: StrictInt = Field(default=16, ge=2, le=100000)
    max_pattern_length: StrictInt = Field(default=10, ge=2, le=32)

    @model_validator(mode="after")
    def valid_method_settings(self) -> ComplexityConfig:
        """Reject settings the associated estimator cannot consume."""
        match self.measure:
            case ComplexityMeasure.APPROXIMATE:
                if self.match.exclusion != Exclusion.SELF or self.match.theiler:
                    raise ParameterError("match", "approximate entropy includes self matches")
            case ComplexityMeasure.DISTRIBUTION:
                if (
                    self.match.tolerance,
                    self.match.relative,
                    self.match.ddof,
                    self.match.closed,
                ) != (0.2, True, 0, False):
                    raise ParameterError("match", "distribution entropy has no threshold")
            case (
                ComplexityMeasure.HDSE
                | ComplexityMeasure.SAMPLE
                | ComplexityMeasure.FUZZY
                | ComplexityMeasure.PERMUTATION
                | ComplexityMeasure.WEIGHTED_PERMUTATION
                | ComplexityMeasure.SPECTRAL
                | ComplexityMeasure.SVD
            ):
                pass
            case unreachable:
                assert_never(unreachable)
        return self


class InputShape(BaseModel):
    """Parse strictly positive integer axis lengths at the planning boundary."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    shape: tuple[StrictInt, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_axes(self) -> InputShape:
        """Reject empty axes rather than estimating an invalid dataset."""
        if min(self.shape) < 1:
            raise ParameterError("input_shape", "axis lengths must be positive")
        return self


@dataclass(frozen=True, slots=True)
class ResourceRequirement:
    """An exact population limit or the estimator's conservative array guard."""

    stage: str
    parameter: Literal["max_templates", "max_pairs", "max_memory_bytes", "max_pattern_length"]
    required: int
    limit: int


@dataclass(frozen=True, slots=True)
class WorkTerm:
    """A counted operation input or an explicitly symbolic algorithm-size term."""

    name: str
    count: int
    interpretation: Literal["exact_scheduled_count", "asymptotic_size_term"]


@dataclass(frozen=True, slots=True)
class ComputationStage:
    """One distance traversal on an exact native-dimensional template population."""

    name: str
    template_shape: tuple[int, ...]
    origin_counts: tuple[int, ...]
    templates: int
    features: int
    candidate_pairs: int
    eligible_pairs: int
    computed_distance_cells: int
    distance_component_visits: int
    origin_component_visits: int
    distance_blocks: int
    template_value_bytes: int
    origin_bytes: int


class ComplexityEstimate(BaseModel):
    """Implementation work and guards; no runtime, FLOP or process-RSS prediction."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    config: ComplexityConfig
    input_shape: tuple[int, ...]
    input_elements: int
    input_float64_bytes: int
    stages: tuple[ComputationStage, ...]
    resources: tuple[ResourceRequirement, ...]
    terms: tuple[WorkTerm, ...]
    assumptions: tuple[str, ...]

    @property
    def resource_violations(self) -> tuple[ResourceRequirement, ...]:
        """Return every declared guard that the planned request exceeds."""
        return tuple(item for item in self.resources if item.required > item.limit)

    @property
    def feasible(self) -> bool:
        """Indicate resource feasibility, without claiming numerical definability."""
        return not self.resource_violations

    @property
    def computed_distance_cells(self) -> int:
        """Sum all computed cells, including masked, duplicate and self cells."""
        return sum(stage.computed_distance_cells for stage in self.stages)

    @property
    def distance_component_visits(self) -> int:
        """Sum scalar coordinate-difference evaluations in distance kernels."""
        return sum(stage.distance_component_visits for stage in self.stages)

    @property
    def guard_peak_bytes(self) -> int:
        """Largest current estimator guard, excluding separately reported input bytes."""
        return max(
            (item.required for item in self.resources if item.parameter == "max_memory_bytes"),
            default=0,
        )


@dataclass(frozen=True, slots=True)
class Lattice:
    """Native-origin grid resolved without constructing origins or templates."""

    shape: tuple[int, ...]
    counts: tuple[int, ...]
    stride: tuple[int, ...]

    @property
    def count(self) -> int:
        """Count all Cartesian origin tuples exactly."""
        return prod(self.counts)

    @property
    def features(self) -> int:
        """Count flattened samples within one extracted local block."""
        return prod(self.shape)


def lattice(
    input_shape: tuple[int, ...], shape: tuple[int, ...], config: EmbeddingConfig
) -> Lattice:
    """Resolve full valid origins for anisotropic delay and stride."""
    delay = resolve_geometry(config.delay, len(input_shape), "delay")
    stride = resolve_geometry(config.stride, len(input_shape), "stride")
    stops = tuple(
        size - (width - 1) * lag for size, width, lag in zip(input_shape, shape, delay, strict=True)
    )
    if min(stops) < 1:
        raise ParameterError("shape", "embedding span exceeds an input axis")
    return Lattice(
        shape,
        tuple((stop - 1) // step + 1 for stop, step in zip(stops, stride, strict=True)),
        stride,
    )


def eligible_pairs(grid: Lattice, matching: MatchConfig) -> int:
    """Count unordered lattice pairs after exact coordinate and Theiler exclusions."""
    close: list[int] = []
    for count, step in zip(grid.counts, grid.stride, strict=True):
        width = min(count - 1, matching.theiler // step)
        close.append(count * (2 * width + 1) - width * (width + 1))
    match matching.exclusion:
        case Exclusion.SELF:
            return (grid.count**2 - prod(close)) // 2
        case Exclusion.COORDINATE:
            all_distinct = prod(count * (count - 1) for count in grid.counts)
            excluded = prod(pairs - count for pairs, count in zip(close, grid.counts, strict=True))
            return (all_distinct - excluded) // 2
        case unreachable:
            assert_never(unreachable)


def block_schedule(count: int, block_size: int, *, ordered: bool = False) -> tuple[int, int]:
    """Count distance cells and calls, including complete diagonal blocks."""
    complete, remainder = divmod(count, block_size)
    blocks = complete + int(remainder > 0)
    if ordered:
        return count**2, blocks**2
    diagonal = complete * block_size**2 + remainder**2
    return (count**2 + diagonal) // 2, blocks * (blocks + 1) // 2


PAIR_MEASURES: Final = frozenset(
    (
        ComplexityMeasure.HDSE,
        ComplexityMeasure.SAMPLE,
        ComplexityMeasure.APPROXIMATE,
        ComplexityMeasure.FUZZY,
        ComplexityMeasure.DISTRIBUTION,
    )
)


def embedding_memory(grid: Lattice, features: int) -> int:
    """Mirror the extraction guard, including origins, indices and offsets."""
    ndim = len(grid.shape)
    return grid.count * (features * 8 + ndim * 32 + 16) + grid.features * ndim * 8 + 4096


def pair_memory(grid: Lattice, config: ComplexityConfig, extra: int) -> int:
    """Mirror guard_pairs' template, consumer-lifetime and blocked scratch budget."""
    storage = grid.count * (grid.features * 8 + len(grid.shape) * 8)
    return storage + extra + min(grid.count, config.match.block_size) ** 2 * 160 + 4096


def memory_requirement(name: str, required: int, config: ComplexityConfig) -> ResourceRequirement:
    """Record one current conservative memory guard against its declared budget."""
    return ResourceRequirement(
        name, "max_memory_bytes", required, config.embedding.max_memory_bytes
    )


def population_requirements(
    name: str, grid: Lattice, config: ComplexityConfig
) -> list[ResourceRequirement]:
    """Mirror independent template and pre-exclusion candidate-pair limits."""
    result = [
        ResourceRequirement(name, "max_templates", grid.count, config.embedding.max_templates)
    ]
    if config.measure in PAIR_MEASURES:
        result.append(
            ResourceRequirement(
                name, "max_pairs", grid.count * (grid.count - 1) // 2, config.embedding.max_pairs
            )
        )
    return result


def computation_stage(name: str, grid: Lattice, config: ComplexityConfig) -> ComputationStage:
    """Describe one actual block schedule or a local-template-only stage."""
    cells, blocks, pairs = 0, 0, 0
    ordered = config.measure is ComplexityMeasure.APPROXIMATE
    if config.measure in PAIR_MEASURES:
        cells, blocks = block_schedule(grid.count, config.match.block_size, ordered=ordered)
        pairs = grid.count**2 if ordered else eligible_pairs(grid, config.match)
        if config.measure is ComplexityMeasure.FUZZY and config.match.tolerance == 0:
            cells, blocks = 0, 0
    return ComputationStage(
        name,
        grid.shape,
        grid.counts,
        grid.count,
        grid.features,
        grid.count * (grid.count - 1) // 2 if config.measure in PAIR_MEASURES else 0,
        pairs,
        cells,
        cells * grid.features,
        0 if ordered else cells * len(grid.shape),
        blocks,
        grid.count * grid.features * 8,
        grid.count * len(grid.shape) * 8,
    )
