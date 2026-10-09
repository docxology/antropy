# Copyright (c) 2026 Daniel Ari Friedman
"""Exact planning compared with real spatial kernels and resource-limit failures."""

from itertools import combinations, product
from math import prod
from typing import assert_never

import numpy as np
import pytest
from numpy.typing import NDArray
from pydantic import JsonValue, ValidationError

from antropy_hd.complexity import ComplexityConfig, ComplexityMeasure, estimate_complexity
from antropy_hd.embedding import local_templates, paired_templates
from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.models import EmbeddingConfig, EntropyResult, Exclusion, MatchConfig
from antropy_hd.orchestration import AnalysisSpec, analyze
from antropy_hd.pairs import pair_blocks
from antropy_hd.template_entropy import approximate_entropy, hdse


def execute_planned_measure(data: NDArray[np.float64], config: ComplexityConfig) -> EntropyResult:
    """Drive the real registered estimator with the exact settings modeled by its plan."""
    parameters: dict[str, JsonValue] = {"embedding": config.embedding.model_dump(mode="json")}
    match config.measure:
        case (
            ComplexityMeasure.HDSE
            | ComplexityMeasure.SAMPLE
            | ComplexityMeasure.APPROXIMATE
            | ComplexityMeasure.FUZZY
        ):
            parameters["match"] = config.match.model_dump(mode="json")
        case ComplexityMeasure.DISTRIBUTION:
            parameters |= {"match": config.match.model_dump(mode="json"), "bins": config.bins}
        case ComplexityMeasure.PERMUTATION | ComplexityMeasure.WEIGHTED_PERMUTATION:
            parameters["max_pattern_length"] = config.max_pattern_length
        case ComplexityMeasure.SVD:
            pass
        case ComplexityMeasure.SPECTRAL:
            parameters = {"max_memory_bytes": config.embedding.max_memory_bytes}
        case unreachable:
            assert_never(unreachable)
    result = analyze(
        data, AnalysisSpec(id="guard", measure=config.measure.value, parameters=parameters)
    )
    assert isinstance(result, EntropyResult)
    return result


@pytest.mark.parametrize(
    ("input_shape", "shape", "delay", "stride", "axes"),
    [
        ((9,), (2,), (2,), (2,), (0,)),
        ((7, 8), (2, 1), (2, 1), (1, 2), (0,)),
        ((6, 7, 5), (1, 2, 1), (2, 1, 2), (2, 1, 1), (1, 2)),
    ],
)
@pytest.mark.parametrize("exclusion", list(Exclusion))
@pytest.mark.parametrize("theiler", [0, 1, 3, 100])
def test_plan_when_geometry_is_anisotropic_matches_independent_pairs_and_real_counts(
    input_shape: tuple[int, ...],
    shape: tuple[int, ...],
    delay: tuple[int, ...],
    stride: tuple[int, ...],
    axes: tuple[int, ...],
    exclusion: Exclusion,
    theiler: int,
) -> None:
    # Given independent native-origin enumeration and coordinate/Theiler filtering.
    larger = tuple(width + int(axis in axes) for axis, width in enumerate(shape))
    origins = list(
        product(
            *(
                range(0, size - (width - 1) * lag, step)
                for size, width, lag, step in zip(input_shape, larger, delay, stride, strict=True)
            )
        )
    )
    selected = sum(
        max(abs(a - b) for a, b in zip(left, right, strict=True)) > theiler
        and (exclusion is Exclusion.SELF or all(a != b for a, b in zip(left, right, strict=True)))
        for left, right in combinations(origins, 2)
    )
    embedding = EmbeddingConfig(shape=shape, delay=delay, stride=stride, extend_axes=axes)
    matching = MatchConfig(
        exclusion=exclusion, theiler=theiler, block_size=3, tolerance=1, relative=False
    )
    data = np.arange(prod(input_shape), dtype=np.float64).reshape(input_shape)
    actual = hdse(data, embedding=embedding, match=matching)
    # When shape-only complexity is planned without materializing templates.
    result = estimate_complexity(input_shape, ComplexityConfig(embedding=embedding, match=matching))
    # Then exact populations agree with both independent enumeration and executed HDSE.
    assert result.stages[0].templates == len(origins) == actual.n_observations
    assert result.stages[0].eligible_pairs == selected == actual.diagnostics["eligible_pairs"]
    assert result.stages[1].eligible_pairs == selected
    assert result.feasible


