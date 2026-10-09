# Copyright (c) 2026 Daniel Ari Friedman
"""Known distributions and rejection controls for discrete information measures."""

import math
from collections.abc import Callable
from decimal import Decimal, localcontext

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.information import (
    conditional_entropy,
    histogram_entropy,
    jensen_shannon_divergence,
    joint_entropy,
    mutual_information,
    renyi_entropy,
    shannon_entropy,
    tsallis_entropy,
)
from antropy_hd.models import EntropyResult, Status


@pytest.mark.parametrize(
    ("probabilities", "expected"), [([0.5, 0.25, 0.25], 1.5), ([1, 0], 0), ([0.25] * 4, 2)]
)
def test_shannon_when_distribution_has_known_entropy(
    probabilities: list[float], expected: float
) -> None:
    # Given a hand-computable distribution.
    # When its entropy is computed.
    result = shannon_entropy(probabilities)
    # Then the answer is in bits.
    assert result.value == pytest.approx(expected)


@pytest.mark.parametrize(
    ("order", "expected"), [(0, math.log2(3)), (1, 1.5), (2, math.log2(8 / 3)), (math.inf, 1)]
)
def test_renyi_when_order_has_known_answer(order: float, expected: float) -> None:
    # Given probabilities with collision sum 3/8.
    probabilities = [0.5, 0.25, 0.25, 0.0]
    # When the requested order is evaluated.
    result = renyi_entropy(probabilities, order=order)
    # Then it agrees with the independent formula or limiting answer.
    assert result.value == pytest.approx(expected)


@pytest.mark.parametrize(("order", "expected"), [(0, 2), (1, 1.5 * math.log(2)), (2, 0.625)])
def test_tsallis_when_order_has_known_answer(order: float, expected: float) -> None:
    # Given a hand-computable distribution.
    probabilities = [0.5, 0.25, 0.25, 0]
    # When Tsallis entropy is evaluated with k=1.
    result = tsallis_entropy(probabilities, order=order)
    # Then it agrees with its natural-unit definition.
    assert result.value == pytest.approx(expected)


@pytest.mark.parametrize("offset", [1e-12, -1e-12, 5e-5, -5e-5])
def test_renyi_when_order_nearly_one_is_stable(offset: float) -> None:
    # Given a nonuniform distribution and an order close to one.
    probabilities = [0.5, 0.25, 0.25]
    # When the near-limit branch is evaluated.
    result = renyi_entropy(probabilities, order=1 + offset)
    # Then continuity holds with an analytically bounded first-order change.
    assert result.value == pytest.approx(1.5, abs=2e-5)


@pytest.mark.parametrize("offset", [1e-12, -1e-12, 5e-5, -5e-5])
def test_tsallis_when_order_nearly_one_is_stable(offset: float) -> None:
    # Given a nonuniform distribution and an order close to one.
    probabilities = [0.5, 0.25, 0.25]
    # When the near-limit branch is evaluated.
    result = tsallis_entropy(probabilities, order=1 + offset)
    # Then continuity holds in natural units.
    assert result.value == pytest.approx(1.5 * math.log(2), abs=4e-5)


def test_renyi_when_order_is_extreme_retains_finite_min_entropy() -> None:
    # Given finite probabilities and the largest float order.
    order = np.finfo(np.float64).max
    # When Rényi entropy is computed without forming p**q.
    result = renyi_entropy([0.75, 0.25], order=order)
    # Then the result approaches the independently known min entropy.
    assert result.value == pytest.approx(-math.log2(0.75))


def test_tsallis_when_probability_is_subnormal_avoids_intermediate_overflow() -> None:
    # Given an extremely small positive probability.
    probabilities = [1.0, 1e-320]
    # When an order below one is evaluated.
    result = tsallis_entropy(probabilities, order=0.5)
    # Then the finite sum of square-root masses remains representable.
    assert result.value == pytest.approx(2 * math.sqrt(1e-320), rel=1e-12, abs=0)


def test_shannon_when_base_is_natural_reports_natural_units() -> None:
    # Given a fair binary alphabet with natural-log entropy ln(2).
    probabilities = [0.5, 0.5]
    # When natural logarithms are selected.
    result = shannon_entropy(probabilities, base=math.e)
    # Then unit conversion is explicit and correct.
    assert result.value == pytest.approx(math.log(2))


def test_shannon_when_probability_shape_changes_preserves_alphabet_entropy() -> None:
    # Given four cell probabilities with entropy 7/4 bits.
    probabilities = np.array([[0.5, 0.25], [0.125, 0.125]])
    # When tensor cells are treated as one joint alphabet.
    result = shannon_entropy(probabilities)
    # Then tensor storage shape does not invent probability-variable independence.
    assert result.value == pytest.approx(1.75)


