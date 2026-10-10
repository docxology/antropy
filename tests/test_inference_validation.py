# Copyright (c) 2026 Daniel Ari Friedman
"""Strict inference input, budget and immutable configuration boundaries."""

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.inference import permutation_test
from antropy_hd.inference_models import Pairing, PermutationConfig


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [1.0],
        [[1.0, 2.0]],
        [True, 1.0],
        np.array([1.0, 2.0], dtype=object),
        ["1", "2"],
        [1j, 2j],
        [1.0, np.nan],
        [1.0, np.inf],
        [[1], [2, 3]],
    ],
)
def test_invalid_groups_are_typed(bad: np.typing.ArrayLike) -> None:
    with pytest.raises(ParameterError):
        permutation_test(bad, [1.0, 2.0], config=PermutationConfig(seed=0))
    with pytest.raises(ParameterError):
        permutation_test([1.0, 2.0], bad, config=PermutationConfig(seed=0))


def test_pair_lengths_sample_limit_and_effect_range() -> None:
    with pytest.raises(ParameterError, match="pairing"):
        permutation_test(
            [1.0, 2.0], [1.0, 2.0, 3.0], config=PermutationConfig(seed=0, pairing=Pairing.PAIRED)
        )
    with pytest.raises(ResourceError, match="max_samples"):
        permutation_test(
            [1.0, 2.0], [1.0, 2.0, 3.0], config=PermutationConfig(seed=0, max_samples=4)
        )
    with pytest.raises(ParameterError, match="effect"):
        permutation_test([-1e308, -1e308], [1e308, 1e308], config=PermutationConfig(seed=0))


@pytest.mark.parametrize(
    "invalid",
    [
        {},
        {"seed": -1},
        {"seed": True},
        {"seed": 0, "mode": "bad"},
        {"seed": 0, "alternative": "bad"},
        {"seed": 0, "pairing": "bad"},
        {"seed": 0, "resamples": 0},
        {"seed": 0, "resamples": 1000001},
        {"seed": 0, "max_samples": 10001},
        {"seed": 0, "max_resampling_work": 0},
        {"seed": 0, "max_exact_allocations": 0},
        {"seed": 0, "unknown": 1},
    ],
)
def test_invalid_permutation_configs_fail(invalid: dict[str, int | str | bool]) -> None:
    with pytest.raises(ValidationError):
        PermutationConfig.model_validate(invalid)


def test_configs_and_results_are_frozen() -> None:
    config = PermutationConfig(seed=0)
    result = permutation_test([1, 2], [3, 4], config=config)
    with pytest.raises(ValidationError):
        config.seed = 1
    with pytest.raises(ValidationError):
        result.p_value = 0.1
    assert type(result.p_value) is float
    assert type(result.extreme) is int
