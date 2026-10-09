# Copyright (c) 2026 Daniel Ari Friedman
"""Immutable configuration and strict JSON results."""

import math
from enum import StrEnum
from typing import ClassVar, Self, assert_never

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictInt, model_validator

from antropy_hd.errors import ParameterError


class Status(StrEnum):
    """Mathematical state of an estimate."""

    FINITE = "finite"
    UNDEFINED = "undefined"
    INFINITE = "infinite"


class EntropyResult(BaseModel):
    """An estimate with explicit degeneracy, parameters and numerical evidence."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", allow_inf_nan=False
    )
    measure: str
    value: float | None
    status: Status = Status.FINITE
    n_observations: int = Field(ge=0)
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    diagnostics: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def consistent_status(self) -> Self:
        """Reject nonfinite values and mismatched status/value pairs."""
        if (self.status is Status.FINITE) != (self.value is not None):
            raise ParameterError(
                "value", "finite status requires a value; other statuses require null"
            )
        return self

    def as_float(self) -> float:
        """Convert an explicitly tagged result to conventional numeric sentinels."""
        match self.status:
            case Status.FINITE:
                if self.value is None:
                    raise ParameterError("value", "finite result has no value")
                return self.value
            case Status.UNDEFINED:
                return math.nan
            case Status.INFINITE:
                return math.inf
            case unreachable:
                assert_never(unreachable)


class Metric(StrEnum):
    """Distance between corresponding values of spatial templates."""

    CHEBYSHEV = "chebyshev"
    EUCLIDEAN = "euclidean"
    CITYBLOCK = "cityblock"


class Exclusion(StrEnum):
    """Origin-pair selection: ordinary self exclusion or source sensitivity."""

    SELF = "self"
    COORDINATE = "coordinate"


class EmbeddingConfig(BaseModel):
    """Spatial geometry and hard limits, resolved against the input dimensionality."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", validate_default=True
    )
    shape: StrictInt | tuple[StrictInt, ...] = 2
    delay: StrictInt | tuple[StrictInt, ...] = 1
    stride: StrictInt | tuple[StrictInt, ...] = 1
    extend_axes: tuple[StrictInt, ...] | None = None
    max_templates: StrictInt = Field(default=10000, ge=2)
    max_pairs: StrictInt = Field(default=50000000, ge=1)
    max_memory_bytes: StrictInt = Field(default=134217728, ge=1024)

    @model_validator(mode="after")
    def positive_geometry(self) -> Self:
        """Validate scalar and per-axis geometry before dimension resolution."""
        for name, value in (("shape", self.shape), ("delay", self.delay), ("stride", self.stride)):
            match value:
                case int():
                    entries = (value,)
                case tuple():
                    entries = value
                case unreachable:
                    assert_never(unreachable)
            if not entries or min(entries) < 1:
                raise ParameterError(name, "requires positive integers")
        if self.extend_axes is not None and (
            not self.extend_axes
            or min(self.extend_axes) < 0
            or len(set(self.extend_axes)) != len(self.extend_axes)
        ):
            raise ParameterError("extend_axes", "requires unique nonnegative axes")
        return self


class MatchConfig(BaseModel):
    """Threshold, distance, origin exclusions and pair block size."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", validate_default=True
    )
    tolerance: float = Field(default=0.2, ge=0, allow_inf_nan=False)
    relative: bool = True
    ddof: StrictInt = Field(default=0, ge=0)
    closed: bool = False
    metric: Metric = Metric.CHEBYSHEV
    exclusion: Exclusion = Exclusion.SELF
    theiler: StrictInt = Field(default=0, ge=0)
    block_size: StrictInt = Field(default=128, ge=1, le=4096)
