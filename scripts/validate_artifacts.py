#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd", "matplotlib>=3.10", "pyyaml>=6", "pypdf>=5", "typer>=0.16"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# How to run: install uv at https://docs.astral.sh/uv/getting-started/installation/
# Frozen project environment: uv run python scripts/validate_artifacts.py [OPTIONS]
# Standalone: uv run scripts/validate_artifacts.py [OPTIONS]
# Executable: chmod +x scripts/validate_artifacts.py && ./scripts/validate_artifacts.py [OPTIONS]
# Copyright (c) 2026 Daniel Ari Friedman
"""Fail-closed validation of actual artifacts, provenance and manuscript bindings."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Annotated, Final, assert_never

import numpy as np
import typer
import yaml
from pydantic import JsonValue
from pypdf import PdfReader

from antropy_hd.errors import ParameterError
from antropy_hd.models import EntropyResult
from antropy_hd.orchestration import AnalysisResult, BatchConfig, array_sha256, canonical_json
from antropy_hd.validation import as_real_array

if __package__ in (None, ""):
    # Source-tree execution imports the same plan schema as module/test execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.artifact_io import bounded_path, digest, read_json
from scripts.artifact_models import (
    ArtifactReport,
    ClaimLedger,
    ExperimentBatch,
    Experiments,
    ExperimentSnapshot,
    Manifest,
)
from scripts.run_experiments import ExperimentPlan, Structure, analyses_for, synthesize

REQUIRED_ARTIFACTS: Final[frozenset[str]] = frozenset(
    {
        "output/data/results.csv",
        "output/reports/experiments.json",
        "output/figures/hdse-tolerance.png",
        "output/provenance/experiment-config.json",
        "docs/manuscript/manuscript.md",
        "output/pdf/antropy-methods.pdf",
        "docs/manuscript/claims.json",
    }
)


type FieldDesign = dict[str, tuple[tuple[int, ...], Structure]]
type ResultIndex = dict[tuple[str, str], tuple[ExperimentBatch, EntropyResult]]


def validated_design(root: Path, experiments: Experiments) -> FieldDesign:
    """Require the complete matrix derived independently from the live plan."""
    plan_path = root / "experiment_plan.yaml"
    plan = ExperimentPlan.model_validate(yaml.safe_load(plan_path.read_text(encoding="utf-8")))
    snapshot = ExperimentSnapshot.model_validate(
        read_json(root / "output/provenance/experiment-config.json")
    )
    if snapshot.plan != plan or snapshot.plan_sha256 != digest(plan_path):
        raise ParameterError("plan", "Experiment plan snapshot/seed/source hash is inconsistent")
    design = {
        f"{structure}-{'x'.join(map(str, shape))}": (shape, structure)
        for shape in plan.shapes
        for structure in plan.structures
    }
    fields = [record.field_id for record in experiments.batches]
    if len(fields) != len(set(fields)) or set(fields) != set(design):
        raise ParameterError("coverage", "Experiment field matrix is incomplete or duplicated")
    expected_config = BatchConfig(analyses=analyses_for(plan))
    for record in experiments.batches:
        shape, structure = design[record.field_id]
        expected_file = f"output/data/{record.field_id}.npy"
        if record.input_file != expected_file or record.batch.config != expected_config:
            raise ParameterError(
                "coverage", "Experiment method/tolerance/parameter matrix differs from the plan"
            )
        array = as_real_array(np.load(bounded_path(root, record.input_file), allow_pickle=False))
        if array.shape != shape or array_sha256(array) != array_sha256(
            synthesize(plan, shape, structure)
        ):
            raise ParameterError("seed", "Generated input differs from the declared seeded design")
    return design


def expected_results(root: Path, manifest_paths: set[str], experiments: Experiments) -> ResultIndex:
    """Authenticate input arrays, batch configurations and exact analysis coverage."""
    expected: ResultIndex = {}
    for record in experiments.batches:
        if record.input_file not in manifest_paths:
            raise ParameterError("artifacts", f"Unmanifested experiment input: {record.input_file}")
        path = bounded_path(root, record.input_file)
        if digest(path) != record.input_file_sha256:
            raise ParameterError(
                "artifacts", f"Experiment input hash mismatch: {record.input_file}"
            )
        array = as_real_array(np.load(path, allow_pickle=False))
        if (
            array_sha256(array) != record.batch.input_sha256
            or array.shape != record.batch.input_shape
        ):
            raise ParameterError("artifacts", "Batch input array identity is inconsistent")
        config_hash = hashlib.sha256(
            canonical_json(record.batch.config.model_dump(mode="json")).encode()
        ).hexdigest()
        if config_hash != record.batch.config_sha256:
            raise ParameterError("artifacts", "Batch configuration hash mismatch")
        ids = {spec.id for spec in record.batch.config.analyses}
        if ids != set(record.batch.results):
            raise ParameterError(
                "artifacts", "Batch results do not cover exactly the configured analyses"
            )
        for spec in record.batch.config.analyses:
            key = (record.field_id, spec.id)
            if key in expected:
                raise ParameterError("artifacts", "Duplicate experiment field/analysis identity")
            result = record.batch.results[spec.id]
            expected[key] = (record, scalar_result(result))
    return expected


def scalar_result(result: AnalysisResult) -> EntropyResult:
    """Require a scalar estimate at the experiment-table boundary."""
    match result:
        case EntropyResult():
            return result
        case tuple():
            raise ParameterError(
                "results", "Scalar experiment table cannot contain multiscale tuples"
            )
        case unreachable:
            assert_never(unreachable)


type CsvRow = dict[str, str]


def validate_csv_row(row: CsvRow, record: ExperimentBatch, result: EntropyResult) -> None:
    """Require matching interpretation, geometry, details, status and estimate."""
    spec = next(spec for spec in record.batch.config.analyses if spec.id == row["analysis_id"])
    if row["structure"] != record.field_id.rsplit("-", 1)[0]:
        raise ParameterError("results", "CSV structure differs from the declared field")
    validate_radius(row, spec.parameters.get("match"))
    if row["status"] != result.status or row["measure"] != spec.measure:
        raise ParameterError("artifacts", "CSV status or measure differs from JSON")
    if (
        row["input_sha256"] != record.batch.input_sha256
        or row["config_sha256"] != record.batch.config_sha256
    ):
        raise ParameterError("artifacts", "CSV provenance differs from JSON")
    if (
        row["ndim"] != str(len(record.batch.input_shape))
        or row["shape"] != "x".join(map(str, record.batch.input_shape))
        or row["n_observations"] != str(result.n_observations)
    ):
        raise ParameterError("artifacts", "CSV geometry or observation count differs from JSON")
    if canonical_json(json.loads(row["parameters_json"])) != canonical_json(
        result.parameters
    ) or canonical_json(json.loads(row["diagnostics_json"])) != canonical_json(result.diagnostics):
        raise ParameterError("artifacts", "CSV estimator details differ from JSON")
    if result.value is None:
        if row["value"] != "":
            raise ParameterError("artifacts", "Nonfinite status must retain an empty CSV value")
    elif not math.isfinite(float(row["value"])) or float(row["value"]) != result.value:
        raise ParameterError("artifacts", "CSV estimate differs from JSON")


def validate_radius(row: CsvRow, matching: JsonValue) -> None:
    """Require CSV tolerance to agree with the declared matching configuration."""
    match matching:
        case dict() as matching:
            radius = matching["tolerance"]
            if row["tolerance"] != str(radius):
                raise ParameterError("results", "CSV tolerance differs from the configured radius")
        case None:
            if row["tolerance"]:
                raise ParameterError("results", "Unconfigured CSV tolerance must be empty")
        case str() | float() | int() | list() | bool() as unexpected:
            raise ParameterError("results", f"Invalid experiment match configuration: {unexpected}")
        case unreachable:
            assert_never(unreachable)


def validate_results(root: Path, manifest_paths: set[str]) -> int:
    """Cross-check every CSV row against authenticated strict JSON results."""
    experiments = Experiments.model_validate(read_json(root / "output/reports/experiments.json"))
    _ = validated_design(root, experiments)
    expected = expected_results(root, manifest_paths, experiments)
    with (root / "output/data/results.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != len(expected) or not rows:
        raise ParameterError("artifacts", "CSV row coverage differs from JSON analyses")
    seen = set()
    for row in rows:
        key = (row["field_id"], row["analysis_id"])
        if key in seen or key not in expected:
            raise ParameterError("artifacts", "Duplicate or unknown CSV result identity")
        seen.add(key)
        record, result = expected[key]
        validate_csv_row(row, record, result)
    return len(rows)


def validate_claims(root: Path, csv_hash: str, paths: list[str]) -> None:
    """Require complete claim identities and authenticated source bindings."""
    ledger = ClaimLedger.model_validate(read_json(root / "docs/manuscript/claims.json"))
    if ledger.results_csv_sha256 != csv_hash or {claim.id for claim in ledger.claims} != {
        "hdse-contract",
        "related-contracts",
        "synthetic-estimates",
        "synthetic-design",
    }:
        raise ParameterError(
            "claims", "Claim ledger is not bound to the current results or complete"
        )
    for claim in ledger.claims:
        if not set(claim.sources) <= set(paths):
            raise ParameterError("claims", "Claim source is missing from authenticated provenance")


def validate(root: Path, manifest_path: Path | None = None) -> ArtifactReport:
    """Require complete authenticated artifacts and meaningful manuscript bindings."""
    root = root.resolve()
    path = manifest_path or root / "output/provenance/manifest.json"
    manifest = Manifest.model_validate(read_json(path))
    required = set(manifest.required_artifacts)
    if not required >= REQUIRED_ARTIFACTS:
        raise ParameterError("artifacts", "Manifest omits the required artifact completeness floor")
    paths = [artifact.path for artifact in manifest.artifacts]
    if len(set(paths)) != len(paths) or not required <= set(paths):
        raise ParameterError(
            "artifacts", "Manifest contains duplicate paths or missing required records"
        )
    for artifact in manifest.artifacts:
        artifact_path = bounded_path(root, artifact.path)
        if (
            artifact_path.stat().st_size != artifact.bytes
            or digest(artifact_path) != artifact.sha256
        ):
            raise ParameterError("artifacts", f"Artifact byte/hash mismatch: {artifact.path}")
    rows = validate_results(root, set(paths))
    manuscript = (root / "docs/manuscript/manuscript.md").read_text(encoding="utf-8")
    csv_hash = digest(root / "output/data/results.csv")
    validate_claims(root, csv_hash, paths)
    if (
        f"Results CSV SHA-256: {csv_hash}" not in manuscript
        or "../../output/figures/hdse-tolerance.png" not in manuscript
    ):
        raise ParameterError(
            "artifacts", "Manuscript is not bound to the authenticated results and figure"
        )
    image = (root / "output/figures/hdse-tolerance.png").read_bytes()
    if (
        image[:8] != b"\x89PNG\r\n\x1a\n"
        or int.from_bytes(image[16:20]) < 300
        or int.from_bytes(image[20:24]) < 200
    ):
        raise ParameterError("artifacts", "Figure is not a legible PNG artifact")
    reader = PdfReader(root / "output/pdf/antropy-methods.pdf")
    text = "\n".join(page.extract_text() for page in reader.pages)
    if (
        not reader.pages
        or "Computational results" not in text
        or csv_hash not in text.replace("\n", "")
    ):
        raise ParameterError("artifacts", "PDF lacks the required result and provenance text")
    return {"authenticated_files": len(paths), "result_rows": rows, "pdf_pages": len(reader.pages)}


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def main(root: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_ROOT) -> None:
    """Validate from disk; any missing, corrupt or incomplete artifact is fatal."""
    print(json.dumps(validate(root), sort_keys=True))


if __name__ == "__main__":
    typer.run(main)
