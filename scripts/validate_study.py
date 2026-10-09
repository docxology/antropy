# Copyright (c) 2026 Daniel Ari Friedman
"""Authenticate complete replicated designs without weakening exact byte custody."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import array_sha256, canonical_json, run_batch
from scripts.artifact_io import bounded_path, digest, replay_equivalent
from scripts.result_replay import result_equivalent, scalar_result
from scripts.study_analysis import preflight_study, record_rows, study_batches, summarize
from scripts.study_fields import study_cases, study_field, symbol_probabilities
from scripts.study_models import StudyPlan, StudyRecord, StudyReport


def validate_fields(root: Path, report: StudyReport) -> None:
    """Authenticate the native field and every explicitly transformed input batch."""
    plan = report.plan
    expected_cases = {case.id: case for case in study_cases(plan)}
    configs = study_batches(plan)
    for record in report.records:
        case = expected_cases[record.case.id]
        if record.case != case or record.input_file != f"output/study/fields/{case.id}.npy":
            raise ParameterError("study", "Field identity differs from the declared design")
        path = bounded_path(root, record.input_file)
        if digest(path) != record.input_sha256:
            raise ParameterError("study", "Stored field file hash differs")
        array = np.load(path, allow_pickle=False)
        if not replay_equivalent(array, study_field(plan, case)):
            raise ParameterError("study", "Stored field fails seeded design replay")
        inputs = (array, array.ravel(order="C"), symbol_probabilities(array, plan))
        batches = (record.native, record.flattened, record.symbols)
        for data, batch, config in zip(inputs, batches, configs, strict=True):
            if (
                batch.config != config
                or batch.input_shape != data.shape
                or batch.input_sha256 != array_sha256(data)
            ):
                raise ParameterError("study", "Transformed input or consumed configuration differs")
            expected_hash = hashlib.sha256(
                canonical_json(config.model_dump(mode="json")).encode()
            ).hexdigest()
            if batch.config_sha256 != expected_hash or set(batch.results) != {
                spec.id for spec in config.analyses
            }:
                raise ParameterError("study", "Configured analysis coverage or hash differs")
            replayed = run_batch(data, config)
            for analysis_id, stored in batch.results.items():
                actual = replayed.results[analysis_id]
                if not result_equivalent(scalar_result(stored), scalar_result(actual)):
                    raise ParameterError(
                        "study", "Stored estimates or diagnostic counts fail numerical replay"
                    )


def validate_tables(root: Path, records: tuple[StudyRecord, ...]) -> int:
    """Require complete exact result rows and uncensored finite-conditional aggregates."""
    rows = [row for record in records for row in record_rows(record)]
    expected_rows = {
        (row.case_id, row.geometry, row.analysis_id): {
            key: "" if value is None else str(value)
            for key, value in row.model_dump(mode="json").items()
        }
        for row in rows
    }
    with (root / "output/study/results.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or ()
        if len(headers) != len(set(headers)) or set(headers) != set(rows[0].model_dump()):
            raise ParameterError("study", "CSV header differs from the scalar study schema")
        actual_rows = list(reader)
    seen: set[tuple[str, str, str]] = set()
    for row in actual_rows:
        key = (row["case_id"], row["geometry"], row["analysis_id"])
        if key in seen or key not in expected_rows or row != expected_rows[key]:
            raise ParameterError("study", "CSV contains unknown, duplicate or inconsistent results")
        seen.add(key)
    if seen != set(expected_rows):
        raise ParameterError("study", "CSV drops declared study results")
    actual_summary = json.loads((root / "output/study/summary.json").read_text())
    expected_summary: list[JsonValue] = [item.model_dump(mode="json") for item in summarize(rows)]
    if canonical_json(actual_summary) != canonical_json(expected_summary):
        raise ParameterError("study", "Aggregates do not preserve all trial outcomes")
    return len(rows)


def validate_study(root: Path) -> int:
    """Require every configured field, transformed batch, result and aggregate."""
    report = StudyReport.model_validate_json((root / "output/study/report.json").read_text())
    plan_path = root / "study_plan.yaml"
    plan = StudyPlan.model_validate(yaml.safe_load(plan_path.read_text(encoding="utf-8")))
    if report.plan != plan or report.plan_sha256 != digest(plan_path):
        raise ParameterError("study", "Study plan and consumed snapshot differ")
    expected = {case.id for case in study_cases(plan)}
    actual = [record.case.id for record in report.records]
    if len(set(actual)) != len(actual) or set(actual) != expected:
        raise ParameterError("study", "Trial design matrix is incomplete or duplicated")
    validate_fields(root, report)
    complexity = json.loads((root / "output/study/complexity.json").read_text())
    expected_complexity: dict[str, JsonValue] = {
        "schema_version": 1,
        "plan_sha256": digest(plan_path),
        "records": [item.model_dump(mode="json") for item in preflight_study(plan)],
    }
    if canonical_json(complexity) != canonical_json(expected_complexity):
        raise ParameterError("study", "Computational plans differ from configured actual requests")
    return validate_tables(root, report.records)
