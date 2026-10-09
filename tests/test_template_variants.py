# Copyright (c) 2026 Daniel Ari Friedman
"""Independent ApEn/FuzzyEn/DistEn formulas and numerical range regressions."""

import itertools
import math
from typing import assert_never

import numpy as np
import pytest

from antropy_hd import (
    EmbeddingConfig,
    EntropyResult,
    MatchConfig,
    ParameterError,
    ResourceError,
    Status,
    approximate_entropy,
    distribution_entropy,
    fuzzy_entropy,
    hdse,
)
from antropy_hd.validation import threshold_for


@pytest.mark.parametrize("order", [1, 2])
def test_approximate_entropy_matches_independent_full_population(order: int) -> None:
    # Given independently constructed 1D templates with self matches included.
    data = [0, 0, 1, 0, 1, 1, 0]
    phis: list[float] = []
    for width in (order, order + 1):
        blocks = [data[start : start + width] for start in range(len(data) - width + 1)]
        proportions = [
            sum(
                max(abs(a - b) for a, b in zip(left, right, strict=True)) <= 0.5 for right in blocks
            )
            / len(blocks)
            for left in blocks
        ]
        phis.append(sum(math.log(value) for value in proportions) / len(blocks))
    # When conventional ApEn is estimated.
    result = approximate_entropy(
        data,
        embedding=EmbeddingConfig(shape=order),
        match=MatchConfig(tolerance=0.5, relative=False, closed=True),
    )
    # Then the per-template log average uses separate full origin populations.
    assert result.as_float() == pytest.approx(phis[0] - phis[1])


def test_strict_zero_radius_approximate_entropy_is_undefined() -> None:
    # Given no self matches at a strict zero threshold.
    # When strict ApEn is explicitly requested.
    result = approximate_entropy([1, 1, 1, 1], match=MatchConfig(closed=False))
    # Then logarithms of zero are explicit degeneracy.
    assert result.status == Status.UNDEFINED


@pytest.mark.parametrize("matching", [MatchConfig(theiler=1), MatchConfig(exclusion="coordinate")])
def test_approximate_entropy_rejects_pair_exclusion(matching: MatchConfig) -> None:
    # Given an exclusion incompatible with ApEn's included-self definition.
    # When it is requested.
    with pytest.raises(ParameterError):
        approximate_entropy([0, 0, 1, 0, 1], match=matching)
    # Then the unsupported option is not ignored.


@pytest.mark.parametrize("center", [False, True])
@pytest.mark.parametrize("power", [1.0, 2.0])
def test_fuzzy_entropy_matches_independent_membership(center: bool, power: float) -> None:
    # Given directly constructed paired templates and explicit membership kernel.
    data = np.array([0.0, 0.2, 0.9, 0.3, 1.0, 0.7])
    memberships: list[float] = []
    for width in (2, 3):
        blocks = [data[start : start + width] for start in range(4)]
        if center:
            blocks = [block - block.mean() for block in blocks]
        weights = [
            math.exp(-((max(abs(a - b) for a, b in zip(left, right, strict=True)) / 0.5) ** power))
            for left, right in itertools.combinations(blocks, 2)
        ]
        memberships.append(sum(weights) / len(weights))
    # When FuzzyEn evaluates the documented convention.
    result = fuzzy_entropy(
        data, match=MatchConfig(tolerance=0.5, relative=False), center=center, power=power
    )
    # Then log membership ratios agree with direct arithmetic.
    assert result.as_float() == pytest.approx(math.log(memberships[0]) - math.log(memberships[1]))


def test_log_domain_fuzzy_preserves_underflowed_memberships() -> None:
    # Given positive memberships too small to represent after exp.
    # When log-domain accumulation is used.
    result = fuzzy_entropy(
        [0, 1, 2, 4, 8],
        embedding=EmbeddingConfig(shape=1),
        match=MatchConfig(tolerance=0.001, relative=False),
        center=False,
    )
    # Then a finite log ratio survives rather than becoming zero/zero.
    assert result.status == Status.FINITE
    assert result.as_float() == pytest.approx(math.log(2), rel=1e-8)


