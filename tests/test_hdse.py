# Copyright (c) 2026 Daniel Ari Friedman
"""Independent spatial enumeration and exact numerical contracts."""

import itertools
import math
from typing import assert_never

import numpy as np
import pytest
from numpy.typing import NDArray
from pydantic import ValidationError

from antropy_hd import (
    EmbeddingConfig,
    Exclusion,
    MatchConfig,
    Metric,
    ParameterError,
    ResourceError,
    Status,
    hdse,
    sample_entropy,
)


def oracle(
    array: NDArray[np.float64],
    shape: tuple[int, ...],
    delay: tuple[int, ...],
    stride: tuple[int, ...],
    axes: tuple[int, ...],
    matching: MatchConfig,
) -> tuple[int, int, int]:
    """Read original spatial elements directly, without production embedding or kernels."""
    larger = tuple(width + int(axis in axes) for axis, width in enumerate(shape))
    origins = list(
        itertools.product(
            *(
                range(0, size - (width - 1) * lag, step)
                for size, width, lag, step in zip(array.shape, larger, delay, stride, strict=True)
            )
        )
    )
    threshold = (
        matching.tolerance * float(np.std(array, ddof=matching.ddof))
        if matching.relative
        else matching.tolerance
    )
    base, extended, eligible = 0, 0, 0
    for left, right in itertools.combinations(origins, 2):
        if matching.exclusion == Exclusion.COORDINATE and not all(
            a != b for a, b in zip(left, right, strict=True)
        ):
            continue
        if max(abs(a - b) for a, b in zip(left, right, strict=True)) <= matching.theiler:
            continue
        eligible += 1
        matches: list[bool] = []
        for block in (shape, larger):
            differences = [
                abs(
                    float(
                        array[
                            tuple(
                                a + k * lag for a, k, lag in zip(left, offset, delay, strict=True)
                            )
                        ]
                    )
                    - float(
                        array[
                            tuple(
                                a + k * lag for a, k, lag in zip(right, offset, delay, strict=True)
                            )
                        ]
                    )
                )
                for offset in itertools.product(*(range(width) for width in block))
            ]
            match matching.metric:
                case Metric.CHEBYSHEV:
                    distance = max(differences)
                case Metric.EUCLIDEAN:
                    distance = math.sqrt(sum(delta * delta for delta in differences))
                case Metric.CITYBLOCK:
                    distance = sum(differences)
                case unreachable:
                    assert_never(unreachable)
            matches.append(distance <= threshold if matching.closed else distance < threshold)
        base += int(matches[0])
        extended += int(matches[1])
    return base, extended, eligible


