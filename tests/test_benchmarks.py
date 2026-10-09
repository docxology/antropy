# Copyright (c) 2026 Daniel Ari Friedman
"""Real benchmark receipts, replay checks and deliberate authenticated corruptions."""

import shutil
import statistics
from dataclasses import replace
from enum import StrEnum
from pathlib import Path
from typing import assert_never

import numpy as np
import pytest
import yaml
from pydantic import ValidationError

from antropy_hd.errors import ParameterError
from antropy_hd.models import EmbeddingConfig, MatchConfig
from antropy_hd.orchestration import array_sha256
from scripts.artifact_io import digest
from scripts.benchmark_complexity import benchmark
from scripts.benchmark_models import BenchmarkPlan, BenchmarkRecord, BenchmarkReport
from scripts.validate_benchmarks import validate_benchmarks


def small_plan() -> BenchmarkPlan:
    """Use two real shapes, two block schedules and two measured repetitions."""
    return BenchmarkPlan(
        seed=17,
        shapes=((8,), (5, 5)),
        block_sizes=(2, 4),
        repetitions=2,
        warmups=1,
        max_input_elements=1000,
        embedding=EmbeddingConfig(
            shape=1, max_templates=200, max_pairs=50000, max_memory_bytes=1048576
        ),
        match=MatchConfig(tolerance=2, block_size=4),
    )


