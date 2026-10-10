# Copyright (c) 2026 Daniel Ari Friedman
"""Independent replay gate for prospective operating-characteristic artifacts."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Never

import yaml
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import canonical_json
from scripts.artifact_io import bounded_path, digest
from scripts.power_models import PowerReport
from scripts.power_plan import PowerPlan
from scripts.power_preflight import preflight_power
from scripts.power_serialization import PowerCSV, decision_csv, summary_csv
from scripts.power_validation_fields import validate_fields
from scripts.power_validation_inference import validate_decisions, validate_summaries


def _unique_pairs(pairs: list[tuple[str, JsonValue]]) -> JsonValue:
    """Reject duplicated JSON keys before any typed model can discard evidence."""
    result: dict[str, JsonValue] = {}
    for key, value in pairs:
        if key in result:
            raise ParameterError("power", "Power report contains duplicate JSON keys")
        result[key] = value
    return result


def _finite_number(raw: str) -> float:
    """Reject numeric overflow such as 1e999 as well as explicit JSON constants."""
    value = float(raw)
    if not math.isfinite(value):
        raise ParameterError("power", "Power report contains nonfinite JSON numbers")
    return value


def _reject_constant(raw: str) -> Never:
    """JSON has no NaN or infinity literals."""
    raise ParameterError("power", f"Power report contains invalid JSON constant {raw}")


def _strict_json(raw: bytes) -> None:
    """Check duplicate and nonfinite evidence, releasing the scratch tree before model parsing."""
    _ = json.loads(
        raw,
        object_pairs_hook=_unique_pairs,
        parse_float=_finite_number,
        parse_constant=_reject_constant,
    )


def _csv_matches(path: Path, expected: PowerCSV) -> None:
    """Require exact ordered canonical values; duplicate columns and rows cannot disappear."""
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream, strict=True)
        header = tuple(next(reader, ()))
        if header != expected.headers:
            raise ParameterError("power", "Power CSV header differs from its complete schema")
        actual = tuple(tuple(row) for row in reader)
    if actual != expected.rows:
        raise ParameterError("power", "Power CSV rows differ from complete canonical records")


def _figures(root: Path) -> None:
    """Require each physical plot and its vector counterpart; publication binds their full bytes."""
    for name in ("rejection-rates", "availability-calibration"):
        for suffix, signature in (("png", b"\x89PNG\r\n\x1a\n"), ("pdf", b"%PDF-")):
            path = bounded_path(root, f"output/power/figures/{name}.{suffix}")
            with path.open("rb") as stream:
                if stream.read(len(signature)) != signature:
                    raise ParameterError(
                        "power", "Power figure file has an invalid format signature"
                    )


def validate_power(root: Path) -> PowerReport:
    """Bind live plan bytes, the full design, real tensors, kernels, tests and all projections."""
    plan_path = bounded_path(root, "power_plan.yaml")
    plan = PowerPlan.model_validate(yaml.safe_load(plan_path.read_text(encoding="utf-8")))
    resources = preflight_power(plan)
    report_path = bounded_path(root, "output/power/report.json")
    if report_path.stat().st_size > plan.max_report_bytes:
        raise ParameterError("max_report_bytes", "Power report exceeds its declared byte budget")
    raw = report_path.read_bytes()
    _strict_json(raw)
    report = PowerReport.model_validate_json(raw, strict=True)
    if report.plan != plan or report.plan_sha256 != digest(plan_path):
        raise ParameterError("power", "Power plan and consumed byte snapshot differ")
    if canonical_json(report.resources.model_dump(mode="json")) != canonical_json(
        resources.model_dump(mode="json")
    ):
        raise ParameterError(
            "power", "Power resource preflight differs from actual configured requests"
        )
    fields = validate_fields(root, report)
    validate_decisions(report, fields)
    validate_summaries(report)
    _csv_matches(bounded_path(root, "output/power/decisions.csv"), decision_csv(report.experiments))
    _csv_matches(bounded_path(root, "output/power/summary.csv"), summary_csv(report.summaries))
    _figures(root)
    return report
