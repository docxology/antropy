#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd", "matplotlib>=3.10", "pyyaml>=6", "typer>=0.16"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# How to run: uv run python scripts/benchmark_complexity.py --plan benchmark_plan.yaml
# Copyright (c) 2026 Daniel Ari Friedman
"""Measure real HDSE kernels and distinguish work counts from platform timings."""

from __future__ import annotations

import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Annotated, Final

import numpy as np
import typer
import yaml

from antropy_hd.complexity import ComplexityConfig, estimate_complexity
from antropy_hd.errors import ParameterError
from antropy_hd.models import EntropyResult, MatchConfig
from antropy_hd.orchestration import array_sha256, canonical_json
from antropy_hd.template_entropy import hdse

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.artifact_io import digest
from scripts.benchmark_models import BenchmarkPlan, BenchmarkRecord, BenchmarkReport
from scripts.benchmark_plots import plot_benchmark


def benchmark(root: Path, plan_path: Path) -> BenchmarkReport:
    """Time real calls with a monotonic clock and preserve every repetition."""
    plan = BenchmarkPlan.model_validate(yaml.safe_load(plan_path.read_text()))
    records: list[BenchmarkRecord] = []
    fields = root / "output/study/benchmark-fields"
    fields.mkdir(parents=True, exist_ok=True)
    for shape in sorted(plan.shapes):
        array = np.random.default_rng(np.random.SeedSequence([plan.seed, *shape])).normal(
            size=shape
        )
        field = fields / ("x".join(map(str, shape)) + ".npy")
        np.save(field, array, allow_pickle=False)
        previous: EntropyResult | None = None
        for block in sorted(plan.block_sizes):
            match = MatchConfig.model_validate(plan.match.model_dump() | {"block_size": block})
            estimate = estimate_complexity(
                shape, ComplexityConfig(embedding=plan.embedding, match=match)
            )
            for _ in range(plan.warmups):
                _ = hdse(array, embedding=plan.embedding, match=match)
            calls: list[tuple[EntropyResult, float]] = []
            for _ in range(plan.repetitions):
                started = time.perf_counter_ns()
                result = hdse(array, embedding=plan.embedding, match=match)
                calls.append((result, (time.perf_counter_ns() - started) / 1e9))
            result = calls[-1][0]
            seconds = [seconds for _, seconds in calls]
            if result.diagnostics["eligible_pairs"] != estimate.stages[0].eligible_pairs:
                raise ParameterError("benchmark", "Observed pair count differs from planning")
            if previous is not None and (previous.value, previous.status, previous.diagnostics) != (
                result.value,
                result.status,
                result.diagnostics,
            ):
                raise ParameterError("benchmark", "Block size changed the numerical result")
            previous = result
            records.append(
                BenchmarkRecord(
                    shape=shape,
                    block_size=block,
                    input_sha256=array_sha256(array),
                    input_file=field.relative_to(root).as_posix(),
                    input_file_sha256=digest(field),
                    estimate=estimate,
                    result=result,
                    seconds=tuple(seconds),
                    median_seconds=statistics.median(seconds),
                    sample_sd_seconds=statistics.stdev(seconds),
                )
            )
    report = BenchmarkReport(
        plan=plan,
        plan_sha256=digest(plan_path),
        python=platform.python_version(),
        numpy=np.__version__,
        platform=platform.platform(),
        machine=platform.machine(),
        records=tuple(records),
    )
    path = root / "output/study/benchmark.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(canonical_json(report.model_dump(mode="json")) + "\n", encoding="utf-8")
    plot_benchmark(report, root / "output/study/figures/cost-scaling.png")
    return report


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_PLAN: Final[Path] = Path("benchmark_plan.yaml")


def main(
    plan: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = DEFAULT_PLAN,
    root: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_ROOT,
) -> None:
    """Measure configured kernels and record the complete machine-specific receipt."""
    report = benchmark(root.resolve(), plan.resolve())
    print(f"Measured {len(report.records)} shape/block requests; no time prediction assumed")


if __name__ == "__main__":
    typer.run(main)
