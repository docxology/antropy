#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd", "matplotlib>=3.10", "pyyaml>=6", "typer>=0.16"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# Copyright (c) 2026 Daniel Ari Friedman
"""Thin prospective power orchestration: preflight, retain fields, compare, summarize, plot."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final

import typer
import yaml

from antropy_hd.errors import ResourceError
from antropy_hd.orchestration import canonical_json

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.artifact_io import digest
from scripts.power_analysis import ExperimentIdentity, experiment_decisions
from scripts.power_models import FieldEstimate, PowerDecision, PowerPool, PowerReport
from scripts.power_plan import PowerPlan
from scripts.power_plots import plot_power
from scripts.power_preflight import preflight_power
from scripts.power_serialization import decision_csv, summary_csv
from scripts.power_storage import retain_pool
from scripts.power_summary import summarize_power


def run_power(root: Path, plan_path: Path) -> PowerReport:
    """Execute every prespecified comparison; preserve nonfinite fields and missing tests."""
    plan = PowerPlan.model_validate(yaml.safe_load(plan_path.read_text(encoding="utf-8")))
    resources = preflight_power(plan)
    pools: list[PowerPool] = []
    estimates: list[FieldEstimate] = []
    decisions: list[PowerDecision] = []
    for scenario in plan.scenarios:
        for shape in plan.shapes:
            for replicate in range(plan.repetitions):
                first = retain_pool(root, plan, scenario, shape, replicate, "first")
                second = retain_pool(root, plan, scenario, shape, replicate, "second")
                pools.extend((first.record, second.record))
                estimates.extend((*first.estimates, *second.estimates))
                identity = ExperimentIdentity(scenario, shape, replicate)
                for n in plan.sample_sizes:
                    decisions.extend(
                        experiment_decisions(plan, identity, n, first.estimates, second.estimates)
                    )
    report = PowerReport(
        plan=plan,
        plan_sha256=digest(plan_path),
        resources=resources,
        pools=tuple(pools),
        estimates=tuple(estimates),
        experiments=tuple(decisions),
        summaries=summarize_power(plan, tuple(decisions)),
    )
    data = (canonical_json(report.model_dump(mode="json")) + "\n").encode("utf-8")
    if len(data) > plan.max_report_bytes:
        raise ResourceError("max_report_bytes", "Retained report exceeds its declared byte budget")
    output = root / "output/power"
    _ = (output / "report.json").write_bytes(data)
    _ = (output / "summary.csv").write_text(summary_csv(report.summaries).text(), encoding="utf-8")
    _ = (output / "decisions.csv").write_text(
        decision_csv(report.experiments).text(), encoding="utf-8"
    )
    plot_power(report, output / "figures")
    return report


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_PLAN: Final[Path] = Path("power_plan.yaml")


def main(
    plan: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_PLAN,
    root: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_ROOT,
) -> None:
    """Produce a complete power artifact set using the declared design and budgets."""
    report = run_power(root.resolve(), plan.resolve())
    print(f"Retained {len(report.estimates)} fields and {len(report.experiments)} decisions")


if __name__ == "__main__":
    typer.run(main)
