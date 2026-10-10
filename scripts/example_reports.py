# Copyright (c) 2026 Daniel Ari Friedman
"""Stable JSON records for runnable examples, preserving original field contracts."""

from typing import Literal

from antropy_hd.complexity import ComplexityEstimate
from antropy_hd.inference_models import IntervalResult, PermutationResult
from antropy_hd.models import EmbeddingConfig, EntropyResult, MatchConfig
from scripts.example_models import ExampleModel, InferencePlan


class SpatialCase(ExampleModel):
    """One generated native field and each measure's effective geometry."""

    input_shape: tuple[int, ...]
    input_sha256: str
    embedding: EmbeddingConfig
    match: MatchConfig
    hdse: EntropyResult
    weighted_permutation: EntropyResult
    svd: EntropyResult


class SpatialReport(ExampleModel):
    """Reproducible seed and actual results including nonfinite statuses."""

    schema_version: Literal[1] = 1
    package_version: str
    seed: int
    cases: tuple[SpatialCase, ...]


class AlphabetReport(ExampleModel):
    """Full fixed probability alphabet with both tails and empty categories."""

    schema_version: Literal[1] = 1
    package_version: str
    seed: int
    input_shape: tuple[int, ...]
    input_sha256: str
    cuts: tuple[float, ...]
    cut_side: Literal["left", "right"] = "right"
    categories: tuple[str, ...]
    counts: tuple[int, ...]
    probabilities: tuple[float, ...]
    unoccupied_categories: tuple[int, ...]
    shannon_bits: EntropyResult
    normalized_shannon: EntropyResult
    js_to_uniform_bits: EntropyResult
    statistical_complexity: EntropyResult
    uniform_reference_complexity: EntropyResult
    delta_reference_complexity: EntropyResult


class ObservedBudgetFailure(ExampleModel):
    """An actual rejected request with typed numerical error fields."""

    budget_bytes: int
    parameter: str
    reason: str


class BlockCase(ExampleModel):
    """Computed work and real kernel diagnostics for the same request."""

    estimate: ComplexityEstimate
    feasible: bool
    guard_peak_bytes: int
    planned_distance_cells: int
    replayed_distance_cells: int
    replayed_blocks: int
    replayed_eligible_pairs_per_stage: tuple[int, ...]
    observed_hdse: EntropyResult
    rejected_budget: ObservedBudgetFailure


class PlanningReport(ExampleModel):
    """One input under several schedules and a large shape-only request."""

    schema_version: Literal[1] = 1
    package_version: str
    seed: int
    input_sha256: str
    cases: tuple[BlockCase, ...]
    large_shape_plan: ComplexityEstimate
    large_shape_feasible: bool


class InferenceReport(ExampleModel):
    """A separate inference example; every p-value and interval is computed."""

    schema_version: Literal[1] = 1
    package_version: str
    plan: InferencePlan
    permutation: PermutationResult
    bootstrap: IntervalResult
    binomial: IntervalResult
    family_p_values: tuple[float, ...]
    holm_adjusted: tuple[float, ...]


type ExampleReport = SpatialReport | AlphabetReport | PlanningReport | InferenceReport
