# Copyright (c) 2026 Daniel Ari Friedman
"""Permutation, bootstrap, binomial and familywise inference APIs."""

import math
from collections.abc import Sequence
from statistics import NormalDist
from typing import assert_never

import numpy as np
from numpy.typing import ArrayLike

from antropy_hd._inference import (
    assumptions_for,
    checked_work,
    contrast_for,
    effect_float,
    groups,
    is_extreme,
    linear_quantile,
    null_statistics,
    permutation_plan,
    work_units,
)
from antropy_hd.errors import ParameterError
from antropy_hd.inference_models import (
    BootstrapConfig,
    InferenceStatus,
    IntervalResult,
    Mode,
    Pairing,
    PermutationConfig,
    PermutationResult,
)


def permutation_test(
    first: ArrayLike, second: ArrayLike, *, config: PermutationConfig
) -> PermutationResult:
    """Test a second-minus-first mean difference using inclusive permutation tails."""
    a, b = groups(first, second, config)
    allocations, evaluated, mode, work = permutation_plan(a.size, b.size, config)
    contrast = contrast_for(a, b, config.pairing)
    effect = effect_float(contrast.observed, contrast.denominator)
    extreme = sum(
        is_extreme(null, contrast.observed, config.alternative)
        for null in null_statistics(contrast, mode, evaluated, config.seed)
    )
    exact = mode is Mode.EXACT
    denominator = evaluated if exact else evaluated + 1
    numerator = extreme if exact else extreme + 1
    return PermutationResult(
        effect=effect,
        effect_numerator=contrast.observed,
        effect_denominator=contrast.denominator,
        p_value=numerator / denominator,
        n_first=a.size,
        n_second=b.size,
        allocations=allocations,
        evaluated=evaluated,
        extreme=extreme,
        resolution=1 / denominator,
        effective_mode=mode,
        effective_seed=None if exact else config.seed,
        resampling_work=work,
        config=config,
        assumptions=assumptions_for(config.pairing),
    )


def bootstrap_interval(
    first: ArrayLike, second: ArrayLike, *, config: BootstrapConfig
) -> IntervalResult:
    """Construct a seeded percentile mean-difference interval with linear quantiles."""
    a, b = groups(first, second, config)
    work = checked_work(
        config.resamples, work_units(a.size, b.size, config.pairing), config.max_resampling_work
    )
    contrast = contrast_for(a, b, config.pairing)
    estimate = effect_float(contrast.observed, contrast.denominator)
    rng = np.random.default_rng(config.seed)
    samples = np.empty(config.resamples, dtype=np.float64)
    for index in range(config.resamples):
        first_indices = rng.integers(0, a.size, size=a.size)
        match config.pairing:
            case Pairing.INDEPENDENT:
                first_sum = sum(contrast.first[int(i)] for i in first_indices)
                second_indices = rng.integers(0, b.size, size=b.size)
                second_sum = sum(contrast.second[int(i)] for i in second_indices)
                numerator = a.size * second_sum - b.size * first_sum
            case Pairing.PAIRED:
                numerator = sum(
                    contrast.second[int(i)] - contrast.first[int(i)] for i in first_indices
                )
            case unreachable:
                assert_never(unreachable)
        samples[index] = effect_float(numerator, contrast.denominator)
    tail = (1 - config.confidence_level) / 2
    samples.sort()
    return IntervalResult(
        estimate=estimate,
        lower=linear_quantile(samples, tail),
        upper=linear_quantile(samples, 1 - tail),
        method="percentile_bootstrap",
        confidence_level=config.confidence_level,
        n_observations=a.size + b.size,
        resamples=config.resamples,
        resampling_work=work,
        config=config,
        assumptions=(
            "independent observational units sampled from the target population",
            "resample pairs jointly when paired; groups separately when independent",
            "percentile coverage is not guaranteed for small, discrete or degenerate samples",
        ),
    )


def binomial_interval(
    successes: int, total: int, *, confidence_level: float = 0.95
) -> IntervalResult:
    """Return the Wilson score interval; zero trials carry explicit undefined bounds."""
    if (
        isinstance(successes, bool)
        or isinstance(total, bool)
        or not isinstance(successes, int)
        or not isinstance(total, int)
    ):
        raise ParameterError("counts", "successes and total must be integers, excluding booleans")
    if total < 0 or successes < 0 or successes > total:
        raise ParameterError("counts", "requires 0 <= successes <= total")
    if (
        isinstance(confidence_level, (bool, np.bool_))
        or not isinstance(confidence_level, (int, float, np.floating, np.integer))
        or not math.isfinite(confidence_level)
        or not 0 < confidence_level < 1
    ):
        raise ParameterError(
            "confidence_level", "requires a finite probability strictly between zero and one"
        )
    assumptions = ("independent Bernoulli trials with a common success probability",)
    if total == 0:
        return IntervalResult(
            estimate=None,
            lower=None,
            upper=None,
            status=InferenceStatus.UNDEFINED,
            method="wilson",
            confidence_level=confidence_level,
            n_observations=0,
            assumptions=assumptions,
        )
    z = -NormalDist().inv_cdf((1 - confidence_level) / 2)
    proportion = successes / total
    try:
        inverse_total = 1.0 / total
    except OverflowError as error:
        raise ParameterError("total", "trial count exceeds the supported binary64 range") from error
    adjustment = z * z * inverse_total
    denominator = 1 + adjustment
    center = (proportion + adjustment / 2) / denominator
    half_width = (
        z
        * math.sqrt(proportion * (1 - proportion) * inverse_total + adjustment * inverse_total / 4)
        / denominator
    )
    return IntervalResult(
        estimate=proportion,
        lower=0.0 if successes == 0 else max(0.0, center - half_width),
        upper=1.0 if successes == total else min(1.0, center + half_width),
        method="wilson",
        confidence_level=confidence_level,
        n_observations=total,
        assumptions=assumptions,
    )


def holm_adjust(p_values: Sequence[float]) -> tuple[float, ...]:
    """Adjust a finite declared family of p-values, retaining the original order."""
    values = tuple(p_values)
    for value in values:
        if (
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, float, np.floating, np.integer))
            or not math.isfinite(value)
            or not 0 <= value <= 1
        ):
            raise ParameterError(
                "p_values", "requires finite probabilities in [0, 1], excluding booleans"
            )
    probabilities = tuple(float(value) for value in values)
    adjusted = [0.0] * len(probabilities)
    running = 0.0
    for rank, index in enumerate(sorted(range(len(probabilities)), key=lambda i: probabilities[i])):
        running = max(running, min(1.0, (len(probabilities) - rank) * probabilities[index]))
        adjusted[index] = running
    return tuple(adjusted)