@pytest.mark.parametrize("block_size", [1, 2, 3, 20])
def test_plan_when_blocks_include_masked_cells_counts_actual_kernel_work(block_size: int) -> None:
    # Given real pair blocks whose distances are computed before masking.
    data = np.arange(9, dtype=np.float64)
    embedding = EmbeddingConfig()
    matching = MatchConfig(block_size=block_size, theiler=1)
    templates = paired_templates(data, embedding)
    observed_cells = 0
    observed_blocks = 0
    for current in (templates.base, templates.extended):
        for distances, _ in pair_blocks(current, embedding, matching):
            observed_cells += distances.size
            observed_blocks += 1
    # When the exact blocked schedule is planned.
    result = estimate_complexity(data.shape, ComplexityConfig(embedding=embedding, match=matching))
    # Then excluded, diagonal and duplicate diagonal-block cells remain accounted for.
    assert result.computed_distance_cells == observed_cells
    assert sum(stage.distance_blocks for stage in result.stages) == observed_blocks
    assert result.distance_component_visits == observed_cells // 2 * 5
    assert observed_cells > 2 * result.stages[0].eligible_pairs


def test_plan_when_population_is_huge_does_not_construct_origins() -> None:
    # Given a billion-element axis that cannot fit the default template budget.
    shape = (10**9,)
    # When only integer geometry/combinatorics are evaluated.
    result = estimate_complexity(shape)
    # Then the huge request is described and flagged without allocating its grid.
    assert result.stages[0].templates == 10**9 - 2
    assert result.input_float64_bytes == 8 * 10**9
    assert not result.feasible
    assert {item.parameter for item in result.resource_violations} == {
        "max_templates",
        "max_pairs",
        "max_memory_bytes",
    }


def test_plan_when_exclusions_remove_every_pair_still_enforces_candidate_budget() -> None:
    # Given origin exclusions eliminating all eligible pairs but not kernel work.
    embedding = EmbeddingConfig(max_pairs=1)
    matching = MatchConfig(theiler=100)
    # When the pre-exclusion candidate population is planned.
    result = estimate_complexity((8,), ComplexityConfig(embedding=embedding, match=matching))
    # Then the real estimator's early pair-population guard is still predicted.
    assert result.stages[0].eligible_pairs == 0
    assert any(item.parameter == "max_pairs" for item in result.resource_violations)
    with pytest.raises(ResourceError, match="max_pairs"):
        hdse(np.arange(8), embedding=embedding, match=matching)


def test_plan_when_memory_boundary_changes_matches_real_paired_guard() -> None:
    # Given an exact conservative guard boundary computed for a small paired grid.
    generous = ComplexityConfig(match=MatchConfig(block_size=2))
    required = estimate_complexity((9,), generous).guard_peak_bytes
    # When the budget is one byte below that boundary.
    embedding = EmbeddingConfig(max_memory_bytes=required - 1)
    result = estimate_complexity((9,), ComplexityConfig(embedding=embedding, match=generous.match))
    # Then the resource report and executed estimator both reject the request.
    assert not result.feasible
    with pytest.raises(ResourceError, match="max_memory_bytes"):
        hdse(np.ones(9), embedding=embedding, match=generous.match)


def test_plan_when_memory_budget_equals_guard_allows_real_computation() -> None:
    # Given the exact maximum guard amount for the configured complete path.
    matching = MatchConfig(block_size=2, tolerance=1, relative=False)
    required = estimate_complexity((9,), ComplexityConfig(match=matching)).guard_peak_bytes
    embedding = EmbeddingConfig(max_memory_bytes=required)
    # When the boundary-equal request is planned.
    result = estimate_complexity((9,), ComplexityConfig(embedding=embedding, match=matching))
    # Then matching conservative guards accept it and the real estimator completes.
    assert result.feasible
    assert hdse(np.ones(9), embedding=embedding, match=matching).as_float() == 0


@pytest.mark.parametrize("measure", list(ComplexityMeasure))
def test_plan_when_each_method_reaches_guard_accepts_equal_budget_and_rejects_one_byte_less(
    measure: ComplexityMeasure,
) -> None:
    # Given the largest real guard predicted for each of the nine modeled estimators.
    shape = (9,) if measure is ComplexityMeasure.SAMPLE else (5, 6)
    data = np.arange(prod(shape), dtype=np.float64).reshape(shape)
    original = ComplexityConfig(measure=measure, match=MatchConfig(block_size=3))
    required = estimate_complexity(shape, original).guard_peak_bytes
    equal = ComplexityConfig.model_validate(
        original.model_dump()
        | {"embedding": original.embedding.model_dump() | {"max_memory_bytes": required}}
    )
    lower = ComplexityConfig.model_validate(
        original.model_dump()
        | {"embedding": original.embedding.model_dump() | {"max_memory_bytes": required - 1}}
    )
    # When the actual registered estimator executes at and immediately below its planned guard.
    result = execute_planned_measure(data, equal)
    # Then the full real path passes at equality and the conservative resource gate fails below it.
    assert result.n_observations > 0
    assert estimate_complexity(shape, equal).feasible
    assert not estimate_complexity(shape, lower).feasible
    with pytest.raises(ResourceError, match="max_memory_bytes"):
        execute_planned_measure(data, lower)


