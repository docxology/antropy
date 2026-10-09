#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd", "matplotlib>=3.10", "pyyaml>=6", "typer>=0.16"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# How to run: uv run python scripts/run_study.py --plan study_plan.yaml
# Copyright (c) 2026 Daniel Ari Friedman
"""Execute a complete bounded replicated design, preserving all outcomes."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Annotated, Final

import numpy as np
import typer
import yaml

from antropy_hd.orchestration import canonical_json, run_batch

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.artifact_io import digest
from scripts.study_analysis import preflight_study, record_rows, study_batches, summarize
from scripts.study_diagnostics import plot_diagnostics
from scripts.study_fields import study_cases, study_field, symbol_probabilities
from scripts.study_models import StudyPlan, StudyRecord, StudyReport
from scripts.study_plots import plot_study


def execute_study(root: Path, plan_path: Path) -> StudyReport:
    """Generate stored native arrays and exactly three explicitly transformed batches."""
    plan = StudyPlan.model_validate(yaml.safe_load(plan_path.read_text(encoding="utf-8")))
    complexity = preflight_study(plan)
    output = root / "output/study"
    (output / "fields").mkdir(parents=True, exist_ok=True)
    _ = (output / "complexity.json").write_text(
        canonical_json(
            {
                "schema_version": 1,
                "plan_sha256": digest(plan_path),
                "records": [record.model_dump(mode="json") for record in complexity],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    configs = study_batches(plan)
    records: list[StudyRecord] = []
    for case in study_cases(plan):
        array = study_field(plan, case)
        path = output / "fields" / f"{case.id}.npy"
        np.save(path, array, allow_pickle=False)
        records.append(
            StudyRecord(
                case=case,
                input_file=path.relative_to(root).as_posix(),
                input_sha256=digest(path),
                native=run_batch(array, configs[0]),
                flattened=run_batch(array.ravel(order="C"), configs[1]),
                symbols=run_batch(symbol_probabilities(array, plan), configs[2]),
            )
        )
    report = StudyReport(plan=plan, plan_sha256=digest(plan_path), records=tuple(records))
    _ = (output / "report.json").write_text(
        canonical_json(report.model_dump(mode="json")) + "\n", encoding="utf-8"
    )
    rows = [row for record in report.records for row in record_rows(record)]
    with (output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].model_dump()))
        writer.writeheader()
        writer.writerows(row.model_dump(mode="json") for row in rows)
    summary = summarize(rows)
    _ = (output / "summary.json").write_text(
        canonical_json([item.model_dump(mode="json") for item in summary]) + "\n", encoding="utf-8"
    )
    plot_study(rows, summary, output / "figures")
    plot_diagnostics(report, root)
    return report


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_PLAN: Final[Path] = Path("study_plan.yaml")


def main(
    plan: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_PLAN,
    root: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_ROOT,
) -> None:
    """Run every declared trial, geometry, method and radius without censoring failures."""
    report = execute_study(root.resolve(), plan.resolve())
    print(f"Generated {len(report.records)} fields; all trial outcomes retained")


if __name__ == "__main__":
    typer.run(main)
