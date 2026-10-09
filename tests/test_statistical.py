# Copyright (c) 2026 Daniel Ari Friedman
"""Independent finite-alphabet statistical-complexity oracles and failure controls."""

import math
from decimal import Decimal, localcontext

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError
from antropy_hd.statistical import StatisticalComplexityConfig, statistical_complexity


@pytest.mark.parametrize("size", [2, 3, 4, 10])
def test_complexity_when_alphabet_is_uniform_is_zero(size: int) -> None:
    # Given a uniform distribution on its full declared alphabet.
    probabilities = np.full(size, 1 / size)
    # When statistical complexity is computed.
    result = statistical_complexity(
        probabilities, config=StatisticalComplexityConfig(alphabet_size=size)
    )
    # Then maximal entropy has no disequilibrium and thus zero complexity.
    assert result.value == pytest.approx(0, abs=1e-14)
    assert result.diagnostics["normalized_entropy"] == pytest.approx(1)


@pytest.mark.parametrize("size", [2, 3, 4, 10])
def test_complexity_when_distribution_is_delta_is_zero(size: int) -> None:
    # Given a delta mass on a full alphabet with retained zero-probability cells.
    probabilities = [1] + [0] * (size - 1)
    # When statistical complexity is computed.
    result = statistical_complexity(
        probabilities, config=StatisticalComplexityConfig(alphabet_size=size)
    )
    # Then zero entropy combines with unit normalized disequilibrium.
    assert result.value == 0
    assert result.diagnostics["normalized_disequilibrium"] == pytest.approx(1)


def test_complexity_when_binary_probabilities_are_intermediate_matches_analytic_oracle() -> None:
    # Given (3/4,1/4), with independently evaluated binary entropies.
    entropy = -(3 / 4) * math.log2(3 / 4) - (1 / 4) * math.log2(1 / 4)
    mixture_entropy = -(5 / 8) * math.log2(5 / 8) - (3 / 8) * math.log2(3 / 8)
    delta_mixture_entropy = -(3 / 4) * math.log2(3 / 4) - (1 / 4) * math.log2(1 / 4)
    expected = entropy * (mixture_entropy - entropy / 2 - 1 / 2) / (delta_mixture_entropy - 1 / 2)
    # When the fixed binary alphabet is analyzed.
    result = statistical_complexity(
        [0.75, 0.25], config=StatisticalComplexityConfig(alphabet_size=2)
    )
    # Then the normalized entropy-divergence product matches the analytic answer.
    assert result.value == pytest.approx(expected)


def test_complexity_when_distribution_is_near_uniform_preserves_decimal_oracle_value() -> None:
    # Given an independently evaluated 80-digit fixed-alphabet complexity close to equilibrium.
    probabilities = [0.5 + 1e-8, 0.5 - 1e-8]
    with localcontext() as context:
        context.prec = 80
        parsed = [Decimal(value) for value in probabilities]
        parsed = [value / sum(parsed) for value in parsed]
        entropy = -sum(value * value.ln() for value in parsed)
        uniform_entropy = Decimal(2).ln()
        mixture = [(value + Decimal("0.5")) / 2 for value in parsed]
        divergence = -sum(value * value.ln() for value in mixture) - (entropy + uniform_entropy) / 2
        maximum = (
            -Decimal("0.75") * Decimal("0.75").ln()
            - Decimal("0.25") * Decimal("0.25").ln()
            - uniform_entropy / 2
        )
        expected = float(entropy / uniform_entropy * divergence / maximum)
    # When the shared stable JS primitive evaluates the float64 input.
    result = statistical_complexity(
        probabilities, config=StatisticalComplexityConfig(alphabet_size=2)
    )
    # Then a small representable complexity value remains accurate.
    assert result.value == pytest.approx(expected, rel=1e-8, abs=0)


def test_complexity_when_alphabet_includes_unoccupied_cells_keeps_the_reference() -> None:
    # Given two occupied cells in a declared four-cell alphabet.
    probabilities = [0.5, 0.5, 0, 0]
    mixture_entropy = -2 * (3 / 8) * math.log2(3 / 8) - 2 * (1 / 8) * math.log2(1 / 8)
    delta_entropy = -(5 / 8) * math.log2(5 / 8) - 3 * (1 / 8) * math.log2(1 / 8)
    expected = (1 / 2) * (mixture_entropy - 3 / 2) / (delta_entropy - 1)
    # When zero cells are retained in the alphabet and uniform reference.
    result = statistical_complexity(
        probabilities, config=StatisticalComplexityConfig(alphabet_size=4)
    )
    # Then the occupied subset's apparent uniformity does not erase disequilibrium.
    assert result.value == pytest.approx(expected)
    assert result.value is not None
    assert result.value > 0


def test_complexity_when_units_change_preserves_the_normalized_product() -> None:
    # Given the same fixed alphabet in natural rather than binary units.
    expected = statistical_complexity(
        [0.5, 0.25, 0.25], config=StatisticalComplexityConfig(alphabet_size=3)
    ).value
    # When both factors are converted to natural units before normalization.
    result = statistical_complexity(
        [0.5, 0.25, 0.25], config=StatisticalComplexityConfig(alphabet_size=3, base=math.e)
    )
    # Then the dimensionless normalized product is unchanged.
    assert result.value == pytest.approx(expected)


def test_complexity_when_cell_order_and_tensor_shape_change_preserves_value() -> None:
    # Given a fixed four-cell distribution under reshaping and relabeling.
    expected = statistical_complexity(
        [0.5, 0.25, 0.25, 0], config=StatisticalComplexityConfig(alphabet_size=4)
    ).value
    # When cell probabilities are arranged in a two-dimensional tensor.
    result = statistical_complexity(
        [[0, 0.25], [0.5, 0.25]], config=StatisticalComplexityConfig(alphabet_size=4)
    )
    # Then the reference depends on alphabet size rather than storage layout.
    assert result.value == pytest.approx(expected)


@pytest.mark.parametrize(
    "probabilities", [[-0.1, 1.1], [0, 0], [2, 2], [math.nan, 1], [math.inf, 0], [1]]
)
def test_complexity_when_probability_domain_is_invalid_rejects_it(
    probabilities: list[float],
) -> None:
    # Given a signed, nonfinite, unnormalized or incorrectly declared alphabet.
    # When it crosses the numerical boundary.
    # Then no counts normalization or alphabet collapse is performed.
    with pytest.raises(ParameterError):
        statistical_complexity(probabilities, config=StatisticalComplexityConfig(alphabet_size=2))


@pytest.mark.parametrize("size", [0, 1, True, 2.5])
def test_complexity_when_declared_alphabet_is_invalid_rejects_it(size: float) -> None:
    # Given a degenerate or noninteger declared alphabet.
    # When the frozen configuration is constructed.
    # Then an undefined normalization is rejected before numerical work.
    with pytest.raises(ValidationError):
        StatisticalComplexityConfig(alphabet_size=size)


def test_complexity_when_declared_alphabet_drops_zero_cells_rejects_it() -> None:
    # Given four actual cells but a declared count of only two occupied cells.
    # When fixed-alphabet complexity is requested.
    # Then silently dropping zero cells cannot change the uniform reference.
    with pytest.raises(ParameterError, match="alphabet_size"):
        statistical_complexity(
            [0.5, 0.5, 0, 0], config=StatisticalComplexityConfig(alphabet_size=2)
        )