def test_plan_when_approximate_entropy_uses_separate_populations_counts_full_ordered_cells() -> (
    None
):
    # Given base and extended templates from separate full origin populations.
    data = np.ones((5, 6))
    embedding = EmbeddingConfig(shape=(2, 1), delay=(1, 2), extend_axes=(1,))
    matching = MatchConfig(block_size=3, tolerance=1, relative=False, closed=True)
    base = local_templates(data, embedding)
    extended = local_templates(data, EmbeddingConfig(shape=(2, 2), delay=(1, 2)))
    actual = approximate_entropy(data, embedding=embedding, match=matching)
    # When included-self ordered distance traversals are planned.
    result = estimate_complexity(
        data.shape,
        ComplexityConfig(measure="approximate_entropy", embedding=embedding, match=matching),
    )
    # Then population counts and N-squared traversals match the real ApEn definition.
    assert result.stages[0].templates == len(base.values) == actual.n_observations
    assert (
        result.stages[1].templates
        == len(extended.values)
        == actual.diagnostics["extended_observations"]
    )
    assert result.computed_distance_cells == len(base.values) ** 2 + len(extended.values) ** 2
    assert result.stages[0].eligible_pairs == len(base.values) ** 2


def test_plan_when_fuzzy_radius_is_zero_skips_distance_kernels() -> None:
    # Given a known zero kernel width, independent of the input values.
    matching = MatchConfig(tolerance=0)
    # When the shape-only fuzzy path is planned.
    result = estimate_complexity((8,), ComplexityConfig(measure="fuzzy_entropy", match=matching))
    # Then template extraction remains but no kernel guard or distance work executes.
    assert result.computed_distance_cells == 0
    assert all("kernel" not in item.stage for item in result.resources)


def test_plan_when_fuzzy_radius_may_be_positive_includes_scaled_template_workspace() -> None:
    # Given identical geometry for plain and fuzzy paired entropy.
    matching = MatchConfig(block_size=2)
    plain = estimate_complexity((9,), ComplexityConfig(match=matching))
    # When the fuzzy scaled/shifted/centered buffers are planned.
    fuzzy = estimate_complexity((9,), ComplexityConfig(measure="fuzzy_entropy", match=matching))
    # Then kernel work is the same but its conservative live storage is larger.
    assert fuzzy.computed_distance_cells == plain.computed_distance_cells
    assert fuzzy.guard_peak_bytes >= plain.guard_peak_bytes
    assert any("positive resolved radius" in item for item in fuzzy.assumptions)


def test_plan_when_distribution_entropy_uses_two_passes_counts_reused_templates_once() -> None:
    # Given six local pair templates and two distance traversals.
    config = ComplexityConfig(
        measure="distribution_entropy", bins=23, match=MatchConfig(block_size=2)
    )
    # When maximum-distance and histogram passes are planned.
    result = estimate_complexity((7,), config)
    # Then two kernel passes reuse one extracted local template population.
    assert len(result.stages) == 2
    assert result.stages[0].computed_distance_cells == result.stages[1].computed_distance_cells
    assert (
        next(term.count for term in result.terms if term.name == "extracted_template_components")
        == 12
    )
    assert next(term.count for term in result.terms if term.name == "histogram_bins") == 23


@pytest.mark.parametrize(
    "measure", ["permutation_entropy", "weighted_permutation_entropy", "svd_entropy"]
)
def test_plan_when_local_measure_has_no_pair_engine_excludes_quadratic_pair_counts(
    measure: str,
) -> None:
    # Given rectangular local geometry, independently counted as 4x4 origins.
    config = ComplexityConfig(
        measure=measure, embedding=EmbeddingConfig(shape=(1, 3), stride=(2, 1))
    )
    # When local ordinal or SVD analysis is planned.
    result = estimate_complexity((7, 6), config)
    # Then local-template storage is accounted without inventing pair distances.
    assert result.stages[0].templates == 16
    assert result.stages[0].features == 3
    assert result.computed_distance_cells == 0
    assert result.stages[0].candidate_pairs == 0
    assert result.feasible
    assert any(term.interpretation == "asymptotic_size_term" for term in result.terms)


def test_plan_when_ordinal_pattern_guard_is_exceeded_predicts_resource_failure() -> None:
    # Given a 4x4 local alphabet beyond the default ten-position ordinal limit.
    # When its local plan is evaluated.
    result = estimate_complexity(
        (5, 5), ComplexityConfig(measure="permutation_entropy", embedding=EmbeddingConfig(shape=4))
    )
    # Then the pattern resource is reported independently of template memory.
    assert any(
        item.parameter == "max_pattern_length" and item.required == 16
        for item in result.resource_violations
    )


