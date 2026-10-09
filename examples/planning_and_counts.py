#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd>=0.2"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# Copyright (c) 2026 Daniel Ari Friedman
"""Compare allocation-free plans, actual block replay and observed HDSE diagnostics."""

import sys
from importlib.metadata import version
from typing import ClassVar, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from antropy_hd import (
    ComplexityConfig,
    ComplexityEstimate,
    EmbeddingConfig,
    EntropyResult,
    Exclusion,
    MatchConfig,
    ParameterError,
    ResourceError,
    estimate_complexity,
    hdse,
)
from antropy_hd.embedding import paired_templates
from antropy_hd.orchestration import array_sha256
from antropy_hd.pairs import pair_blocks


class ObservedBudgetFailure(BaseModel):
    """An actual rejected request, preserving its typed error fields."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    budget_bytes: int
    parameter: str
    reason: str


class BlockCase(BaseModel):
    """Computed work rather than fabricated timing predictions or success flags."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    estimate: ComplexityEstimate
    feasible: bool
    guard_peak_bytes: int
    planned_distance_cells: int
    replayed_distance_cells: int
    replayed_blocks: int
    replayed_eligible_pairs_per_stage: tuple[int, ...]
    observed_hdse: EntropyResult
    rejected_budget: ObservedBudgetFailure


class PlanningReport(BaseModel):
    """Same input under different block schedules plus a shape-only infeasible request."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal[1] = 1
    package_version: str
    seed: int
    input_sha256: str
    cases: tuple[BlockCase, ...]
    large_shape_plan: ComplexityEstimate
    large_shape_feasible: bool


def main() -> None:
    """Drive actual numerical kernels and a negative memory-budget control."""
    seed = 20261009
    field = np.random.default_rng(seed).normal(size=(5, 6))
    embedding = EmbeddingConfig(shape=(2, 1), delay=(1, 2), stride=(1, 1), extend_axes=(0,))
    cases: list[BlockCase] = []
    for block_size in (1, 4, 128):
        matching = MatchConfig(
            tolerance=1.5, exclusion=Exclusion.COORDINATE, theiler=1, block_size=block_size
        )
        config = ComplexityConfig(embedding=embedding, match=matching)
        estimate = estimate_complexity(field.shape, config)
        observed = hdse(field, embedding=embedding, match=matching)
        templates = paired_templates(field, embedding)
        cells, blocks = 0, 0
        eligible_counts: list[int] = []
        for current, other in (
            (templates.base, templates.extended),
            (templates.extended, templates.base),
        ):
            eligible_pairs = 0
            for distances, eligible in pair_blocks(
                current, embedding, matching, live_bytes=other.values.nbytes
            ):
                cells += distances.size
                blocks += 1
                eligible_pairs += int(np.count_nonzero(eligible))
            eligible_counts.append(eligible_pairs)
        below = EmbeddingConfig.model_validate(
            embedding.model_dump() | {"max_memory_bytes": estimate.guard_peak_bytes - 1}
        )
        try:
            _ = hdse(field, embedding=below, match=matching)
        except ResourceError as error:
            failure = ObservedBudgetFailure(
                budget_bytes=below.max_memory_bytes, parameter=error.parameter, reason=error.reason
            )
        else:
            raise ParameterError(
                "max_memory_bytes", "one-byte-below-guard control unexpectedly completed"
            )
        cases.append(
            BlockCase(
                estimate=estimate,
                feasible=estimate.feasible,
                guard_peak_bytes=estimate.guard_peak_bytes,
                planned_distance_cells=estimate.computed_distance_cells,
                replayed_distance_cells=cells,
                replayed_blocks=blocks,
                replayed_eligible_pairs_per_stage=tuple(eligible_counts),
                observed_hdse=observed,
                rejected_budget=failure,
            )
        )
    large = estimate_complexity((128, 128, 128), ComplexityConfig())
    report = PlanningReport(
        package_version=version("antropy-hd"),
        seed=seed,
        input_sha256=array_sha256(field),
        cases=tuple(cases),
        large_shape_plan=large,
        large_shape_feasible=large.feasible,
    )
    _ = sys.stdout.write(report.model_dump_json() + "\n")


if __name__ == "__main__":
    main()