@pytest.mark.parametrize("ndim", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("metric", list(Metric))
@pytest.mark.parametrize("closed", [False, True])
def test_counts_match_independent_spatial_oracle(ndim: int, metric: Metric, closed: bool) -> None:
    # Given small native-dimensional integer fields and an independent oracle.
    array = np.random.default_rng(170 + ndim).integers(0, 3, size=(3,) * ndim).astype(float)
    config = MatchConfig(tolerance=1.0, relative=False, metric=metric, closed=closed, block_size=3)
    expected = oracle(array, (1,) * ndim, (1,) * ndim, (1,) * ndim, tuple(range(ndim)), config)
    # When exact HDSE enumerates the same population in blocks.
    result = hdse(array, embedding=EmbeddingConfig(shape=1), match=config)
    # Then all underlying populations agree, including strict-threshold controls.
    assert (
        result.diagnostics["base_matches"],
        result.diagnostics["extended_matches"],
        result.diagnostics["eligible_pairs"],
    ) == expected


@pytest.mark.parametrize(
    ("exclusion", "expected"), [(Exclusion.SELF, math.log(6)), (Exclusion.COORDINATE, math.log(2))]
)
def test_paper_ambiguity_changes_real_pair_population(
    exclusion: Exclusion, expected: float
) -> None:
    # Given a source-sensitive field whose conventions produce different counts.
    array = [[0, 0, 0], [0, 0, 1], [0, 1, 0]]
    # When explicit exclusion is selected.
    result = hdse(
        array,
        embedding=EmbeddingConfig(shape=1),
        match=MatchConfig(tolerance=0.5, relative=False, exclusion=exclusion),
    )
    # Then tuple/coordinate conventions are distinguishable.
    assert result.as_float() == pytest.approx(expected)


@pytest.mark.parametrize(("closed", "counts"), [(False, (3, 1)), (True, (6, 6))])
def test_boundary_equality_is_explicit(closed: bool, counts: tuple[int, int]) -> None:
    # Given distances exactly on the radius boundary.
    matching = MatchConfig(tolerance=1.0, relative=False, closed=closed)
    # When the boundary convention changes.
    result = hdse([0, 0, 1, 0, 1], embedding=EmbeddingConfig(shape=1), match=matching)
    # Then equal-radius pairs are included only under the closed convention.
    assert (result.diagnostics["base_matches"], result.diagnostics["extended_matches"]) == counts


@pytest.mark.parametrize(
    ("data", "matching", "status"),
    [
        ([1, 1, 1, 1], MatchConfig(), Status.UNDEFINED),
        ([1, 1, 1, 1], MatchConfig(tolerance=0.1, relative=False), Status.FINITE),
        ([0, 0, 1], MatchConfig(tolerance=0.1, relative=False), Status.INFINITE),
        ([0, 1, 2], MatchConfig(tolerance=0.1, relative=False), Status.UNDEFINED),
    ],
)
def test_degenerate_ratios_are_tagged(
    data: list[int], matching: MatchConfig, status: Status
) -> None:
    # Given constant, no-match or extension-failure data.
    # When HDSE is estimated.
    result = hdse(data, embedding=EmbeddingConfig(shape=1), match=matching)
    # Then the strict JSON status carries the mathematical state.
    assert result.status == status
    assert "NaN" not in result.model_dump_json()
    assert "Infinity" not in result.model_dump_json()


@pytest.mark.parametrize(
    ("delay", "stride", "axes", "exclusion", "theiler"),
    [
        ((2, 1), (1, 2), (0,), Exclusion.SELF, 0),
        ((1, 2), (2, 1), (1,), Exclusion.COORDINATE, 0),
        ((1, 1), (1, 1), (0, 1), Exclusion.SELF, 2),
    ],
)
def test_anisotropic_geometry_and_exclusions_match_oracle(
    delay: tuple[int, int],
    stride: tuple[int, int],
    axes: tuple[int, ...],
    exclusion: Exclusion,
    theiler: int,
) -> None:
    # Given rectangular local blocks with nontrivial lag and stride.
    array = np.random.default_rng(42).integers(0, 4, size=(7, 6)).astype(float)
    matching = MatchConfig(
        tolerance=1.0,
        relative=False,
        closed=True,
        exclusion=exclusion,
        theiler=theiler,
        block_size=4,
    )
    expected = oracle(array, (2, 1), delay, stride, axes, matching)
    # When the geometry is applied.
    result = hdse(
        array,
        embedding=EmbeddingConfig(shape=(2, 1), delay=delay, stride=stride, extend_axes=axes),
        match=matching,
    )
    # Then no flattening or off-by-one changes the pair population.
    assert (
        result.diagnostics["base_matches"],
        result.diagnostics["extended_matches"],
        result.diagnostics["eligible_pairs"],
    ) == expected


def test_relative_threshold_is_affine_and_axis_permutation_invariant() -> None:
    # Given the same structure under uniform affine transformation and axis permutation.
    array = np.random.default_rng(41).normal(size=(6, 7))
    # When all variants use global-relative Chebyshev matching.
    results = [
        hdse(variant, embedding=EmbeddingConfig(shape=1), match=MatchConfig(tolerance=1.5))
        for variant in (array, 3 * array + 10, array.T)
    ]
    # Then spatial order and global units do not change the ratio.
    assert len({result.as_float() for result in results}) == 1


@pytest.mark.parametrize(
    "config",
    [
        EmbeddingConfig(shape=8),
        EmbeddingConfig(shape=(1, 1)),
        EmbeddingConfig(shape=1, extend_axes=(1,)),
        EmbeddingConfig(shape=1, max_templates=2),
        EmbeddingConfig(shape=1, max_pairs=1),
        EmbeddingConfig(shape=1, max_memory_bytes=1024),
    ],
)
def test_infeasible_geometry_is_rejected(config: EmbeddingConfig) -> None:
    # Given a real request beyond a geometry or hard resource limit.
    # When templates are requested.
    with pytest.raises((ParameterError, ResourceError)):
        hdse(np.arange(7), embedding=config)
    # Then no partial numeric estimate substitutes for failure.


@pytest.mark.parametrize(
    "data", [[], 1.0, [math.nan, 1], [math.inf, 1], [True, False], [1 + 1j, 2], ["1", "2"]]
)
def test_invalid_numerical_input_is_rejected(
    data: list[float] | float | list[bool] | list[complex] | list[str],
) -> None:
    # Given nonfinite, nonnumeric or structurally invalid input.
    # When it reaches the public boundary.
    with pytest.raises(ParameterError):
        hdse(data)
    # Then invalid observations are not dropped or coerced to real values.


@pytest.mark.parametrize("value", [0, -1, True, 1.5, (), (1, 0)])
def test_embedding_constructor_rejects_invalid_geometry(value: float | tuple[int, ...]) -> None:
    # Given a malformed geometry vector.
    # When the typed config is constructed.
    with pytest.raises(ValidationError):
        EmbeddingConfig(shape=value)
    # Then invalid geometry cannot enter the core.


def test_sample_entropy_uses_one_dimensional_closed_contract() -> None:
    # Given a constant 1D input under conventional closed matching.
    # When SampEn is evaluated.
    result = sample_entropy([1, 1, 1, 1])
    # Then the self-free ratio is zero even at zero SD.
    assert result.as_float() == 0


def test_sample_entropy_rejects_spatial_data() -> None:
    # Given multidimensional input intended for HDSE.
    # When passed to the 1D compatibility API.
    with pytest.raises(ParameterError):
        sample_entropy(np.ones((4, 4)))
    # Then the input is not silently flattened.


def test_ddof_beyond_population_is_rejected() -> None:
    # Given a sample SD with no remaining degrees of freedom.
    # When matching resolves its threshold.
    with pytest.raises(ParameterError):
        hdse([1, 2, 3, 4], match=MatchConfig(ddof=4))
    # Then no NaN threshold is used.