def test_plan_when_fft_is_anisotropic_uses_every_axis_and_actual_guard() -> None:
    # Given 2x8x3 samples with logarithmic axis terms (1,3,2).
    config = ComplexityConfig(measure="spectral_entropy")
    # When full N-D FFT complexity is planned.
    result = estimate_complexity((2, 8, 3), config)
    # Then the current 80-byte-per-cell guard and symbolic multidimensional FFT term agree.
    assert result.guard_peak_bytes == 48 * 80
    assert result.stages == ()
    assert next(term.count for term in result.terms if term.name == "fft_N_sum_log2_axes") == 48 * 6


def test_plan_when_sample_entropy_is_one_dimensional_has_paired_geometry() -> None:
    # Given a 1D common-origin SampEn request.
    # When its current HDSE-based implementation is planned.
    result = estimate_complexity((8,), ComplexityConfig(measure="sample_entropy"))
    # Then two paired template stages are present.
    assert [stage.features for stage in result.stages] == [2, 3]


@pytest.mark.parametrize("shape", [(), (0,), (-1, 3)])
def test_plan_when_shape_is_invalid_rejects_it(shape: tuple[int, ...]) -> None:
    # Given a nonsensical dataset shape.
    # When shape-only planning is requested.
    # Then an empty or negative dataset cannot receive a feasible plan.
    with pytest.raises((ValidationError, ParameterError)):
        estimate_complexity(shape)


@pytest.mark.parametrize(
    "config",
    [
        ComplexityConfig(measure="sample_entropy"),
        ComplexityConfig(embedding=EmbeddingConfig(shape=(1,))),
        ComplexityConfig(embedding=EmbeddingConfig(shape=5)),
        ComplexityConfig(embedding=EmbeddingConfig(extend_axes=(2,))),
    ],
)
def test_plan_when_geometry_cannot_apply_rejects_it(config: ComplexityConfig) -> None:
    # Given invalid dimensionality or embedding geometry for a small spatial field.
    # When the plan is resolved.
    # Then configuration errors are not mislabeled as resource feasibility.
    with pytest.raises(ParameterError):
        estimate_complexity((4, 4), config)


def test_plan_when_only_one_common_origin_exists_rejects_paired_entropy() -> None:
    # Given one complete extended window and no unordered comparison population.
    # When paired entropy is planned.
    # Then the estimator's minimum two-origin contract is enforced.
    with pytest.raises(ParameterError):
        estimate_complexity((3,))


@pytest.mark.parametrize(
    "method", ["hdse", "sample_entropy", "fuzzy_entropy", "approximate_entropy"]
)
@pytest.mark.parametrize("relative", [False, True])
def test_plan_when_sd_degrees_of_freedom_exceed_data_rejects_it(
    method: str, relative: bool
) -> None:
    # Given an invalid global-SD denominator.
    # When the corresponding pair estimator is planned.
    # Then numerical boundary validation is preserved.
    with pytest.raises(ParameterError, match="ddof"):
        estimate_complexity(
            (8,), ComplexityConfig(measure=method, match=MatchConfig(ddof=8, relative=relative))
        )
    with pytest.raises(ParameterError, match="ddof"):
        execute_planned_measure(
            np.arange(8, dtype=np.float64),
            ComplexityConfig(measure=method, match=MatchConfig(ddof=8, relative=relative)),
        )


@pytest.mark.parametrize("method", ["approximate_entropy", "distribution_entropy"])
def test_config_when_method_cannot_consume_matching_options_rejects_it(method: str) -> None:
    # Given exclusions incompatible with ApEn, or a radius incompatible with DistEn.
    matching = MatchConfig(theiler=1, tolerance=0.5)
    # When planning configuration is parsed.
    # Then unsupported matching options are not silently accepted.
    with pytest.raises(ValidationError, match="match"):
        ComplexityConfig(measure=method, match=matching)


def test_config_when_measure_is_unknown_rejects_it() -> None:
    # Given a method with no implementation-specific planning model.
    # When the configuration is parsed.
    # Then a generic fabricated estimate is not substituted.
    with pytest.raises(ValidationError):
        ComplexityConfig(measure="invented")


def test_plan_when_serialized_has_strict_typed_json_records() -> None:
    # Given a small feasible estimator plan.
    result = estimate_complexity((8,))
    # When nested frozen planning records are serialized and parsed.
    recovered = type(result).model_validate_json(result.model_dump_json())
    # Then integer counts and stages preserve their typed values.
    assert recovered == result
    assert recovered.config.measure is ComplexityMeasure.HDSE
