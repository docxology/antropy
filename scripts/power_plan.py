# Copyright (c) 2026 Daniel Ari Friedman
"""Prospective independent-field scenarios and fully consumed operating-characteristic controls."""

from __future__ import annotations

import math
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from antropy_hd.errors import ParameterError
from antropy_hd.inference_models import Pairing, PermutationConfig
from antropy_hd.orchestration import AnalysisSpec


class PowerScenario(BaseModel):
    """A stochastic identical-distribution null or prespecified replacement alternative."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    label: str = Field(min_length=1)
    role: Literal["null", "alternative"]
    first_probability: float = Field(ge=0, le=1)
    second_probability: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def declared_null(self) -> PowerScenario:
        """Prevent a differently generated alternative from being labeled a null control."""
        equal = self.first_probability == self.second_probability
        if (self.role == "null") != equal:
            raise ParameterError(
                "scenario", "Null labels require identical generating probabilities"
            )
        return self


class PowerAnalysis(BaseModel):
    """One registered estimator with explicit transformation and plot/table identity."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    label: str = Field(min_length=1)
    geometry: Literal["native", "flattened", "symbols"]
    spec: AnalysisSpec


class PowerPlan(BaseModel):
    """All outer simulation, inner inference, symbolization and resource controls."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    schema_version: Literal[1] = 1
    seed: StrictInt = Field(ge=0)
    shapes: tuple[tuple[StrictInt, ...], ...] = Field(min_length=1)
    sample_sizes: tuple[StrictInt, ...] = Field(min_length=1)
    scenarios: tuple[PowerScenario, ...] = Field(min_length=1)
    analyses: tuple[PowerAnalysis, ...] = Field(min_length=1)
    repetitions: StrictInt = Field(ge=2)
    alpha: float = Field(gt=0, lt=1)
    confidence_level: float = Field(gt=0, lt=1)
    target_power: float = Field(gt=0, lt=1)
    multiplicity: Literal["none", "holm"]
    test: PermutationConfig
    period: float = Field(gt=0)
    phase_origin: StrictInt = Field(ge=0)
    symbol_range: tuple[float, float]
    symbol_bins: StrictInt = Field(ge=3, le=256)
    max_input_elements: StrictInt = Field(ge=1)
    max_fields: StrictInt = Field(ge=1)
    max_distance_component_visits: StrictInt = Field(ge=1)
    max_inference_work: StrictInt = Field(ge=1)
    max_pool_bytes: StrictInt = Field(ge=1024)
    max_report_bytes: StrictInt = Field(ge=1024)

    @model_validator(mode="after")
    def coherent_design(self) -> PowerPlan:
        """Reject duplicated cells, impossible axes and falsely independent pairing."""
        for items in (self.shapes, self.sample_sizes):
            if len(items) != len(set(items)):
                raise ParameterError("power", "Design axes must be unique")
        ids = [scenario.id for scenario in self.scenarios]
        analyses = [analysis.spec.id for analysis in self.analyses]
        if len(ids) != len(set(ids)) or len(analyses) != len(set(analyses)):
            raise ParameterError("power", "Scenario and analysis identities must be unique")
        if min(self.sample_sizes) < 2 or self.symbol_range[0] >= self.symbol_range[1]:
            raise ParameterError(
                "power", "Groups require at least two fields and a valid symbol range"
            )
        if self.test.pairing is not Pairing.INDEPENDENT:
            raise ParameterError("pairing", "This generator supplies independent field groups")
        if not any(
            scenario.role == "null" and scenario.first_probability > 0
            for scenario in self.scenarios
        ):
            raise ParameterError(
                "scenarios", "At least one stochastic same-probability null is required"
            )
        for shape in self.shapes:
            if not shape or min(shape) < 1 or math.prod(shape) > self.max_input_elements:
                raise ParameterError(
                    "shapes", "A native field exceeds the declared geometry budget"
                )
        if self.field_count > self.max_fields:
            raise ParameterError("max_fields", "Planned field pools exceed the declared budget")
        return self

    @property
    def field_count(self) -> int:
        """Generate one maximum-size pool per group and reuse its prefixes across n."""
        return (
            len(self.shapes) * len(self.scenarios) * self.repetitions * 2 * max(self.sample_sizes)
        )

    @property
    def experiment_count(self) -> int:
        """Every outer experiment contributes a separate decision for every analysis."""
        return (
            len(self.shapes)
            * len(self.scenarios)
            * len(self.sample_sizes)
            * self.repetitions
            * len(self.analyses)
        )
