# Copyright (c) 2026 Daniel Ari Friedman
"""Bootstrap, Wilson, Holm and immutable-result boundary evidence."""

import math
from fractions import Fraction
from statistics import NormalDist

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.inference import (
    binomial_interval,
    bootstrap_interval,
    holm_adjust,
    permutation_test,
)
from antropy_hd.inference_models import (
    BootstrapConfig,
    InferenceStatus,
    IntervalResult,
    Mode,
    Pairing,
    PermutationConfig,
    PermutationResult,
)


def mean(values: list[float]) -> Fraction:
    return sum((Fraction(value) for value in values), Fraction()) / len(values)


def linear_quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


@pytest.mark.parametrize("pairing", list(Pairing))
def test_bootstrap_fraction_and_manual_quantile_oracle(pairing: Pairing) -> None:
    first = [0.1, 2.0, -3.0]
    second = [0.2, 4.0, 1.0] if pairing is Pairing.PAIRED else [0.2, 4.0]
    config = BootstrapConfig(seed=42, pairing=pairing, resamples=23, confidence_level=0.8)
    result = bootstrap_interval(first, second, config=config)
    rng = np.random.default_rng(config.seed)
    samples: list[float] = []
    for _ in range(config.resamples):
        first_indices = rng.integers(0, len(first), size=len(first))
        second_indices = (
            first_indices
            if pairing is Pairing.PAIRED
            else rng.integers(0, len(second), size=len(second))
        )
        samples.append(
            float(
                mean([second[int(i)] for i in second_indices])
                - mean([first[int(i)] for i in first_indices])
            )
        )
    tail = (1 - config.confidence_level) / 2
    assert result.estimate == float(mean(second) - mean(first))
    assert result.lower == pytest.approx(linear_quantile(samples, tail), abs=1e-15)
    assert result.upper == pytest.approx(linear_quantile(samples, 1 - tail), abs=1e-15)
    assert result.resamples == config.resamples
    assert result.resampling_work == config.resamples * (
        len(first) if pairing is Pairing.PAIRED else len(first) + len(second)
    )
    assert result == bootstrap_interval(first, second, config=config)
    assert (
        result.model_dump_json()
        == bootstrap_interval(first, second, config=config).model_dump_json()
    )


def test_paired_bootstrap_preserves_joint_pairs() -> None:
    first = [1.0, 20.0, -100.0, 0.0]
    second = [4.0, 23.0, -97.0, 3.0]
    paired = bootstrap_interval(
        first, second, config=BootstrapConfig(seed=5, pairing=Pairing.PAIRED, resamples=31)
    )
    independent = bootstrap_interval(first, second, config=BootstrapConfig(seed=5, resamples=31))
    assert paired.estimate == paired.lower == paired.upper == 3
    assert independent.lower < 3 < independent.upper


def test_bootstrap_offset_precision_constant_and_single_resample() -> None:
    spacing = np.spacing(1e308)
    first = 1e308 + spacing * np.array([0, 1, 2, 0])
    second = 1e308 + spacing * np.array([1, 0, 2, 1])
    config = BootstrapConfig(seed=15, pairing=Pairing.PAIRED, resamples=11)
    original = bootstrap_interval(first, second, config=config)
    translated = bootstrap_interval(first - first[0], second - first[0], config=config)
    assert (original.estimate, original.lower, original.upper) == (
        translated.estimate,
        translated.lower,
        translated.upper,
    )
    constant = bootstrap_interval([7, 7], [7, 7], config=BootstrapConfig(seed=4, resamples=1))
    assert constant.estimate == constant.lower == constant.upper == 0
    assert "coverage is not guaranteed" in constant.assumptions[-1]


def test_bootstrap_work_boundary_and_range_error() -> None:
    result = bootstrap_interval(
        [0, 1], [2, 3], config=BootstrapConfig(seed=0, resamples=2, max_resampling_work=8)
    )
    assert result.resampling_work == 8
    with pytest.raises(ResourceError, match="max_resampling_work"):
        bootstrap_interval(
            [0, 1], [2, 3], config=BootstrapConfig(seed=0, resamples=2, max_resampling_work=7)
        )
    with pytest.raises(ParameterError, match="effect"):
        bootstrap_interval(
            [-1e308, -1e308], [1e308, 1e308], config=BootstrapConfig(seed=0, resamples=1)
        )
    with pytest.raises(ParameterError, match="pairing"):
        bootstrap_interval(
            [0, 1], [2, 3, 4], config=BootstrapConfig(seed=0, pairing=Pairing.PAIRED)
        )


def test_bootstrap_linear_percentiles_do_not_overflow_finite_endpoints() -> None:
    result = bootstrap_interval(
        [-1e308, 1e308],
        [0.0, 0.0],
        config=BootstrapConfig(seed=49, pairing=Pairing.PAIRED, resamples=2),
    )
    assert result.estimate == 0
    assert result.lower == pytest.approx(-9.5e307)
    assert result.upper == pytest.approx(9.5e307)


@pytest.mark.parametrize("confidence", [0, 1, -0.1, math.inf, math.nan, True, False])
def test_invalid_bootstrap_confidence(confidence: float) -> None:
    with pytest.raises(ValidationError):
        BootstrapConfig(seed=0, confidence_level=confidence)