def test_tsallis_when_order_is_extreme_has_representable_small_value() -> None:
    # Given equal masses and an order near the float64 maximum.
    order = 1e308
    # When large-order power contributions saturate to zero.
    result = tsallis_entropy([0.5, 0.5], order=order)
    # Then entropy is approximately 1/(q-1), without nonfinite intermediates escaping.
    assert result.value == pytest.approx(1e-308, rel=1e-12, abs=0)


def test_histogram_when_auto_edges_cannot_resolve_float_spacing_rejects_it() -> None:
    # Given a constant amplitude whose unit-width default range is unrepresentable.
    data = [1e308, 1e308]
    # When NumPy's automatic bin geometry cannot separate finite boundaries.
    # Then the failure is reported explicitly instead of returning invented counts.
    with pytest.raises(ParameterError):
        histogram_entropy(data, bins=4)


def test_normalization_when_alphabet_includes_zero_mass_cells() -> None:
    # Given two occupied cells within an alphabet of four.
    probabilities = [0.5, 0.5, 0, 0]
    # When Shannon entropy is normalized by the declared alphabet.
    result = shannon_entropy(probabilities, normalize=True)
    # Then one bit is half the two-bit maximum.
    assert result.value == pytest.approx(0.5)


@pytest.mark.parametrize("measure", [shannon_entropy, renyi_entropy, tsallis_entropy])
def test_normalization_when_alphabet_is_singleton_is_undefined(
    measure: Callable[..., EntropyResult],
) -> None:
    # Given an alphabet whose entropy maximum is zero.
    probabilities = [1]
    # When division by the maximum is requested.
    result = measure(probabilities, normalize=True)
    # Then the undefined normalization is explicit and JSON-safe.
    assert result.status is Status.UNDEFINED
    assert result.value is None


@pytest.mark.parametrize("measure", [shannon_entropy, renyi_entropy, tsallis_entropy])
def test_normalization_when_alphabet_is_uniform_has_unit_value(
    measure: Callable[..., EntropyResult],
) -> None:
    # Given a uniform alphabet of four cells.
    probabilities = [0.25] * 4
    # When normalized entropy is evaluated.
    result = measure(probabilities, normalize=True)
    # Then the entropy attains its own maximum.
    assert result.value == pytest.approx(1)


@pytest.mark.parametrize(
    "probabilities", [[2, 2], [0, 0], [-0.5, 1.5], [0.1, 0.2], [math.nan, 1], []]
)
def test_shannon_when_input_is_not_a_distribution_rejects_it(probabilities: list[float]) -> None:
    # Given data that cannot represent a finite probability distribution.
    # When it crosses the probability boundary.
    # Then it must fail rather than normalizing counts or dropping invalid cells.
    with pytest.raises(ParameterError):
        shannon_entropy(probabilities)


@pytest.mark.parametrize("base", [1, 0, -2, math.inf, math.nan, True, "2"])
def test_shannon_when_base_is_invalid_rejects_it(base: float | str) -> None:
    # Given an invalid logarithmic unit specification.
    # When it crosses the options boundary.
    # Then the typed validator rejects the request.
    with pytest.raises(ValidationError):
        shannon_entropy([0.5, 0.5], base=base)


@pytest.mark.parametrize("order", [-1, math.nan, True, "2"])
@pytest.mark.parametrize("measure", [renyi_entropy, tsallis_entropy])
def test_order_when_invalid_is_rejected(
    measure: Callable[..., EntropyResult], order: float | str
) -> None:
    # Given a nonnumeric or negative order.
    # When a generalized entropy is requested.
    # Then the boundary rejects it.
    with pytest.raises(ValidationError):
        measure([0.5, 0.5], order=order)


def test_tsallis_when_infinite_order_is_requested_rejects_it() -> None:
    # Given an unsupported infinite order.
    # When Tsallis entropy is requested.
    # Then a typed domain failure names the unsupported parameter.
    with pytest.raises(ParameterError, match="order"):
        tsallis_entropy([0.5, 0.5], order=math.inf)


def test_histogram_when_data_is_spatial_pools_only_amplitudes() -> None:
    # Given amplitudes with counts (1,2,1) in explicit intervals.
    array = np.array([[0, 1], [1, 3]])
    # When amplitude histogram entropy is requested.
    result = histogram_entropy(array, bins=[0, 1, 2, 3])
    # Then entropy and observation count reflect those four scalar amplitudes.
    assert result.value == pytest.approx(1.5)
    assert result.n_observations == 4
    assert result.diagnostics["counts"] == [1, 2, 1]


def test_histogram_when_data_is_constant_has_zero_entropy() -> None:
    # Given a constant multidimensional field.
    array = np.ones((3, 4))
    # When equal-width amplitude bins are selected.
    result = histogram_entropy(array, bins=3)
    # Then only one bin is occupied.
    assert result.value == 0