def test_fuzzy_large_finite_centering_is_scale_invariant() -> None:
    # Given the independent review's overflowing finite field.
    # When scale-equivalent absolute kernel widths are used.
    large = fuzzy_entropy(
        [1.7e308, -1.7e308, -1.7e308, -1.7e308], match=MatchConfig(tolerance=1e308, relative=False)
    )
    small = fuzzy_entropy([1.7, -1.7, -1.7, -1.7], match=MatchConfig(tolerance=1.0, relative=False))
    # Then normalized centering preserves the finite estimate.
    assert large.as_float() == pytest.approx(small.as_float())


@pytest.mark.parametrize("center", [False, True])
def test_fuzzy_retains_small_differences_at_large_common_offset(center: bool) -> None:
    # Given representable local differences on a huge common offset.
    spacing = np.spacing(1e308)
    data = np.array([0, 1, 2, 0, 1, 0, 2, 1]) * spacing + 1e308
    matching = MatchConfig(tolerance=spacing, relative=False)
    # When translation-equivalent local templates use the same kernel radius.
    original = fuzzy_entropy(data, match=matching, center=center)
    translated = fuzzy_entropy(data - data[0], match=matching, center=center)
    # Then centering and pair distances preserve the represented local information.
    assert original.as_float() == pytest.approx(translated.as_float(), rel=1e-13)


@pytest.mark.parametrize(
    ("data", "radius"), [([1.7e308, -1.7e308], 0.1), ([1e-308, -1e-308], 1.7e308)]
)
def test_threshold_product_avoids_intermediate_overflow(data: list[float], radius: float) -> None:
    # Given a representable radius whose intermediate SD/product overflows.
    # When threshold resolution uses mantissa/exponent arithmetic.
    result = threshold_for(np.array(data), MatchConfig(ddof=1, tolerance=radius))
    # Then the final representable scale is retained.
    assert result == pytest.approx(math.sqrt(2) * (abs(data[0]) * radius))


def test_threshold_product_avoids_intermediate_underflow() -> None:
    # Given a huge scale and subnormal radius, with a small nonzero SD.
    data = np.array([1e308, np.nextafter(1e308, 0.0)])
    # When threshold resolution combines exponents before multiplication.
    threshold = threshold_for(data, MatchConfig(tolerance=1e-310))
    # Then a representable nonzero radius survives.
    assert threshold > 0


def test_nearby_huge_values_retain_true_sd_and_pair_counts() -> None:
    # Given representable tiny differences on a huge common offset.
    data = np.array([1e308, np.nextafter(1e308, 0.0)] * 3)
    config = EmbeddingConfig(shape=1)
    matching = MatchConfig(tolerance=2.0)
    # When original and translated fields are estimated.
    original = hdse(data, embedding=config, match=matching)
    translated = hdse(data - data[0], embedding=config, match=matching)
    # Then the radius and actual pair counts remain translation invariant.
    assert original.diagnostics["threshold"] == translated.diagnostics["threshold"]
    assert original.diagnostics["base_matches"] == translated.diagnostics["base_matches"] == 4


def test_complete_pair_scratch_budget_is_enforced() -> None:
    # Given blocks with overlapping yielded arrays and kernel scratch.
    # When their complete peak estimate exceeds the stated template/pair budget.
    with pytest.raises(ResourceError):
        hdse(
            np.ones(1002),
            embedding=EmbeddingConfig(max_memory_bytes=710000),
            match=MatchConfig(tolerance=1, relative=False, block_size=128),
        )
    # Then array lifetimes cannot bypass the limit.


def test_joint_template_memory_rejected_before_allocation() -> None:
    # Given the independent review's near-budget simultaneous populations.
    # When an exact HDSE request exceeds the complete workspace estimate.
    with pytest.raises(ResourceError):
        hdse(
            np.ones((30, 30)),
            embedding=EmbeddingConfig(shape=10, max_memory_bytes=715000),
            match=MatchConfig(tolerance=1, relative=False, block_size=32),
        )
    # Then the hard resource ceiling cannot be bypassed by separate guards.


def test_approximate_entropy_releases_separate_population() -> None:
    # Given a budget that supports each full population separately.
    # When ApEn evaluates them sequentially.
    result = approximate_entropy(
        np.ones((30, 30)),
        embedding=EmbeddingConfig(shape=10, max_memory_bytes=500000),
        match=MatchConfig(tolerance=1, relative=False, block_size=16),
    )
    # Then no combined population allocation is needed.
    assert result.as_float() == 0


