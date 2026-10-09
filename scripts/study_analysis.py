# Copyright (c) 2026 Daniel Ari Friedman
"""Explicit estimator configurations and trial-level aggregation."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Literal, assert_never

from pydantic import JsonValue

from antropy_hd.complexity import ComplexityConfig, estimate_complexity
from antropy_hd.errors import ParameterError
from antropy_hd.models import EntropyResult
from antropy_hd.orchestration import AnalysisSpec, BatchConfig, BatchResult, canonical_json
from scripts.study_models import (
    Geometry,
    StudyCase,
    StudyComplexityRecord,
    StudyPlan,
    StudyRecord,
    StudyRow,
    StudySummary,
)


def study_batches(plan: StudyPlan) -> tuple[BatchConfig, BatchConfig, BatchConfig]:
    """Separate spatial observations, row-major observations and fixed probability alphabets."""
    embedding: dict[str, JsonValue] = {
        "shape": plan.embedding_shape,
        "max_templates": plan.max_templates,
        "max_pairs": plan.max_pairs,
        "max_memory_bytes": plan.max_memory_bytes,
    }
    native = [
        AnalysisSpec(
            id=f"hdse-r{r}",
            measure="hdse",
            parameters={
                "embedding": embedding,
                "match": {"tolerance": r, "block_size": plan.block_size},
            },
        )
        for r in sorted(plan.radii)
    ]
    native.extend(
        [
            AnalysisSpec(
                id="distribution",
                measure="distribution_entropy",
                parameters={
                    "embedding": embedding,
                    "bins": plan.symbol_bins,
                    "match": {"block_size": plan.block_size},
                },
            ),
            AnalysisSpec(
                id="permutation",
                measure="permutation_entropy",
                parameters={"embedding": embedding, "normalize": True},
            ),
            AnalysisSpec(
                id="spectral",
                measure="spectral_entropy",
                parameters={"normalize": True, "max_memory_bytes": plan.max_memory_bytes},
            ),
        ]
    )
    flattened = [
        AnalysisSpec(
            id=f"sample-r{r}",
            measure="sample_entropy",
            parameters={
                "embedding": embedding,
                "match": {"tolerance": r, "block_size": plan.block_size},
            },
        )
        for r in sorted(plan.radii)
    ]
    symbols = [
        AnalysisSpec(id="shannon", measure="shannon_entropy", parameters={"normalize": True}),
        AnalysisSpec(
            id="statistical",
            measure="statistical_complexity",
            parameters={"config": {"alphabet_size": plan.symbol_bins}},
        ),
    ]
    return (
        BatchConfig(analyses=tuple(native)),
        BatchConfig(analyses=tuple(flattened)),
        BatchConfig(analyses=tuple(symbols)),
    )


def batch_rows(case: StudyCase, geometry: Geometry, batch: BatchResult) -> list[StudyRow]:
    """Preserve estimator parameters, diagnostics and explicit nonfinite statuses."""
    rows: list[StudyRow] = []
    for spec in batch.config.analyses:
        result = batch.results[spec.id]
        match result:
            case EntropyResult():
                pass
            case tuple():
                raise ParameterError("study", "The scalar study cannot contain multiscale tuples")
            case unreachable:
                assert_never(unreachable)
        matching = spec.parameters.get("match")
        match matching:
            case dict():
                radius = matching.get("tolerance")
            case None:
                radius = None
            case str() | float() | int() | list() | bool():
                raise ParameterError("study", "Matching parameters require a mapping")
            case unreachable:
                assert_never(unreachable)
        rows.append(
            StudyRow.model_validate(
                {
                    "case_id": case.id,
                    "shape": "x".join(map(str, case.shape)),
                    "dimension": len(case.shape),
                    "family": case.family,
                    "mixing": case.mixing,
                    "trial": case.trial,
                    "geometry": geometry,
                    "analysis_id": spec.id,
                    "measure": result.measure,
                    "radius": radius,
                    "value": result.value,
                    "status": result.status.value,
                    "observations": result.n_observations,
                    "parameters_json": canonical_json(result.parameters),
                    "diagnostics_json": canonical_json(result.diagnostics),
                }
            )
        )
    return rows


def record_rows(record: StudyRecord) -> list[StudyRow]:
    """Expand all three authenticated input geometries for a field."""
    return [
        *batch_rows(record.case, "native", record.native),
        *batch_rows(record.case, "flattened", record.flattened),
        *batch_rows(record.case, "symbols", record.symbols),
    ]


def preflight_study(plan: StudyPlan) -> list[StudyComplexityRecord]:
    """Plan every allocating request before creating any output files."""
    reports: list[StudyComplexityRecord] = []
    native, flattened, _ = study_batches(plan)
    for shape in sorted(plan.shapes):
        requests: tuple[
            tuple[Literal["native", "flattened"], tuple[int, ...], BatchConfig], ...
        ] = (("native", shape, native), ("flattened", (math.prod(shape),), flattened))
        for geometry, actual_shape, batch in requests:
            for spec in batch.analyses:
                config = ComplexityConfig.model_validate(
                    {
                        "measure": spec.measure,
                        "embedding": spec.parameters.get(
                            "embedding", {"max_memory_bytes": plan.max_memory_bytes}
                        ),
                        "match": spec.parameters.get("match", {}),
                        "bins": spec.parameters.get("bins", plan.symbol_bins),
                    }
                )
                estimate = estimate_complexity(actual_shape, config)
                if not estimate.feasible:
                    raise ParameterError(
                        "study", f"Infeasible {geometry} {spec.id}: {estimate.resource_violations}"
                    )
                reports.append(
                    StudyComplexityRecord(
                        original_shape=shape,
                        geometry=geometry,
                        analysis_id=spec.id,
                        estimate=estimate,
                        guard_peak_bytes=estimate.guard_peak_bytes,
                        distance_component_visits=estimate.distance_component_visits,
                    )
                )
    visits = (
        sum(item.distance_component_visits for item in reports)
        * (len(plan.controls) + len(plan.mixing_probabilities))
        * plan.replicates
    )
    if visits > plan.max_distance_component_visits:
        raise ParameterError("study", "Scheduled distance evaluations exceed the study work budget")
    return reports


def summarize(rows: list[StudyRow]) -> list[StudySummary]:
    """Trials, not overlapping template pairs, are the unit of observed variability."""
    groups: dict[tuple[str, str, float | None, str, str], list[StudyRow]] = defaultdict(list)
    for row in rows:
        groups[(row.shape, row.family, row.mixing, row.geometry, row.analysis_id)].append(row)
    summaries: list[StudySummary] = []
    for group in groups.values():
        first = group[0]
        values = [row.value for row in group if row.value is not None]
        summaries.append(
            StudySummary(
                shape=first.shape,
                dimension=first.dimension,
                family=first.family,
                mixing=first.mixing,
                geometry=first.geometry,
                analysis_id=first.analysis_id,
                measure=first.measure,
                radius=first.radius,
                n_total=len(group),
                n_finite=len(values),
                n_undefined=sum(row.status == "undefined" for row in group),
                n_infinite=sum(row.status == "infinite" for row in group),
                finite_mean=statistics.mean(values) if values else None,
                finite_sample_sd=statistics.stdev(values) if len(values) > 1 else None,
            )
        )
    return summaries
