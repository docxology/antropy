# Copyright (c) 2026 Daniel Ari Friedman
"""Immutable inference settings and results, distinct from entropy estimates."""

from enum import StrEnum
from typing import ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from antropy_hd.errors import ParameterError


class Pairing(StrEnum):
    """The exchangeable observational unit."""

    INDEPENDENT = "independent"
    PAIRED = "paired"


class Alternative(StrEnum):
    """Inclusive tails of the second-minus-first statistic."""

    TWO_SIDED = "two_sided"
    GREATER = "greater"
    LESS = "less"


class Mode(StrEnum):
    """Permutation allocation strategy."""

    AUTO = "auto"
    EXACT = "exact"
    MONTE_CARLO = "monte_carlo"


class InferenceStatus(StrEnum):
    """Whether an interval has a defined estimand and bounds."""

    DEFINED = "defined"
    UNDEFINED = "undefined"


class ResamplingConfig(BaseModel):
    """Explicit seed and bounded observation/resampling work limits."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", validate_default=True, allow_inf_nan=False
    )
    seed: StrictInt = Field(ge=0)
    pairing: Pairing = Pairing.INDEPENDENT
    resamples: StrictInt = Field(default=9999, ge=1, le=1000000)
    max_samples: StrictInt = Field(default=10000, ge=4, le=10000)
    max_resampling_work: StrictInt = Field(default=100000000, ge=1)


class PermutationConfig(ResamplingConfig):
    """Permutation tails, enumeration ceiling and Monte Carlo draws."""

    alternative: Alternative = Alternative.TWO_SIDED
    mode: Mode = Mode.AUTO
    max_exact_allocations: StrictInt = Field(default=100000, ge=1)


class BootstrapConfig(ResamplingConfig):
    """Percentile bootstrap with linear empirical quantiles."""

    confidence_level: float = Field(default=0.95, gt=0, lt=1)


class PermutationResult(BaseModel):
    """Allocation evidence and p-value; effect uses the original data units."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", allow_inf_nan=False
    )
    effect: float
    effect_numerator: int
    effect_denominator: int = Field(ge=1)
    p_value: float = Field(gt=0, le=1)
    n_first: int = Field(ge=2)
    n_second: int = Field(ge=2)
    allocations: int = Field(ge=1)
    evaluated: int = Field(ge=1)
    extreme: int = Field(ge=0)
    resolution: float = Field(gt=0, le=1)
    effective_mode: Literal[Mode.EXACT, Mode.MONTE_CARLO]
    effective_seed: int | None
    resampling_work: int = Field(ge=1)
    config: PermutationConfig
    assumptions: tuple[str, ...]
    tail_policy: str = "inclusive comparisons of exact binary64 rational contrasts"

    @model_validator(mode="after")
    def consistent_counts(self) -> Self:
        """Reject count metadata inconsistent with its p-value denominator."""
        if self.extreme > self.evaluated:
            raise ParameterError("extreme", "cannot exceed evaluated allocations")
        exact = self.effective_mode is Mode.EXACT
        denominator = self.evaluated if exact else self.evaluated + 1
        numerator = self.extreme if exact else self.extreme + 1
        if self.p_value != numerator / denominator or self.resolution != 1 / denominator:
            raise ParameterError("p_value", "must agree with allocation counts")
        if exact and (self.evaluated != self.allocations or self.effective_seed is not None):
            raise ParameterError("effective_mode", "exact enumeration must cover its population")
        if not exact and (
            self.evaluated != self.config.resamples or self.effective_seed != self.config.seed
        ):
            raise ParameterError("effective_mode", "Monte Carlo must report its configured draws")
        return self


class IntervalResult(BaseModel):
    """A score or percentile interval with explicit undefined boundaries."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", allow_inf_nan=False
    )
    estimate: float | None
    lower: float | None
    upper: float | None
    status: InferenceStatus = InferenceStatus.DEFINED
    method: Literal["percentile_bootstrap", "wilson"]
    confidence_level: float = Field(gt=0, lt=1)
    n_observations: int = Field(ge=0)
    resamples: int = Field(default=0, ge=0)
    resampling_work: int = Field(default=0, ge=0)
    config: BootstrapConfig | None = None
    assumptions: tuple[str, ...]

    @model_validator(mode="after")
    def consistent_bounds(self) -> Self:
        """Require finite ordered bounds and an estimate for defined intervals."""
        values = (self.estimate, self.lower, self.upper)
        if self.status is InferenceStatus.UNDEFINED:
            if any(value is not None for value in values):
                raise ParameterError("bounds", "undefined intervals require null values")
        elif self.estimate is None or self.lower is None or self.upper is None:
            raise ParameterError("bounds", "defined intervals require all values")
        elif self.lower > self.upper:
            raise ParameterError("bounds", "lower bound cannot exceed upper bound")
        return self