@pytest.mark.parametrize("bins", [0, True, [0], [0, 0, 4], [1, 2], [[0, 2], [3, 4]]])
def test_histogram_when_bins_are_invalid_rejects_it(
    bins: int | list[int] | list[list[int]],
) -> None:
    # Given invalid edges or edges that omit observations.
    data = [0, 1, 3]
    # When the histogram is requested.
    # Then invalid geometry never silently discards observations.
    with pytest.raises(ParameterError):
        histogram_entropy(data, bins=bins)


def test_histogram_when_bin_limit_is_exceeded_rejects_before_allocation() -> None:
    # Given a request exceeding its declared bin resource limit.
    # When histogram computation is requested.
    # Then a resource failure occurs.
    with pytest.raises(ResourceError):
        histogram_entropy([0, 1], bins=100, max_bins=20)


def test_joint_when_variables_are_independent_is_additive() -> None:
    # Given two independent fair binary variables.
    distribution = np.full((2, 2), 0.25)
    # When joint entropy is computed.
    result = joint_entropy(distribution)
    # Then it equals the sum of the two one-bit entropies.
    assert result.value == pytest.approx(2)


def test_conditional_when_variables_are_identical_has_zero_value() -> None:
    # Given perfectly coupled binary variables.
    distribution = np.diag([0.5, 0.5])
    # When X entropy is conditioned on Y.
    result = conditional_entropy(distribution)
    # Then conditioning completely removes uncertainty.
    assert result.value == 0


def test_conditional_when_uncertainty_is_tiny_preserves_representable_entropy() -> None:
    # Given nearly coupled binary variables whose rare conditional events matter.
    tiny = 1e-200
    distribution = [[0.5, tiny], [tiny, 0.5]]
    expected = -2 * tiny * math.log2(2 * tiny)
    # When conditional entropy is computed.
    result = conditional_entropy(distribution)
    # Then the rare-event entropy survives rather than cancelling in H(X,Y)-H(Y).
    assert result.value == pytest.approx(expected, rel=1e-12, abs=0)


def test_conditional_when_tensor_is_independent_has_expected_remaining_entropy() -> None:
    # Given three independent fair binary variables.
    distribution = np.full((2, 2, 2), 0.125)
    # When one variable is conditioned on.
    result = conditional_entropy(distribution, conditioned_axes=(1,))
    # Then the remaining two variables retain two bits.
    assert result.value == pytest.approx(2)


def test_mutual_information_when_variables_are_independent_is_zero() -> None:
    # Given an independent nonuniform joint distribution.
    distribution = np.outer([0.25, 0.75], [0.5, 0.5])
    # When mutual information is computed.
    result = mutual_information(distribution)
    # Then dependence contributes no information.
    assert result.value == pytest.approx(0)


def test_mutual_information_when_x_spans_multiple_axes_preserves_partition() -> None:
    # Given three identical binary variables represented by distinct tensor axes.
    distribution = np.zeros((2, 2, 2))
    distribution[0, 0, 0] = distribution[1, 1, 1] = 0.5
    # When X combines nonadjacent axes and Y is their complement.
    result = mutual_information(distribution, x_axes=(0, 2))
    # Then X and Y share precisely one bit.
    assert result.value == pytest.approx(1)


@pytest.mark.parametrize("axes", [(), (0, 0), (0, 1), (-1,), (2,), (True,)])
def test_mutual_information_when_partition_is_invalid_rejects_it(axes: tuple[int, ...]) -> None:
    # Given an empty, duplicated, complete, out-of-range or noninteger partition.
    distribution = np.full((2, 2), 0.25)
    # When it crosses the partition boundary.
    # Then the probability variables cannot be ambiguously grouped.
    with pytest.raises(ParameterError):
        mutual_information(distribution, x_axes=axes)


def test_jensen_shannon_when_supports_are_disjoint_has_one_bit() -> None:
    # Given point masses on disjoint cells.
    # When equally weighted JSD is computed.
    result = jensen_shannon_divergence([1, 0], [0, 1])
    # Then the source identity contributes one bit.
    assert result.value == pytest.approx(1)


@pytest.mark.parametrize("weight", [0.0, 1.0, 0.2, 0.5])
def test_jensen_shannon_when_supports_are_disjoint_equals_binary_mixture_entropy(
    weight: float,
) -> None:
    # Given an explicit mixture weight and the independent analytic answer.
    expected = (
        0
        if weight in (0, 1)
        else -weight * math.log2(weight) - (1 - weight) * math.log2(1 - weight)
    )
    # When JSD is computed.
    result = jensen_shannon_divergence([1, 0], [0, 1], weight=weight)
    # Then the requested mixture convention is honored.
    assert result.value == pytest.approx(expected)