def test_wilson_analytic_one_sigma_and_zero_trials() -> None:
    confidence = 2 * NormalDist().cdf(1) - 1
    middle = binomial_interval(5, 10, confidence_level=confidence)
    expected_half = math.sqrt(0.25 / 10 + 1 / 400) / 1.1
    assert middle.estimate == 0.5
    assert middle.lower == pytest.approx(0.5 - expected_half, abs=2e-16)
    assert middle.upper == pytest.approx(0.5 + expected_half, abs=2e-16)
    none = binomial_interval(0, 10, confidence_level=confidence)
    all_success = binomial_interval(10, 10, confidence_level=confidence)
    assert none.lower == 0
    assert none.upper == pytest.approx(1 / 11)
    assert all_success.lower == pytest.approx(10 / 11)
    assert all_success.upper == 1
    undefined = binomial_interval(0, 0)
    assert undefined.status is InferenceStatus.UNDEFINED
    assert undefined.estimate is undefined.lower is undefined.upper is None
    assert '"lower":null' in undefined.model_dump_json()


def test_wilson_95_percent_reference_values_and_extreme_confidence() -> None:
    result = binomial_interval(5, 10)
    assert result.lower == pytest.approx(0.236593090512564, abs=1e-14)
    assert result.upper == pytest.approx(0.763406909487436, abs=1e-14)
    extreme = binomial_interval(5, 10, confidence_level=np.nextafter(1.0, 0.0))
    assert extreme.lower is not None
    assert extreme.upper is not None
    assert 0 < extreme.lower < extreme.upper < 1


@pytest.mark.parametrize(
    ("successes", "total"),
    [(-1, 1), (2, 1), (0, -1), (1, 0), (True, 1), (0, True), (1.0, 2), (0, 2.0)],
)
def test_invalid_binomial_counts(successes: int, total: int) -> None:
    with pytest.raises(ParameterError, match="counts"):
        binomial_interval(successes, total)


@pytest.mark.parametrize("confidence", [0, 1, -1, math.inf, math.nan, True, False, "0.95"])
def test_invalid_binomial_confidence(confidence: float) -> None:
    with pytest.raises(ParameterError, match="confidence_level"):
        binomial_interval(1, 2, confidence_level=confidence)


def test_binomial_supported_integer_range() -> None:
    with pytest.raises(ParameterError, match="total"):
        binomial_interval(0, 10**400)


def test_holm_declared_family_sort_monotonicity_and_ties() -> None:
    assert holm_adjust([0.01, 0.04, 0.03, 0.2]) == pytest.approx((0.04, 0.09, 0.09, 0.2))
    assert holm_adjust([0.2, 0.03, 0.04, 0.01]) == pytest.approx((0.2, 0.09, 0.09, 0.04))
    assert holm_adjust([0.1, 0.1, 0.1]) == pytest.approx((0.3, 0.3, 0.3))
    assert holm_adjust([0.0, 1.0]) == (0.0, 1.0)
    assert holm_adjust([0.9, 0.9]) == (1.0, 1.0)
    assert holm_adjust([]) == ()
    assert holm_adjust([0.05]) == (0.05,)
    numpy_probabilities = holm_adjust(np.array([0.1, 0.2], dtype=np.float64))
    assert numpy_probabilities == (0.2, 0.2)
    assert all(type(value) is float for value in numpy_probabilities)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -0.1, 1.1, True, "0.5", 1j])
def test_holm_rejects_invalid_family_members(bad: float) -> None:
    with pytest.raises(ParameterError, match="p_values"):
        holm_adjust([0.5, bad])


@pytest.mark.parametrize(
    "changes",
    [
        {"extreme": 100},
        {"p_value": 0.1},
        {"resolution": 0.1},
        {"allocations": 100},
        {"effective_seed": 0},
    ],
)
def test_permutation_result_rejects_inconsistent_exact_metadata(
    changes: dict[str, int | float],
) -> None:
    result = permutation_test([0, 1], [2, 3], config=PermutationConfig(seed=0))
    with pytest.raises(ValidationError):
        PermutationResult.model_validate({**result.model_dump(), **changes})


@pytest.mark.parametrize(
    "changes",
    [{"evaluated": 2, "extreme": 0, "p_value": 1 / 3, "resolution": 1 / 3}, {"effective_seed": 1}],
)
def test_permutation_result_rejects_inconsistent_monte_carlo_metadata(
    changes: dict[str, int | float],
) -> None:
    result = permutation_test(
        [0, 1], [2, 3], config=PermutationConfig(seed=0, mode=Mode.MONTE_CARLO, resamples=1)
    )
    with pytest.raises(ValidationError):
        PermutationResult.model_validate({**result.model_dump(), **changes})


@pytest.mark.parametrize(
    "changes", [{"status": "undefined"}, {"lower": None}, {"lower": 3.0, "upper": 2.0}]
)
def test_interval_result_rejects_inconsistent_bounds(
    changes: dict[str, float | str | None],
) -> None:
    result = binomial_interval(1, 2)
    with pytest.raises(ValidationError):
        IntervalResult.model_validate({**result.model_dump(), **changes})
