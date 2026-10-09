# Copyright (c) 2026 Daniel Ari Friedman
"""Strict research artifact boundary models shared by validators."""

from __future__ import annotations

from typing import ClassVar, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

from antropy_hd.orchestration import BatchResult
from scripts.run_experiments import ExperimentPlan


class Artifact(BaseModel):
    """One nonempty file whose actual bytes are authenticated."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    path: str
    kind: Literal["input", "output"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(gt=0)


class Manifest(BaseModel):
    """Versioned artifact inventory with a required completeness floor."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    required_artifacts: tuple[str, ...]
    artifacts: tuple[Artifact, ...] = Field(min_length=1)


class ExperimentBatch(BaseModel):
    """Input byte identity and the independently validated numerical batch."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    field_id: str
    input_file: str
    input_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    batch: BatchResult


class Experiments(BaseModel):
    """Nonempty experiment result record."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    batches: tuple[ExperimentBatch, ...] = Field(min_length=1)


class ExperimentSnapshot(BaseModel):
    """Consumed plan and the exact bytes of its YAML source."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    plan: ExperimentPlan
    plan_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Claim(BaseModel):
    """A bounded method, configuration or measured claim with explicit sources."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    id: str
    kind: Literal["method", "configuration", "measured"]
    sources: tuple[str, ...] = Field(min_length=1)


class ClaimLedger(BaseModel):
    """Bind manuscript numerical claims to the current result table."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    results_csv_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    claims: tuple[Claim, ...] = Field(min_length=1)


class ArtifactReport(TypedDict):
    """Counts from a completed on-disk validation."""

    authenticated_files: int
    result_rows: int
    pdf_pages: int