def test_jensen_shannon_when_distributions_are_identical_is_zero() -> None:
    # Given identical probability distributions.
    probabilities = [0.25, 0.75]
    # When JSD is computed.
    result = jensen_shannon_divergence(probabilities, probabilities)
    # Then their divergence is zero.
    assert result.value == pytest.approx(0)


@pytest.mark.parametrize("weight", [0.5, 0.2, 1e-8])
def test_jensen_shannon_when_distributions_are_nearby_matches_decimal_oracle(weight: float) -> None:
    # Given independently evaluated 80-digit entropy differences for nearby distributions.
    left, right = [0.5 + 1e-8, 0.5 - 1e-8], [0.5, 0.5]
    with localcontext() as context:
        context.prec = 80
        a, b = ([Decimal(value) for value in left], [Decimal(value) for value in right])
        a = [value / sum(a) for value in a]
        b = [value / sum(b) for value in b]
        w = Decimal(weight)
        mixture = [w * p + (1 - w) * q for p, q in zip(a, b, strict=True)]
        expected = float(
            (
                -sum(value * value.ln() for value in mixture)
                + w * sum(value * value.ln() for value in a)
                + (1 - w) * sum(value * value.ln() for value in b)
            )
            / Decimal(2).ln()
        )
    # When the weighted divergence is evaluated in ordinary float64 arithmetic.
    result = jensen_shannon_divergence(left, right, weight=weight)
    # Then representable quadratic information is preserved rather than rounded away.
    assert result.value == pytest.approx(expected, rel=1e-8, abs=0)


@pytest.mark.parametrize("weight", [1e-200, 1e-8, 0.2, 0.8])
def test_jensen_shannon_when_zero_supports_mix_unequally_matches_binary_entropy(
    weight: float,
) -> None:
    # Given disjoint supports and a stable analytic binary-mixture entropy.
    expected = (-weight * math.log(weight) - (1 - weight) * math.log1p(-weight)) / math.log(2)
    # When arbitrary mixture weights and explicit zero cells are used.
    result = jensen_shannon_divergence([1, 0], [0, 1], weight=weight)
    # Then tiny mixing probabilities are retained without ratio overflow.
    assert result.value == pytest.approx(expected, rel=1e-12, abs=0)


def test_jensen_shannon_when_alphabets_share_zero_cells_handles_exact_zero_limits() -> None:
    # Given a shared zero cell and an analytic binary mixture on the occupied cells.
    expected = -(0.25 * math.log2(0.25) + 0.75 * math.log2(0.75)) - 0.5
    # When both probability distributions retain the complete three-cell alphabet.
    result = jensen_shannon_divergence([0.5, 0.5, 0], [0, 1, 0])
    # Then shared zeros create no undefined logarithms or spurious contributions.
    assert result.value == pytest.approx(expected)


def test_jensen_shannon_when_mixture_weight_is_subnormal_remains_finite() -> None:
    # Given the smallest positive float mixing two disjoint point masses.
    weight = float(np.nextafter(0.0, 1.0))
    expected = (-weight * math.log(weight) - (1 - weight) * math.log1p(-weight)) / math.log(2)
    # When logarithmic mixture coordinates avoid p/m ratio overflow.
    result = jensen_shannon_divergence([1, 0], [0, 1], weight=weight)
    # Then the representable subnormal binary entropy is retained.
    assert result.value == pytest.approx(expected, abs=2 * weight)


def test_jensen_shannon_when_weighted_mass_underflows_preserves_log_amplified_contribution() -> (
    None
):
    # Given a rare cell whose weighted mass underflows but whose entropy contribution does not.
    rare, weight = 1e-124, 1e-200
    expected = weight * (rare * -math.log(weight)) / math.log(2)
    # When log-mixture arithmetic avoids prematurely rounding the rare mass to zero.
    result = jensen_shannon_divergence([1, rare], [1, 0], weight=weight)
    # Then the leading entropy contribution survives within two subnormal ulps.
    assert result.value == pytest.approx(expected, abs=2 * float(np.nextafter(0.0, 1.0)))


def test_jensen_shannon_when_alphabets_differ_rejects_it() -> None:
    # Given distributions over differently shaped alphabets.
    # When JSD is requested.
    # Then implicit reshaping cannot establish shared cell identities.
    with pytest.raises(ParameterError):
        jensen_shannon_divergence([0.5, 0.5], [[0.5, 0.5]])


@pytest.mark.parametrize("weight", [-0.1, 1.1, math.nan, math.inf, True, "0.5"])
def test_jensen_shannon_when_weight_is_invalid_rejects_it(weight: float | str) -> None:
    # Given an invalid mixture probability.
    # When JSD is requested.
    # Then the options boundary rejects it.
    with pytest.raises(ValidationError):
        jensen_shannon_divergence([1, 0], [0, 1], weight=weight)
