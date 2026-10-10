# Copyright (c) 2026 Daniel Ari Friedman
"""Bounded allocation streams and exact binary64 contrast arithmetic."""

import math
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
from typing import Literal, assert_never

import numpy as np
from numpy.typing import ArrayLike, NDArray

from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.inference_models import (
    Alternative,
    Mode,
    Pairing,
    PermutationConfig,
    ResamplingConfig,
)
from antropy_hd.validation import as_real_array


@dataclass(frozen=True, slots=True)
class Contrast:
    """Aligned integer observations with one common statistic denominator."""

    first: tuple[int, ...]
    second: tuple[int, ...]
    denominator: int
    observed: int
    pairing: Pairing
    pooled_sum: int
    pooled: tuple[int, ...]

    def independent_statistic(self, indices: tuple[int, ...]) -> int:
        """Compute second-minus-first without floating summation order effects."""
        return len(self.first) * self.pooled_sum - len(self.pooled) * sum(
            self.pooled[i] for i in indices
        )

    def paired_statistic(self, signs: tuple[int, ...]) -> int:
        """Compute an exact contrast after within-pair label exchanges."""
        return sum(
            sign * (b - a) for sign, a, b in zip(signs, self.first, self.second, strict=True)
        )


def groups(
    first: ArrayLike, second: ArrayLike, config: ResamplingConfig
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Validate finite one-dimensional groups without coercing boolean observations."""
    arrays: list[NDArray[np.float64]] = []
    for name, data in (("first", first), ("second", second)):
        try:
            raw = np.asarray(data, dtype=object)
            if any(isinstance(value, (bool, np.bool_)) for value in raw.flat):
                raise ParameterError(name, "boolean observations are not supported")
            array = as_real_array(data)
        except (TypeError, ValueError, OverflowError) as error:
            raise ParameterError(name, str(error)) from error
        if array.ndim != 1 or array.size < 2:
            raise ParameterError(
                name, "requires a one-dimensional group with at least two observations"
            )
        arrays.append(array)
    a, b = arrays
    if config.pairing is Pairing.PAIRED and a.size != b.size:
        raise ParameterError("pairing", "paired groups require equal lengths")
    if a.size + b.size > config.max_samples:
        raise ResourceError("max_samples", "total group size exceeds the configured limit")
    return a, b


def work_units(n_first: int, n_second: int, pairing: Pairing) -> int:
    """Conservative observation visits per draw, not a time or RSS estimate."""
    match pairing:
        case Pairing.INDEPENDENT:
            return n_first + n_second
        case Pairing.PAIRED:
            return n_first
        case unreachable:
            assert_never(unreachable)


def checked_work(evaluations: int, units: int, limit: int) -> int:
    """Reject resampling plans before constructing allocation streams or RNGs."""
    work = evaluations * units
    if work > limit:
        raise ResourceError(
            "max_resampling_work", f"requires {work} observation visits; limit is {limit}"
        )
    return work


def permutation_plan(
    n_first: int, n_second: int, config: PermutationConfig
) -> tuple[int, int, Literal[Mode.EXACT, Mode.MONTE_CARLO], int]:
    """Resolve exact feasibility before exact integer encoding or resampling."""
    allocations = (
        math.comb(n_first + n_second, n_first)
        if config.pairing is Pairing.INDEPENDENT
        else 2**n_first
    )
    units = work_units(n_first, n_second, config.pairing)
    feasible = (
        allocations <= config.max_exact_allocations
        and allocations * units <= config.max_resampling_work
    )
    match config.mode:
        case Mode.AUTO:
            mode = Mode.EXACT if feasible else Mode.MONTE_CARLO
        case Mode.EXACT:
            if allocations > config.max_exact_allocations:
                raise ResourceError("max_exact_allocations", f"requires {allocations} allocations")
            mode = Mode.EXACT
        case Mode.MONTE_CARLO:
            mode = Mode.MONTE_CARLO
        case unreachable:
            assert_never(unreachable)
    evaluated = allocations if mode is Mode.EXACT else config.resamples
    work = checked_work(evaluated, units, config.max_resampling_work)
    return allocations, evaluated, mode, work


def contrast_for(
    first: NDArray[np.float64], second: NDArray[np.float64], pairing: Pairing
) -> Contrast:
    """Align finite IEEE-754 observations over a power-of-two denominator."""
    ratios = tuple(float(value).as_integer_ratio() for value in (*first, *second))
    denominator = max(den for _, den in ratios)
    integers = tuple(num * (denominator // den) for num, den in ratios)
    a, b = integers[: first.size], integers[first.size :]
    match pairing:
        case Pairing.INDEPENDENT:
            observed = len(a) * sum(b) - len(b) * sum(a)
            statistic_denominator = denominator * len(a) * len(b)
        case Pairing.PAIRED:
            observed = sum(b) - sum(a)
            statistic_denominator = denominator * len(a)
        case unreachable:
            assert_never(unreachable)
    return Contrast(a, b, statistic_denominator, observed, pairing, sum(a) + sum(b), integers)


def effect_float(numerator: int, denominator: int) -> float:
    """Round the exact contrast once; reject an unrepresentable finite effect."""
    try:
        return float(Fraction(numerator, denominator))
    except OverflowError as error:
        raise ParameterError("effect", "mean difference exceeds the binary64 range") from error


def linear_quantile(sorted_samples: NDArray[np.float64], probability: float) -> float:
    """Interpolate ordered finite endpoints without overflowing their difference."""
    position = (sorted_samples.size - 1) * probability
    lower = math.floor(position)
    upper = min(lower + 1, sorted_samples.size - 1)
    weight = Fraction(position - lower)
    value = (
        Fraction(float(sorted_samples[lower])) * (1 - weight)
        + Fraction(float(sorted_samples[upper])) * weight
    )
    return effect_float(value.numerator, value.denominator)


def null_statistics(
    contrast: Contrast,
    mode: Literal[Mode.EXACT, Mode.MONTE_CARLO],
    evaluated: int,
    seed: int,
) -> Iterator[int]:
    """Stream exhaustive allocations or independent uniform draws with replacement."""
    n_first = len(contrast.first)
    n_total = n_first + len(contrast.second)
    if mode is Mode.EXACT:
        match contrast.pairing:
            case Pairing.INDEPENDENT:
                for indices in combinations(range(n_total), n_first):
                    yield contrast.independent_statistic(indices)
            case Pairing.PAIRED:
                for signs in product((-1, 1), repeat=n_first):
                    yield contrast.paired_statistic(signs)
            case unreachable:
                assert_never(unreachable)
        return
    rng = np.random.default_rng(seed)
    for _ in range(evaluated):
        match contrast.pairing:
            case Pairing.INDEPENDENT:
                chosen = rng.choice(n_total, size=n_first, replace=False)
                yield contrast.independent_statistic(tuple(int(index) for index in chosen))
            case Pairing.PAIRED:
                chosen = rng.integers(0, 2, size=n_first)
                yield contrast.paired_statistic(tuple(2 * int(sign) - 1 for sign in chosen))
            case unreachable:
                assert_never(unreachable)


def is_extreme(null: int, observed: int, alternative: Alternative) -> bool:
    """Compare rational contrasts inclusively without an epsilon or widened tail."""
    match alternative:
        case Alternative.TWO_SIDED:
            return abs(null) >= abs(observed)
        case Alternative.GREATER:
            return null >= observed
        case Alternative.LESS:
            return null <= observed
        case unreachable:
            assert_never(unreachable)


def assumptions_for(pairing: Pairing) -> tuple[str, ...]:
    """Declare exchangeability at the observational unit actually resampled."""
    match pairing:
        case Pairing.INDEPENDENT:
            return ("independent observations exchangeable across group labels under the null",)
        case Pairing.PAIRED:
            return ("independent pairs with exchangeable within-pair labels under the null",)
        case unreachable:
            assert_never(unreachable)
