# Copyright (c) 2026 Daniel Ari Friedman
"""Strict controls and observable records for computational benchmarks."""

from __future__ import annotations

import itertools
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from antropy_hd.complexity import ComplexityConfig, ComplexityEstimate, estimate_complexity
from antropy_hd.errors import ParameterError
from antropy_hd.models import EmbeddingConfig, EntropyResult, MatchConfig


class BenchmarkPlan(BaseModel):
    """A bounded shape/block sweep, including warmup and timed repetition controls."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", allow_inf_nan=False
    )
    schema_version: Literal[1] = 1
    seed: StrictInt = Field(ge=0)
    shapes: tuple[tuple[StrictInt, ...], ...] = Field(min_length=1)
    block_sizes: tuple[StrictInt, ...] = Field(min_length=1)
    repetitions: StrictInt = Field(ge=2, le=100)
    warmups: StrictInt = Field(ge=0, le=10)
    max_input_elements: StrictInt = Field(ge=1)
    embedding: EmbeddingConfig
    match: MatchConfig

    @model_validator(mode="after")
    def feasible_geometry(self) -> BenchmarkPlan:
        """Reject duplicate sweeps and resource-infeasible requests before allocating inputs."""
        if len(set(self.shapes)) != len(self.shapes) or len(set(self.block_sizes)) != len(
            self.block_sizes
        ):
            raise ParameterError("benchmark", "Shape/block axes must be unique")
        for shape, block in itertools.product(self.shapes, self.block_sizes):
            matching = MatchConfig.model_validate(self.match.model_dump() | {"block_size": block})
            estimate = estimate_complexity(
                shape, ComplexityConfig(embedding=self.embedding, match=matching)
            )
            if not estimate.feasible or estimate.input_elements > self.max_input_elements:
                raise ParameterError("benchmark", "Request exceeds declared resource limits")
        return self


class BenchmarkRecord(BaseModel):
    """Observed timings and an allocation-free estimate for the exact same request."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", allow_inf_nan=False
    )
    shape: tuple[StrictInt, ...]
    block_size: StrictInt
    input_file: str
    input_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    estimate: ComplexityEstimate
    result: EntropyResult
    seconds: tuple[float, ...] = Field(min_length=2)
    median_seconds: float = Field(gt=0)
    sample_sd_seconds: float = Field(ge=0)


class BenchmarkReport(BaseModel):
    """Environment-specific empirical times, not portable runtime promises or FLOPs."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal[1] = 1
    plan: BenchmarkPlan
    plan_sha256: str
    python: str
    numpy: str
    platform: str
    machine: str
    records: tuple[BenchmarkRecord, ...] = Field(min_length=1)
