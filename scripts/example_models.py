# Copyright (c) 2026 Daniel Ari Friedman
"""Strict YAML controls for bounded, reusable scientific examples."""

import math
from enum import StrEnum
from typing import ClassVar, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    model_validator,
)

from antropy_hd.complexity import ComplexityConfig, ComplexityMeasure, estimate_complexity
from antropy_hd.errors import ParameterError
from antropy_hd.inference_models import BootstrapConfig, PermutationConfig
from antropy_hd.models import EmbeddingConfig, MatchConfig
from antropy_hd.symbolization import SymbolizationConfig


class ExampleKind(StrEnum):
    """The finite set of checked example plan types."""

    SPATIAL = "spatial"
    ALPHABET = "alphabet"
    PLANNING = "planning"
    INFERENCE = "inference"


class ExampleModel(BaseModel):
    """Immutable configuration with no ignored settings or nonfinite values."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", allow_inf_nan=False
    )


class NormalField(ExampleModel):
    """Gaussian amplitude controls consumed by the real NumPy generator."""

    mean: StrictFloat
    standard_deviation: StrictFloat = Field(ge=0)


class SpatialField(NormalField):
    """Native-grid sine, linear trend and Gaussian noise controls."""

    sine_axis: StrictInt = Field(ge=0)
    sine_amplitude: StrictFloat
    sine_divisor: StrictFloat = Field(gt=0)
    trend_slope: StrictFloat


class SpatialDesign(ExampleModel):
    """One native input grid and its full embedding/matching configuration."""

    input_shape: tuple[StrictInt, ...] = Field(min_length=1)
    embedding: EmbeddingConfig
    match: MatchConfig


def validate_shape(shape: tuple[int, ...], limit: int) -> None:
    """Reject unsupported axes or input allocations before generating fields."""
    if not shape or min(shape) < 1 or math.prod(shape) > limit:
        raise ParameterError("input_shape", "requires positive axes within max_input_elements")


class SpatialPlan(ExampleModel):
    """Anisotropic spatial cases and every numerical field/measure control."""

    schema_version: Literal[1] = 1
    kind: Literal["spatial"]
    seed: StrictInt = Field(ge=0)
    field: SpatialField
    cases: tuple[SpatialDesign, ...] = Field(min_length=1)
    max_cases: StrictInt = Field(ge=1)
    max_input_elements: StrictInt = Field(ge=1)
    entropy_base: StrictFloat = Field(gt=1)
    weighted_permutation_normalize: StrictBool
    max_pattern_length: StrictInt = Field(ge=2, le=32)
    svd_demean: StrictBool
    svd_normalize: StrictBool

    @model_validator(mode="after")
    def feasible_designs(self) -> Self:
        """Preflight every geometry and guard before any synthetic allocation."""
        if len(self.cases) > self.max_cases or len(set(self.cases)) != len(self.cases):
            raise ParameterError("cases", "requires unique cases within max_cases")
        for case in self.cases:
            validate_shape(case.input_shape, self.max_input_elements)
            if self.field.sine_axis >= len(case.input_shape):
                raise ParameterError("sine_axis", "axis must exist in every native field")
            for measure in (
                ComplexityMeasure.HDSE,
                ComplexityMeasure.WEIGHTED_PERMUTATION,
                ComplexityMeasure.SVD,
            ):
                estimate = estimate_complexity(
                    case.input_shape,
                    ComplexityConfig(
                        measure=measure,
                        embedding=case.embedding,
                        match=case.match,
                        max_pattern_length=self.max_pattern_length,
                    ),
                )
                if not estimate.feasible:
                    raise ParameterError(
                        "cases", "estimator request exceeds configured resource guards"
                    )
        return self


class FieldOverride(ExampleModel):
    """A declared finite value at a native-grid index."""

    index: tuple[StrictInt, ...] = Field(min_length=1)
    value: StrictFloat


class AlphabetPlan(ExampleModel):
    """Fixed amplitude categories, explicit tails and retained zero bins."""

    schema_version: Literal[1] = 1
    kind: Literal["alphabet"]
    seed: StrictInt = Field(ge=0)
    input_shape: tuple[StrictInt, ...] = Field(min_length=1)
    field: NormalField
    overrides: tuple[FieldOverride, ...]
    symbolization: SymbolizationConfig
    entropy_base: StrictFloat = Field(ge=2, le=2)
    max_input_elements: StrictInt = Field(ge=1)

    @model_validator(mode="after")
    def valid_field(self) -> Self:
        """Reject out-of-grid or duplicate overrides before assigning symbols."""
        validate_shape(self.input_shape, self.max_input_elements)
        if len({item.index for item in self.overrides}) != len(self.overrides):
            raise ParameterError("overrides", "indices must be unique")
        for item in self.overrides:
            if len(item.index) != len(self.input_shape) or any(
                i < 0 or i >= size for i, size in zip(item.index, self.input_shape, strict=True)
            ):
                raise ParameterError("overrides", "every index must exist in the native grid")
        return self


class PlanningPlan(ExampleModel):
    """Real HDSE block schedules and a separate allocation-free shape request."""

    schema_version: Literal[1] = 1
    kind: Literal["planning"]
    seed: StrictInt = Field(ge=0)
    input_shape: tuple[StrictInt, ...] = Field(min_length=1)
    field: NormalField
    embedding: EmbeddingConfig
    match: MatchConfig
    block_sizes: tuple[StrictInt, ...] = Field(min_length=1)
    max_input_elements: StrictInt = Field(ge=1)
    below_guard_bytes: StrictInt = Field(ge=1)
    large_shape: tuple[StrictInt, ...] = Field(min_length=1)
    large_config: ComplexityConfig

    @model_validator(mode="after")
    def feasible_schedules(self) -> Self:
        """Require executable bounded cases and valid negative-control budgets."""
        validate_shape(self.input_shape, self.max_input_elements)
        if len(set(self.block_sizes)) != len(self.block_sizes):
            raise ParameterError("block_sizes", "block schedules must be unique")
        for block in self.block_sizes:
            matching = MatchConfig.model_validate(self.match.model_dump() | {"block_size": block})
            estimate = estimate_complexity(
                self.input_shape, ComplexityConfig(embedding=self.embedding, match=matching)
            )
            if not estimate.feasible or estimate.guard_peak_bytes - self.below_guard_bytes < 1024:
                raise ParameterError(
                    "planning", "request must fit guards and support the below-guard control"
                )
        _ = estimate_complexity(self.large_shape, self.large_config)
        return self


class BinomialPlan(ExampleModel):
    """A declared Bernoulli count and confidence level."""

    successes: StrictInt = Field(ge=0)
    total: StrictInt = Field(ge=0)
    confidence_level: StrictFloat = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def valid_counts(self) -> Self:
        """Reject successes outside the declared number of trials."""
        if self.successes > self.total:
            raise ParameterError("successes", "cannot exceed total")
        return self


class InferencePlan(ExampleModel):
    """Explicit replicate groups, seeds, budgets and a declared p-value family."""

    schema_version: Literal[1] = 1
    kind: Literal["inference"]
    first: tuple[StrictFloat, ...] = Field(min_length=2)
    second: tuple[StrictFloat, ...] = Field(min_length=2)
    permutation: PermutationConfig
    bootstrap: BootstrapConfig
    binomial: BinomialPlan
    additional_p_values: tuple[StrictFloat, ...]

    @model_validator(mode="after")
    def valid_family(self) -> Self:
        """Require all explicitly declared family members to be valid probabilities."""
        if any(not 0 <= value <= 1 for value in self.additional_p_values):
            raise ParameterError("additional_p_values", "requires probabilities in [0, 1]")
        return self


type ExamplePlan = SpatialPlan | AlphabetPlan | PlanningPlan | InferencePlan
