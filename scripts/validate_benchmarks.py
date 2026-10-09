# Copyright (c) 2026 Daniel Ari Friedman
"""Authenticate measured kernel receipts without treating timings as predictions."""

from __future__ import annotations

import itertools
import statistics
from pathlib import Path

import numpy as np
import yaml

from antropy_hd.complexity import ComplexityConfig, estimate_complexity
from antropy_hd.errors import ParameterError
from antropy_hd.models import MatchConfig
from antropy_hd.orchestration import array_sha256, canonical_json
from antropy_hd.template_entropy import hdse
from antropy_hd.validation import as_real_array
from scripts.artifact_io import bounded_path, digest, replay_equivalent
from scripts.benchmark_models import BenchmarkPlan, BenchmarkReport
from scripts.result_replay import result_equivalent


def validate_benchmarks(root: Path) -> int:
    """Require all declared shape/block measurements, exact plans and real numerical replay."""
    plan_path = root / "benchmark_plan.yaml"
    report = BenchmarkReport.model_validate_json((root / "output/study/benchmark.json").read_text())
    plan = BenchmarkPlan.model_validate(yaml.safe_load(plan_path.read_text()))
    if report.plan != plan or report.plan_sha256 != digest(plan_path):
        raise ParameterError("benchmark", "Consumed benchmark plan differs")
    expected = set(itertools.product(plan.shapes, plan.block_sizes))
    actual = [(record.shape, record.block_size) for record in report.records]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ParameterError("benchmark", "Measurement design is incomplete or duplicated")
    for record in report.records:
        expected_file = "output/study/benchmark-fields/" + "x".join(map(str, record.shape)) + ".npy"
        if record.input_file != expected_file:
            raise ParameterError("benchmark", "Input path differs from the declared shape")
        path = bounded_path(root, record.input_file)
        array = as_real_array(np.load(path, allow_pickle=False))
        reference = np.random.default_rng(
            np.random.SeedSequence([plan.seed, *record.shape])
        ).normal(size=record.shape)
        if (
            digest(path) != record.input_file_sha256
            or array_sha256(array) != record.input_sha256
            or not replay_equivalent(array, reference)
        ):
            raise ParameterError("benchmark", "Measured input identity or seeded replay differs")
        matching = MatchConfig.model_validate(
            plan.match.model_dump() | {"block_size": record.block_size}
        )
        estimate = estimate_complexity(
            record.shape, ComplexityConfig(embedding=plan.embedding, match=matching)
        )
        if canonical_json(estimate.model_dump(mode="json")) != canonical_json(
            record.estimate.model_dump(mode="json")
        ):
            raise ParameterError(
                "benchmark", "Work or memory estimates differ from the actual request"
            )
        if len(record.seconds) != plan.repetitions or min(record.seconds) <= 0:
            raise ParameterError("benchmark", "Timing repetitions differ or are not positive")
        if record.median_seconds != statistics.median(
            record.seconds
        ) or record.sample_sd_seconds != statistics.stdev(record.seconds):
            raise ParameterError("benchmark", "Timing summaries differ from recorded repetitions")
        result = hdse(array, embedding=plan.embedding, match=matching)
        if not result_equivalent(record.result, result):
            raise ParameterError("benchmark", "Measured kernel result fails numerical replay")
    return len(actual)
