# Copyright (c) 2026 Daniel Ari Friedman
"""Strict scientific records separating unavailable tests from observed rejection rates."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, model_validator

from antropy_hd.errors import ParameterError
from antropy_hd.inference_models import IntervalResult, PermutationResult
from antropy_hd.models import EntropyResult
from scripts.power_plan import PowerPlan


class PowerPool(BaseModel):
    """A stored tensor of independently generated fields; its leading axis indexes subjects."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    id: str
    scenario_id: str
    shape: tuple[StrictInt, ...]
    replicate: StrictInt = Field(ge=0)
    group: Literal["first", "second"]
    input_file: str
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    array_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subjects: StrictInt = Field(ge=2)


class FieldEstimate(BaseModel):
    """One whole-field unit, retaining all estimator values, parameters, counts and statuses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    field_id: str
    pool_id: str
    pool_index: StrictInt = Field(ge=0)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    results: dict[str, EntropyResult]


class PowerDecision(BaseModel):
    """One prespecified whole-field comparison and its actual inference result or failure."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    scenario_id: str
    shape: tuple[StrictInt, ...]
    sample_size: StrictInt = Field(ge=2)
    replicate: StrictInt = Field(ge=0)
    analysis_id: str
    status: Literal["available", "unavailable"]
    undefined_first: StrictInt = Field(ge=0)
    undefined_second: StrictInt = Field(ge=0)
    infinite_first: StrictInt = Field(ge=0)
    infinite_second: StrictInt = Field(ge=0)
    mean_difference: float | None
    p_value: float | None = Field(ge=0, le=1)
    adjusted_p_value: float | None = Field(ge=0, le=1)
    raw_rejected: StrictBool
    rejected: StrictBool
    test: PermutationResult | None

    @model_validator(mode="after")
    def unavailable_is_not_zero(self) -> PowerDecision:
        """Never encode an unavailable entropy comparison as an observed zero or rejection."""
        failed = (
            self.undefined_first
            + self.undefined_second
            + self.infinite_first
            + self.infinite_second
        )
        available = self.status == "available"
        if (
            self.undefined_first + self.infinite_first > self.sample_size
            or self.undefined_second + self.infinite_second > self.sample_size
        ):
            raise ParameterError("decision", "Nonfinite counts exceed the declared group size")
        if available != (failed == 0) or available != (self.test is not None):
            raise ParameterError(
                "decision", "Test availability differs from the retained field statuses"
            )
        if not available and (
            self.p_value is not None
            or self.adjusted_p_value is not None
            or self.mean_difference is not None
            or self.rejected
            or self.raw_rejected
        ):
            raise ParameterError(
                "decision", "Unavailable decisions must remain null and unrejected"
            )
        if available and (
            self.p_value is None or self.adjusted_p_value is None or self.mean_difference is None
        ):
            raise ParameterError("decision", "Available decisions require every inference value")
        if self.test is not None and (
            self.test.n_first != self.sample_size
            or self.test.n_second != self.sample_size
            or self.p_value != self.test.p_value
            or self.mean_difference != self.test.effect
        ):
            raise ParameterError("decision", "Decision values differ from its retained test")
        return self


class PowerSummary(BaseModel):
    """Outer Monte Carlo uncertainty with every denominator and failure cause explicit."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    scenario_id: str
    role: Literal["null", "alternative"]
    shape: tuple[StrictInt, ...]
    sample_size: StrictInt = Field(ge=2)
    analysis_id: str
    attempted: StrictInt = Field(ge=1)
    available: StrictInt = Field(ge=0)
    unavailable: StrictInt = Field(ge=0)
    rejected: StrictInt = Field(ge=0)
    raw_rejected: StrictInt = Field(ge=0)
    conditional_rejection: IntervalResult
    unconditional_rejection: IntervalResult
    availability: IntervalResult
    missing_decision_lower: float = Field(ge=0, le=1)
    missing_decision_upper: float = Field(ge=0, le=1)
    mean_difference_mean: float | None
    mean_difference_sd: float | None = Field(ge=0)
    minimum_p_resolution: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def consistent_denominators(self) -> PowerSummary:
        """Reject contradictory counts, missing effects and mislabeled binomial estimates."""
        if (
            self.available + self.unavailable != self.attempted
            or not self.rejected <= self.raw_rejected <= self.available <= self.attempted
        ):
            raise ParameterError("summary", "Counts must retain every attempted decision")
        if (
            self.missing_decision_lower != self.rejected / self.attempted
            or self.missing_decision_upper != (self.rejected + self.unavailable) / self.attempted
        ):
            raise ParameterError("summary", "Missing-decision range differs from the counts")
        if (self.mean_difference_mean is not None) != (self.available > 0) or (
            self.mean_difference_sd is not None
        ) != (self.available > 1):
            raise ParameterError("summary", "Effect summaries require available comparisons")
        expected = (
            (
                self.conditional_rejection,
                self.available,
                self.rejected / self.available if self.available else None,
            ),
            (self.unconditional_rejection, self.attempted, self.rejected / self.attempted),
            (self.availability, self.attempted, self.available / self.attempted),
        )
        for interval, total, proportion in expected:
            if (
                interval.method != "wilson"
                or interval.n_observations != total
                or interval.estimate != proportion
            ):
                raise ParameterError("summary", "Binomial intervals differ from the denominators")
        return self


class InferenceSchedule(BaseModel):
    """Exact allocation counts and configured inner-work bounds for each field sample size."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    sample_size: StrictInt = Field(ge=2)
    allocations: StrictInt = Field(ge=1)
    evaluated: StrictInt = Field(ge=1)
    method: Literal["exact", "monte_carlo"]
    work: StrictInt = Field(ge=1)
    resolution: float = Field(gt=0, le=1)


class PowerPreflight(BaseModel):
    """Whole-design scheduled work, prior to any field allocation or output creation."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    fields: StrictInt = Field(ge=1)
    experiments: StrictInt = Field(ge=1)
    distance_component_visits: StrictInt = Field(ge=0)
    inference_work: StrictInt = Field(ge=1)
    peak_pool_bytes: StrictInt = Field(ge=1)
    schedules: tuple[InferenceSchedule, ...]
    worst_case_mc_standard_error: float = Field(gt=0)


class PowerReport(BaseModel):
    """Complete declared design and actual retained scientific outcomes, not observed power."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    plan: PowerPlan
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    resources: PowerPreflight
    pools: tuple[PowerPool, ...] = Field(min_length=1)
    estimates: tuple[FieldEstimate, ...] = Field(min_length=1)
    experiments: tuple[PowerDecision, ...] = Field(min_length=1)
    summaries: tuple[PowerSummary, ...] = Field(min_length=1)