@pytest.fixture(scope="module")
def benchmark_baseline(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run actual kernels, preserve timings/NPYs and validate the complete receipt."""
    root = tmp_path_factory.mktemp("benchmark-baseline")
    plan_path = root / "benchmark_plan.yaml"
    _ = plan_path.write_text(yaml.safe_dump(small_plan().model_dump(mode="json")), encoding="utf-8")
    _ = benchmark(root, plan_path)
    assert validate_benchmarks(root) == 4
    return root


@pytest.fixture
def benchmark_root(tmp_path: Path, benchmark_baseline: Path) -> Path:
    """Isolate every negative mutation in a real filesystem copy."""
    root = tmp_path / "benchmark"
    _ = shutil.copytree(benchmark_baseline, root)
    return root


def read_report(root: Path) -> BenchmarkReport:
    """Parse the actual stored receipt through its typed schema."""
    return BenchmarkReport.model_validate_json(
        (root / "output/study/benchmark.json").read_text(encoding="utf-8")
    )


def write_report(root: Path, report: BenchmarkReport) -> None:
    """Store one deliberate, valid-schema mutation without suppressing write failures."""
    _ = (root / "output/study/benchmark.json").write_text(
        report.model_dump_json() + "\n", encoding="utf-8"
    )


def test_benchmark_when_real_plan_executes_preserves_arrays_times_and_complete_design(
    benchmark_root: Path,
) -> None:
    # Given a complete real benchmark receipt and its declared shape/block sweep.
    report = read_report(benchmark_root)
    # When independent replay validation runs.
    count = validate_benchmarks(benchmark_root)
    # Then every declared measurement and real positive timing remains represented.
    assert count == 4
    assert {(record.shape, record.block_size) for record in report.records} == {
        (shape, block) for shape in report.plan.shapes for block in report.plan.block_sizes
    }
    for record in report.records:
        assert len(record.seconds) == report.plan.repetitions
        assert min(record.seconds) > 0
        assert record.median_seconds == statistics.median(record.seconds)
        assert record.sample_sd_seconds == statistics.stdev(record.seconds)
        path = benchmark_root / record.input_file
        array = np.load(path, allow_pickle=False)
        assert array.shape == record.shape
        assert digest(path) == record.input_file_sha256
        assert array_sha256(array) == record.input_sha256


class ReceiptFault(StrEnum):
    """Independent failure seams in measurement design, timing, identity and replay."""

    MISSING_CASE = "missing_case"
    DUPLICATE_CASE = "duplicate_case"
    MEDIAN = "median"
    SAMPLE_SD = "sample_sd"
    SAMPLE_COUNT = "sample_count"
    ZERO_TIME = "zero_time"
    ARRAY_HASH = "array_hash"
    FILE_HASH = "file_hash"
    INPUT_PATH = "input_path"
    WORK = "work"
    RESULT = "result"


def altered_record(record: BenchmarkRecord, fault: ReceiptFault) -> BenchmarkRecord:
    """Create a targeted corruption that remains parseable as a benchmark record."""
    changes = {
        ReceiptFault.MEDIAN: {"median_seconds": record.median_seconds * 2},
        ReceiptFault.SAMPLE_SD: {"sample_sd_seconds": record.sample_sd_seconds + 0.001},
        ReceiptFault.SAMPLE_COUNT: {"seconds": (*record.seconds, record.seconds[-1])},
        ReceiptFault.ZERO_TIME: {"seconds": (0.0, *record.seconds[1:])},
        ReceiptFault.ARRAY_HASH: {"input_sha256": "0" * 64},
        ReceiptFault.FILE_HASH: {"input_file_sha256": "0" * 64},
        ReceiptFault.INPUT_PATH: {"input_file": "../outside.npy"},
    }
    match fault:
        case (
            ReceiptFault.MEDIAN
            | ReceiptFault.SAMPLE_SD
            | ReceiptFault.SAMPLE_COUNT
            | ReceiptFault.ZERO_TIME
            | ReceiptFault.ARRAY_HASH
            | ReceiptFault.FILE_HASH
            | ReceiptFault.INPUT_PATH
        ):
            return record.model_copy(update=changes[fault])
        case ReceiptFault.WORK:
            stage = record.estimate.stages[0]
            altered = replace(stage, distance_component_visits=stage.distance_component_visits + 1)
            estimate = record.estimate.model_copy(
                update={"stages": (altered, *record.estimate.stages[1:])}
            )
            return record.model_copy(update={"estimate": estimate})
        case ReceiptFault.RESULT:
            value = record.result.value
            assert value is not None
            result = record.result.model_copy(update={"value": value + 1})
            return record.model_copy(update={"result": result})
        case ReceiptFault.MISSING_CASE | ReceiptFault.DUPLICATE_CASE:
            raise ParameterError("fault", "design faults require report-level mutation")
        case unreachable:
            assert_never(unreachable)


@pytest.mark.parametrize("fault", list(ReceiptFault))
def test_validator_when_receipt_is_corrupted_rejects_each_semantic_seam(
    benchmark_root: Path, fault: ReceiptFault
) -> None:
    # Given a receipt whose unmodified inputs and measurements validate.
    report = read_report(benchmark_root)
    assert validate_benchmarks(benchmark_root) == 4
    match fault:
        case ReceiptFault.MISSING_CASE:
            altered = report.model_copy(update={"records": report.records[1:]})
        case ReceiptFault.DUPLICATE_CASE:
            altered = report.model_copy(update={"records": (*report.records, report.records[0])})
        case (
            ReceiptFault.MEDIAN
            | ReceiptFault.SAMPLE_SD
            | ReceiptFault.SAMPLE_COUNT
            | ReceiptFault.ZERO_TIME
            | ReceiptFault.ARRAY_HASH
            | ReceiptFault.FILE_HASH
            | ReceiptFault.INPUT_PATH
            | ReceiptFault.WORK
            | ReceiptFault.RESULT
        ):
            first = altered_record(report.records[0], fault)
            altered = report.model_copy(update={"records": (first, *report.records[1:])})
        case unreachable:
            assert_never(unreachable)
    write_report(benchmark_root, altered)
    # When the corrupted real JSON is validated against the unchanged plan/inputs.
    # Then missing coverage, altered summaries, identity and numerical results fail closed.
    with pytest.raises(ParameterError):
        _ = validate_benchmarks(benchmark_root)


@pytest.mark.parametrize("refresh_hashes", [False, True])
def test_validator_when_input_bytes_change_rejects_even_refreshed_hashes(
    benchmark_root: Path, refresh_hashes: bool
) -> None:
    # Given a real stored field and a meaningful alteration outside replay roundoff.
    report = read_report(benchmark_root)
    first = report.records[0]
    path = benchmark_root / first.input_file
    array = np.load(path, allow_pickle=False)
    array.flat[0] += 0.125
    np.save(path, array, allow_pickle=False)
    if refresh_hashes:
        records = tuple(
            record.model_copy(
                update={"input_file_sha256": digest(path), "input_sha256": array_sha256(array)}
            )
            if record.input_file == first.input_file
            else record
            for record in report.records
        )
        write_report(benchmark_root, report.model_copy(update={"records": records}))
    # When exact identity and independently seeded replay are checked.
    # Then changing both custody hashes cannot authorize a different generated field.
    with pytest.raises(ParameterError):
        _ = validate_benchmarks(benchmark_root)


def test_validator_when_measured_input_is_missing_rejects_it(benchmark_root: Path) -> None:
    # Given a complete receipt with one required NPY removed from its isolated copy.
    report = read_report(benchmark_root)
    (benchmark_root / report.records[0].input_file).unlink()
    # When real input loading is required for numerical replay.
    # Then a missing file cannot be replaced by copied result fields.
    with pytest.raises(ParameterError) as failure:
        _ = validate_benchmarks(benchmark_root)
    assert failure.value.parameter == "artifacts"


class PlanFault(StrEnum):
    """Requests that must fail before a benchmark output directory is created."""

    TEMPLATE_BUDGET = "template_budget"
    PAIR_BUDGET = "pair_budget"
    MEMORY_BUDGET = "memory_budget"
    INPUT_BUDGET = "input_budget"
    ZERO_BLOCK = "zero_block"
    LARGE_BLOCK = "large_block"
    BOOLEAN_BLOCK = "boolean_block"
    DUPLICATE_BLOCK = "duplicate_block"
    DUPLICATE_SHAPE = "duplicate_shape"
    IMPOSSIBLE_SHAPE = "impossible_shape"


@pytest.mark.parametrize("fault", list(PlanFault))
def test_benchmark_when_preflight_request_is_invalid_creates_no_outputs(
    tmp_path: Path, fault: PlanFault
) -> None:
    # Given an invalid but real plan file under a new study root.
    root = tmp_path / "invalid"
    root.mkdir()
    original = small_plan()
    plan = original.model_dump(mode="json")
    embedding = original.embedding.model_dump(mode="json")
    changes = {
        PlanFault.TEMPLATE_BUDGET: {"embedding": embedding | {"max_templates": 2}},
        PlanFault.PAIR_BUDGET: {"embedding": embedding | {"max_pairs": 1}},
        PlanFault.MEMORY_BUDGET: {"embedding": embedding | {"max_memory_bytes": 1024}},
        PlanFault.INPUT_BUDGET: {"max_input_elements": 1},
        PlanFault.ZERO_BLOCK: {"block_sizes": [0, 4]},
        PlanFault.LARGE_BLOCK: {"block_sizes": [2, 4097]},
        PlanFault.BOOLEAN_BLOCK: {"block_sizes": [True, 4]},
        PlanFault.DUPLICATE_BLOCK: {"block_sizes": [2, 2]},
        PlanFault.DUPLICATE_SHAPE: {"shapes": [[8], [8]]},
        PlanFault.IMPOSSIBLE_SHAPE: {"shapes": [[2]]},
    }
    plan.update(changes[fault])
    path = root / "benchmark_plan.yaml"
    _ = path.write_text(yaml.safe_dump(plan), encoding="utf-8")
    # When the real benchmark runner validates domain and resource limits.
    with pytest.raises(ValidationError):
        _ = benchmark(root, path)
    # Then no field, timing receipt or figure exists after rejected preflight.
    assert not (root / "output").exists()
