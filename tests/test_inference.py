# Copyright (c) 2026 Daniel Ari Friedman
"""Permutation evidence against independent rational enumeration oracles."""

import itertools
import math
from fractions import Fraction

import numpy as np
import pytest

from antropy_hd.errors import ResourceError
from antropy_hd.inference import permutation_test
from antropy_hd.inference_models import Alternative, Mode, Pairing, PermutationConfig


def mean(values: list[float]) -> Fraction:
    return sum((Fraction(value) for value in values), Fraction()) / len(values)


def tail(null: Fraction, observed: Fraction, alternative: Alternative) -> bool:
    if alternative == Alternative.TWO_SIDED:
        return abs(null) >= abs(observed)
    if alternative == Alternative.GREATER:
        return null >= observed
    return null <= observed


@pytest.mark.parametrize("alternative", list(Alternative))
@pytest.mark.parametrize(
    ("first", "second"), [([0.1, 2.3], [1.2, 3.0, 7.7]), ([0.0, 0.0], [0.0, 1.0])]
)
def test_independent_exact_fraction_oracle(
    first: list[float], second: list[float], alternative: Alternative
) -> None:
    result = permutation_test(
        first, second, config=PermutationConfig(seed=3, mode=Mode.EXACT, alternative=alternative)
    )
    pool = first + second
    observed = mean(second) - mean(first)
    nulls: list[Fraction] = []
    for indices in itertools.combinations(range(len(pool)), len(first)):
        chosen = set(indices)
        a = [value for i, value in enumerate(pool) if i in chosen]
        b = [value for i, value in enumerate(pool) if i not in chosen]
        nulls.append(mean(b) - mean(a))
    count = sum(tail(value, observed, alternative) for value in nulls)
    assert result.effect == float(observed)
    assert Fraction(result.effect_numerator, result.effect_denominator) == observed
    assert result.extreme == count
    assert result.evaluated == len(nulls) == math.comb(len(pool), len(first))
    assert result.p_value == count / len(nulls)
    assert result.resolution == 1 / len(nulls)
    assert result.effective_seed is None
    assert result.resampling_work == len(pool) * len(nulls)


@pytest.mark.parametrize("alternative", list(Alternative))
def test_paired_exact_sign_oracle(alternative: Alternative) -> None:
    first, second = [0.1, 2.0, -3.0], [0.2, 4.0, -3.0]
    observed = mean(second) - mean(first)
    differences = [Fraction(b) - Fraction(a) for a, b in zip(first, second, strict=True)]
    nulls = [
        sum(
            (sign * difference for sign, difference in zip(signs, differences, strict=True)),
            Fraction(),
        )
        / 3
        for signs in itertools.product((-1, 1), repeat=3)
    ]
    result = permutation_test(
        first,
        second,
        config=PermutationConfig(
            seed=7, pairing=Pairing.PAIRED, alternative=alternative, mode=Mode.EXACT
        ),
    )
    assert result.extreme == sum(tail(value, observed, alternative) for value in nulls)
    assert result.allocations == result.evaluated == 8
    assert result.p_value == result.extreme / 8
    assert result.resampling_work == 24
    assert "within-pair" in result.assumptions[0]


@pytest.mark.parametrize("pairing", list(Pairing))
@pytest.mark.parametrize("alternative", list(Alternative))
def test_monte_carlo_uniform_draws_fraction_oracle(
    pairing: Pairing, alternative: Alternative
) -> None:
    first, second = [0.1, 2.0, -3.0], [0.2, 4.0, 1.0]
    config = PermutationConfig(
        seed=31, pairing=pairing, alternative=alternative, mode=Mode.MONTE_CARLO, resamples=17
    )
    result = permutation_test(first, second, config=config)
    rng = np.random.default_rng(config.seed)
    observed = mean(second) - mean(first)
    count = 0
    for _ in range(config.resamples):
        if pairing is Pairing.INDEPENDENT:
            chosen = {int(i) for i in rng.choice(6, size=3, replace=False)}
            pool = first + second
            null = mean([value for i, value in enumerate(pool) if i not in chosen]) - mean(
                [value for i, value in enumerate(pool) if i in chosen]
            )
        else:
            signs = rng.integers(0, 2, size=3)
            null = (
                sum(
                    (
                        (2 * int(sign) - 1) * (Fraction(b) - Fraction(a))
                        for sign, a, b in zip(signs, first, second, strict=True)
                    ),
                    Fraction(),
                )
                / 3
            )
        count += tail(null, observed, alternative)
    assert result.extreme == count
    assert result.p_value == (count + 1) / 18
    assert result.effective_seed == config.seed
    assert result == permutation_test(first, second, config=config)
    assert (
        result.model_dump_json() == permutation_test(first, second, config=config).model_dump_json()
    )


