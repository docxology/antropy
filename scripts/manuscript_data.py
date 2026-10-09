# Copyright (c) 2026 Daniel Ari Friedman
"""Typed reads of measured publication inputs; no scientific outputs are recomputed."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from antropy_hd.errors import ParameterError
from scripts.benchmark_models import BenchmarkReport
from scripts.manuscript_profile import ManuscriptContext
from scripts.study_models import StudyComplexityRecord, StudyReport, StudyRow, StudySummary


class BaselineRow(BaseModel):
    """One complete legacy baseline CSV record."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    field_id: str
    ndim: int
    shape: str
    structure: str
    analysis_id: str
    measure: str
    tolerance: float | None
    value: float | None
    status: Literal["finite", "undefined", "infinite"]
    n_observations: int
    input_sha256: str
    config_sha256: str
    parameters_json: str
    diagnostics_json: str


class ComplexityReport(BaseModel):
    """Analytical work estimates emitted by the study producer."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    plan_sha256: str
    records: tuple[StudyComplexityRecord, ...] = Field(min_length=1)


class PublicationData(BaseModel):
    """Producer-authored records consumed by manuscript variables."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    baseline: tuple[BaselineRow, ...]
    study: StudyReport | None
    study_rows: tuple[StudyRow, ...]
    summaries: tuple[StudySummary, ...]
    complexity: ComplexityReport | None
    benchmark: BenchmarkReport | None


def file_sha256(path: Path) -> str:
    """Read and authenticate actual source bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_source(path: Path, *, required: bool) -> JsonValue:
    """Read a declared JSON source, rejecting nonfinite values and missing required inputs."""
    if not path.is_file():
        if required:
            raise ParameterError("manuscript", f"Required producer output missing: {path.name}")
        return None
    value = TypeAdapter(JsonValue).validate_json(path.read_text(encoding="utf-8"))
    _ = json.dumps(value, allow_nan=False)
    if value is None and required:
        raise ParameterError("manuscript", "Required producer output cannot be null")
    return value


def read_data(root: Path, context: ManuscriptContext) -> PublicationData:
    """Parse measured CSVs and reports without inventing missing results."""
    with (root / "output/data/results.csv").open(newline="", encoding="utf-8") as stream:
        baseline = tuple(
            BaselineRow.model_validate(
                {
                    **row,
                    "value": row["value"] or None,
                    "tolerance": row["tolerance"] or None,
                }
            )
            for row in csv.DictReader(stream)
        )
    if not baseline:
        raise ParameterError("manuscript", "Baseline measurements must be nonempty")
    profile = context.profile
    report_path = root / "output/study/report.json"
    study_payload = json_source(report_path, required=profile.study_required)
    study = None if study_payload is None else StudyReport.model_validate(study_payload)
    rows: tuple[StudyRow, ...] = ()
    summaries: tuple[StudySummary, ...] = ()
    if study is not None:
        with (root / "output/study/results.csv").open(newline="", encoding="utf-8") as stream:
            rows = tuple(
                StudyRow.model_validate(
                    {
                        **row,
                        "value": row["value"] or None,
                        "radius": row["radius"] or None,
                        "mixing": row["mixing"] or None,
                        "dimension": int(row["dimension"]),
                        "trial": int(row["trial"]),
                        "observations": int(row["observations"]),
                    }
                )
                for row in csv.DictReader(stream)
            )
        summaries = TypeAdapter(tuple[StudySummary, ...]).validate_json(
            (root / "output/study/summary.json").read_text(encoding="utf-8")
        )
        if not rows or not summaries:
            raise ParameterError(
                "manuscript", "Replicated measurements and summaries must be nonempty"
            )
    complexity = json_source(
        root / "output/study/complexity.json", required=profile.complexity_required
    )
    benchmark = json_source(
        root / "output/study/benchmark.json", required=profile.benchmark_required
    )
    return PublicationData(
        baseline=baseline,
        study=study,
        study_rows=rows,
        summaries=summaries,
        complexity=None if complexity is None else ComplexityReport.model_validate(complexity),
        benchmark=None if benchmark is None else BenchmarkReport.model_validate(benchmark),
    )