@pytest.mark.parametrize("power", [0.0, -1.0, math.inf, math.nan])
def test_invalid_fuzzy_kernel_is_rejected(power: float) -> None:
    # Given an invalid membership exponent.
    # When it reaches the public API.
    with pytest.raises(ParameterError):
        fuzzy_entropy([0, 1, 2, 3], power=power)
    # Then no substitute kernel is used.


@pytest.mark.parametrize(
    ("data", "tolerance", "power"),
    [([1.7e308, -1.7e308, 0.0], 1.0, 0.1), ([0.0, 1.0, 2.0], 1e-200, 2.0)],
)
def test_unrepresentable_fuzzy_kernel_is_range_error(
    data: list[float], tolerance: float, power: float
) -> None:
    # Given finite input with a kernel distance or log weight beyond float64.
    # When the mathematically positive membership cannot be represented.
    with pytest.raises(ParameterError):
        fuzzy_entropy(
            data,
            embedding=EmbeddingConfig(shape=1),
            match=MatchConfig(tolerance=tolerance, relative=False),
            power=power,
            center=False,
        )
    # Then numeric range failure is not mislabeled as mathematical undefined.


def test_zero_fuzzy_width_is_tagged() -> None:
    # Given a constant field with zero relative tolerance width.
    # When fuzzy entropy is estimated.
    result = fuzzy_entropy([1, 1, 1, 1])
    # Then the kernel is undefined explicitly.
    assert result.status == Status.UNDEFINED


def test_distance_histogram_differs_from_amplitude_histogram() -> None:
    # Given three templates whose distances are 1,1,2.
    # When distance distribution entropy uses two bins on [0,1].
    result = distribution_entropy(
        [0, 1, 2], embedding=EmbeddingConfig(shape=1), bins=2, normalize=False
    )
    # Then all normalized distances lie in the high bin, producing zero.
    assert result.as_float() == 0
    assert result.diagnostics["bin_counts"] == [0, 3]


@pytest.mark.parametrize(("data", "status"), [([1, 1, 1], Status.FINITE), ([1], Status.UNDEFINED)])
def test_distance_histogram_degeneracy(data: list[int], status: Status) -> None:
    # Given identical templates or an absent pair population.
    # When distribution entropy is requested.
    result = distribution_entropy(data, embedding=EmbeddingConfig(shape=1))
    # Then degeneracy is explicit without an empty histogram division.
    assert result.status == status


def test_distribution_entropy_rejects_unused_radius() -> None:
    # Given a threshold option absent from distance-distribution entropy.
    # When supplied explicitly.
    with pytest.raises(ParameterError):
        distribution_entropy(
            [0, 1, 2], embedding=EmbeddingConfig(shape=1), match=MatchConfig(tolerance=1)
        )
    # Then scientific configuration is not silently ignored.


def test_histogram_workspace_is_reserved_before_template_allocation() -> None:
    # Given histogram buffers far larger than the complete workspace ceiling.
    # When distribution entropy is requested.
    with pytest.raises(ResourceError):
        distribution_entropy(
            [0, 1, 2], embedding=EmbeddingConfig(shape=1, max_memory_bytes=10000), bins=100000
        )
    # Then a tiny template population cannot bypass the histogram budget.


@pytest.mark.parametrize("bins", [1, 0, -1, True, 1.5, 100001])
def test_distribution_bin_domain(bins: float) -> None:
    # Given unsupported histogram resolution.
    # When parsed at the numeric boundary.
    with pytest.raises(ParameterError):
        distribution_entropy([0, 1, 2], embedding=EmbeddingConfig(shape=1), bins=bins)
    # Then allocation and normalization remain well defined.


@pytest.mark.parametrize(
    ("status", "value"), [(Status.FINITE, 0.0), (Status.UNDEFINED, None), (Status.INFINITE, None)]
)
def test_result_numeric_adapter(status: Status, value: float | None) -> None:
    # Given an explicitly tagged estimate.
    result = EntropyResult(measure="test", value=value, status=status, n_observations=2)
    # When a conventional numeric sentinel is requested.
    numeric = result.as_float()
    # Then finite/undefined/infinite distinctions are preserved.
    match status:
        case Status.FINITE:
            assert numeric == 0
        case Status.UNDEFINED:
            assert math.isnan(numeric)
        case Status.INFINITE:
            assert numeric == math.inf
        case unreachable:
            assert_never(unreachable)
