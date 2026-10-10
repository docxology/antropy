# Copyright (c) 2026 Daniel Ari Friedman
"""Actual fixed-alphabet counts, tie semantics and dimension-independent assignment."""

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd import SymbolizationConfig, fixed_alphabet
from antropy_hd.errors import ParameterError


@pytest.mark.parametrize("shape", [(8,), (2, 4), (2, 2, 2), (1, 2, 1, 4)])
@pytest.mark.parametrize(("side", "expected"), [("right", (1, 3, 0, 4)), ("left", (3, 1, 2, 2))])
def test_full_alphabet_and_tails(
    shape: tuple[int, ...], side: str, expected: tuple[int, ...]
) -> None:
    config = SymbolizationConfig.model_validate({"cuts": [-1, 0, 1], "side": side})
    values = np.array([-100, -1, -1, -0.5, 1, 1, 2, 100], dtype=np.float64).reshape(shape)
    result = fixed_alphabet(values, config=config)
    assert result.counts == expected
    assert result.input_shape == shape
    assert result.observations == values.size
    assert result.probabilities == tuple(count / values.size for count in expected)
    assert sum(result.probabilities) == 1
    assert len(result.counts) == len(config.cuts) + 1


@pytest.mark.parametrize("cuts", [[], [0, 0], [1, -1], [np.nan], [np.inf]])
def test_invalid_cut_geometry(cuts: list[float]) -> None:
    with pytest.raises((ValidationError, ParameterError)):
        SymbolizationConfig(cuts=tuple(cuts))


@pytest.mark.parametrize("values", [[], [np.nan], [np.inf], [1 + 1j]])
def test_reject_invalid_observations(values: list[complex]) -> None:
    with pytest.raises(ParameterError):
        fixed_alphabet(values, config=SymbolizationConfig(cuts=(0,)))


def test_fixed_cuts_are_immutable_and_unknown_keys_fail() -> None:
    with pytest.raises(ValidationError):
        SymbolizationConfig.model_validate({"cuts": [0], "fit_from_data": True})
    config = SymbolizationConfig(cuts=(0,))
    with pytest.raises(ValidationError):
        config.side = "left"
    assert fixed_alphabet([2, 3], config=config).counts == (0, 2)