def test_monte_carlo_no_zero_p_value_and_effect_direction() -> None:
    result = permutation_test(
        [0.0, 0.0, 0.0],
        [10.0, 10.0, 10.0],
        config=PermutationConfig(
            seed=0, mode=Mode.MONTE_CARLO, alternative=Alternative.GREATER, resamples=1
        ),
    )
    assert result.extreme == 0
    assert result.p_value == result.resolution == 0.5
    assert result.effect == 10
    reversed_result = permutation_test(
        [10.0, 10.0, 10.0],
        [0.0, 0.0, 0.0],
        config=PermutationConfig(
            seed=0, mode=Mode.MONTE_CARLO, alternative=Alternative.LESS, resamples=1
        ),
    )
    assert reversed_result.effect == -10
    assert reversed_result.p_value == result.p_value


@pytest.mark.parametrize("mode", [Mode.EXACT, Mode.MONTE_CARLO])
@pytest.mark.parametrize("pairing", list(Pairing))
@pytest.mark.parametrize("alternative", list(Alternative))
def test_constants_count_every_tie(mode: Mode, pairing: Pairing, alternative: Alternative) -> None:
    result = permutation_test(
        [7.0, 7.0],
        [7.0, 7.0],
        config=PermutationConfig(
            seed=1, mode=mode, pairing=pairing, alternative=alternative, resamples=5
        ),
    )
    assert result.effect == 0
    assert result.p_value == 1
    assert result.extreme == result.evaluated


@pytest.mark.parametrize("pairing", list(Pairing))
def test_exact_binary64_tails_preserve_offset_and_order(pairing: Pairing) -> None:
    spacing = np.spacing(1e308)
    data = 1e308 + spacing * np.array([0, 1, 2, 0, 1, 0, 2, 1])
    shifted = data - data[0]
    config = PermutationConfig(seed=5, mode=Mode.EXACT, pairing=pairing)
    original = permutation_test(data[:4], data[4:], config=config)
    translated = permutation_test(shifted[:4], shifted[4:], config=config)
    reordered = permutation_test(data[:4][::-1], data[4:][::-1], config=config)
    assert original.effect == translated.effect == reordered.effect
    assert original.p_value == translated.p_value == reordered.p_value
    assert original.extreme == translated.extreme == reordered.extreme


def test_subnormal_contrast_is_preserved() -> None:
    tiny = np.nextafter(0.0, 1.0)
    result = permutation_test(
        [0.0, 0.0],
        [tiny, tiny],
        config=PermutationConfig(seed=2, mode=Mode.EXACT, alternative=Alternative.GREATER),
    )
    assert result.effect == tiny
    assert result.p_value == 1 / 6


def test_auto_limits_and_exact_work_boundary() -> None:
    a, b = [0.0, 1.0], [2.0, 3.0]
    exact = permutation_test(
        a, b, config=PermutationConfig(seed=0, max_exact_allocations=6, max_resampling_work=24)
    )
    assert exact.effective_mode is Mode.EXACT
    for limits in ({"max_exact_allocations": 5}, {"max_resampling_work": 23}):
        monte_carlo = permutation_test(
            a, b, config=PermutationConfig(seed=0, resamples=2, **limits)
        )
        assert monte_carlo.effective_mode is Mode.MONTE_CARLO
    with pytest.raises(ResourceError, match="max_exact_allocations"):
        permutation_test(
            a, b, config=PermutationConfig(seed=0, mode=Mode.EXACT, max_exact_allocations=5)
        )
    with pytest.raises(ResourceError, match="max_resampling_work"):
        permutation_test(
            a, b, config=PermutationConfig(seed=0, mode=Mode.EXACT, max_resampling_work=23)
        )
    accepted = permutation_test(
        a,
        b,
        config=PermutationConfig(seed=0, mode=Mode.MONTE_CARLO, resamples=2, max_resampling_work=8),
    )
    assert accepted.resampling_work == 8
    with pytest.raises(ResourceError, match="max_resampling_work"):
        permutation_test(
            a,
            b,
            config=PermutationConfig(
                seed=0, mode=Mode.MONTE_CARLO, resamples=2, max_resampling_work=7
            ),
        )


def test_infeasible_exact_space_fails_without_enumeration() -> None:
    with pytest.raises(ResourceError, match="max_exact_allocations"):
        permutation_test(
            np.arange(50), np.arange(50), config=PermutationConfig(seed=2, mode=Mode.EXACT)
        )
