# Copyright (c) 2026 Daniel Ari Friedman
"""Strict controls and records for replicated spatial-complexity experiments."""

from __future__ import annotations

import math
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from antropy_hd.complexity import ComplexityEstimate
from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import BatchResult

type Control = Literal["constant", "checkerboard", "gaussian", "correlated", "shuffled"]
type Family = Literal["mix", "constant", "checkerboard", "gaussian", "correlated", "shuffled"]
type Geometry = Literal["native", "flattened", "symbols"]


class StudyPlan(BaseModel):
    """A finite, fully consumed design; trial seeds are independent of list ordering."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    schema_version: Literal[1] = 1
    seed: StrictInt = Field(ge=0)
    shapes: tuple[tuple[StrictInt, ...], ...] = Field(min_length=1)
    mixing_probabilities: tuple[float, ...] = Field(min_length=1)
    controls: tuple[Control, ...] = Field(min_length=1)
    replicates: StrictInt = Field(ge=2)
    radii: tuple[float, ...] = Field(min_length=1)
    period: float = Field(gt=0)
    phase_origin: StrictInt = Field(ge=0)
    embedding_shape: StrictInt = Field(ge=1)
    gaussian_sd: float = Field(gt=0)
    correlation_steps: StrictInt = Field(ge=1, le=100)
    symbol_range: tuple[float, float]
    symbol_bins: StrictInt = Field(ge=3, le=256)
    max_input_elements: StrictInt = Field(ge=1)
    max_fields: StrictInt = Field(ge=1)
    max_distance_component_visits: StrictInt = Field(ge=1)
    max_templates: StrictInt = Field(ge=2)
    max_pairs: StrictInt = Field(ge=1)
    max_memory_bytes: StrictInt = Field(ge=1024)
    block_size: StrictInt = Field(ge=1, le=4096)

    @model_validator(mode="after")
    def feasible_design(self) -> StudyPlan:
        """Reject duplicates, invalid probabilities and geometrically impossible designs."""
        for values in (self.shapes, self.mixing_probabilities, self.controls, self.radii):
            if len(set(values)) != len(values):
                raise ParameterError("study", "Design axes must not contain duplicates")
        if min(self.mixing_probabilities) < 0 or max(self.mixing_probabilities) > 1:
            raise ParameterError("mixing_probabilities", "Probabilities must lie in [0, 1]")
        if min(self.radii) <= 0 or self.symbol_range[0] >= self.symbol_range[1]:
            raise ParameterError("study", "Radii and symbol range must be valid")
        if (
            len(self.shapes)
            * (len(self.controls) + len(self.mixing_probabilities))
            * self.replicates
            > self.max_fields
        ):
            raise ParameterError("study", "Trial matrix exceeds the declared field budget")
        for shape in self.shapes:
            if not shape or min(shape) <= self.embedding_shape:
                raise ParameterError("shapes", "All axes must support the extended template")
            if math.prod(shape) > self.max_input_elements:
                raise ParameterError("shapes", "Input exceeds the declared element budget")
        return self


class StudyCase(BaseModel):
    """One field, with common random numbers across MIX probabilities within a trial."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    shape: tuple[StrictInt, ...] = Field(min_length=1)
    family: Family
    mixing: float | None = Field(ge=0, le=1)
    trial: StrictInt = Field(ge=0)

    @model_validator(mode="after")
    def valid_case(self) -> StudyCase:
        """Require valid native axes and a mixing probability only for MIX fields."""
        if min(self.shape) < 1 or (self.family == "mix") != (self.mixing is not None):
            raise ParameterError("case", "Invalid field geometry or family probability")
        return self

    @property
    def id(self) -> str:
        """Use round-trip float spelling and full shape for unambiguous file identities."""
        probability = "" if self.mixing is None else f"-p{self.mixing}"
        return f"{self.family}{probability}-{'x'.join(map(str, self.shape))}-trial{self.trial}"


class StudyRecord(BaseModel):
    """Stored input plus exact native, flattened and fixed-symbol batch identities."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    case: StudyCase
    input_file: str
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    native: BatchResult
    flattened: BatchResult
    symbols: BatchResult


class StudyComplexityRecord(BaseModel):
    """Plan one actual invocation, keeping original and analyzed geometry separate."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    original_shape: tuple[int, ...]
    geometry: Literal["native", "flattened"]
    analysis_id: str
    estimate: ComplexityEstimate
    guard_peak_bytes: int
    distance_component_visits: int


class StudyReport(BaseModel):
    """Consumed plan, platform metadata and every declared trial result."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    plan: StudyPlan
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    records: tuple[StudyRecord, ...] = Field(min_length=1)


class StudyRow(BaseModel):
    """One scalar result; null values preserve infinite or undefined estimates."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    case_id: str
    shape: str
    dimension: StrictInt = Field(ge=1)
    family: Family
    mixing: float | None
    trial: StrictInt = Field(ge=0)
    geometry: Literal["native", "flattened", "symbols"]
    analysis_id: str
    measure: str
    radius: float | None
    value: float | None
    status: Literal["finite", "undefined", "infinite"]
    observations: StrictInt = Field(ge=0)
    parameters_json: str
    diagnostics_json: str


class StudySummary(BaseModel):
    """Conditional finite mean and sample SD, accompanied by every outcome count."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    shape: str
    dimension: StrictInt = Field(ge=1)
    family: Family
    mixing: float | None
    geometry: Literal["native", "flattened", "symbols"]
    analysis_id: str
    measure: str
    radius: float | None
    n_total: StrictInt = Field(ge=1)
    n_finite: StrictInt = Field(ge=0)
    n_undefined: StrictInt = Field(ge=0)
    n_infinite: StrictInt = Field(ge=0)
    finite_mean: float | None
    finite_sample_sd: float | None

    @model_validator(mode="after")
    def consistent_summary(self) -> StudySummary:
        """Preserve every outcome and define variability only for replicated finite values."""
        if self.n_total != self.n_finite + self.n_undefined + self.n_infinite:
            raise ParameterError("summary", "Outcome counts do not sum to the trial count")
        if (self.n_finite == 0) != (self.finite_mean is None) or (self.n_finite < 2) != (
            self.finite_sample_sd is None
        ):
            raise ParameterError("summary", "Mean or sample SD is inconsistent with finite trials")
        if self.finite_sample_sd is not None and self.finite_sample_sd < 0:
            raise ParameterError("summary", "Sample SD cannot be negative")
        return self
