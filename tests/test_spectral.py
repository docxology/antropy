# Copyright (c) 2026 Daniel Ari Friedman
"""Analytic Fourier/SVD examples and explicit degeneracy/resource checks."""

import math

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd.errors import ResourceError
from antropy_hd.models import EmbeddingConfig, Status
from antropy_hd.spectral import spectral_entropy, svd_entropy


def test_spectral_when_input_is_impulse_has_uniform_full_spectrum() -> None:
    # Given an N-D impulse, whose Fourier power is identical at every bin.
    data = np.zeros((3, 4))
    data[0, 0] = 1
    # When the complete periodogram is evaluated without centering.
    result = spectral_entropy(data, demean=False)
    # Then its entropy is the logarithm of all twelve bins.
    assert result.value == pytest.approx(math.log2(12))


def test_spectral_when_dc_is_removed_uses_remaining_alphabet() -> None:
    # Given an impulse with uniform full-spectrum power.
    data = np.array([1, 0, 0, 0])
    # When DC is excluded from the probability alphabet.
    result = spectral_entropy(data, demean=False, include_dc=False)
    # Then the three retained bins have log2(3) entropy.
    assert result.value == pytest.approx(math.log2(3))


def test_spectral_when_normalized_impulse_has_unit_entropy() -> None:
    # Given a uniform spectrum after DC exclusion.
    data = np.array([1, 0, 0, 0])
    # When entropy is normalized by the retained bin count.
    result = spectral_entropy(data, demean=False, include_dc=False, normalize=True)
    # Then it attains the maximum of that alphabet.
    assert result.value == pytest.approx(1)


def test_spectral_when_input_is_cosine_counts_conjugate_bins_separately() -> None:
    # Given a real sinusoid occupying two equal conjugate-frequency bins.
    data = np.cos(2 * np.pi * np.arange(16) / 16)
    # When full-spectrum entropy is computed.
    result = spectral_entropy(data)
    # Then the two-bin distribution has one bit, unlike a one-sided convention.
    assert result.value == pytest.approx(1, abs=1e-12)


def test_spectral_when_axis_geometry_differs_from_flattening_uses_nd_transform() -> None:
    # Given a checkerboard carrying one N-D Nyquist component.
    data = np.array([[1, -1], [-1, 1]])
    # When the native two-dimensional FFT is computed.
    result = spectral_entropy(data)
    # Then the one-bin spectrum has zero entropy.
    assert result.value == pytest.approx(0)


def test_spectral_when_signal_is_constant_and_dc_retained_has_zero_entropy() -> None:
    # Given a nonzero constant field carrying only DC power.
    data = np.full((2, 3), 5.0)
    # When DC is retained without centering.
    result = spectral_entropy(data, demean=False)
    # Then its point-mass spectrum has zero entropy.
    assert result.value == 0


@pytest.mark.parametrize(("demean", "include_dc"), [(True, True), (False, False)])
def test_spectral_when_constant_signal_has_no_retained_power_is_undefined(
    demean: bool, include_dc: bool
) -> None:
    # Given a constant field whose only power is removed by the chosen convention.
    data = np.full((2, 3), 5.0)
    # When the periodogram convention is applied.
    result = spectral_entropy(data, demean=demean, include_dc=include_dc)
    # Then zero total power cannot define probabilities.
    assert result.status is Status.UNDEFINED


def test_spectral_when_zero_signal_has_no_power_is_undefined() -> None:
    # Given a zero-amplitude signal.
    data = np.zeros((2, 3))
    # When uncentered spectral entropy is computed.
    result = spectral_entropy(data, demean=False)
    # Then the zero-power result is explicit.
    assert result.status is Status.UNDEFINED


def test_spectral_when_singleton_alphabet_is_normalized_is_undefined() -> None:
    # Given one nonzero input sample and one Fourier bin.
    # When division by its zero entropy maximum is requested.
    result = spectral_entropy([2], demean=False, normalize=True)
    # Then singleton normalization is undefined.
    assert result.status is Status.UNDEFINED


def test_spectral_when_dc_removal_leaves_no_bins_is_undefined() -> None:
    # Given one input sample whose only Fourier bin is DC.
    # When the bin is excluded.
    result = spectral_entropy([2], demean=False, include_dc=False)
    # Then an empty spectral alphabet is represented explicitly.
    assert result.status is Status.UNDEFINED


def test_spectral_when_amplitudes_are_extreme_is_scale_invariant() -> None:
    # Given a checkerboard whose direct power squares would overflow.
    data = np.array([[1, -1], [-1, 1]], dtype=np.float64) * 1e308
    # When the scaled periodogram is computed.
    result = spectral_entropy(data)
    # Then the one-bin result remains finite and correct.
    assert result.value == pytest.approx(0)


def test_spectral_when_offset_is_huge_preserves_demeaned_fluctuations() -> None:
    # Given exactly represented fluctuations over a huge common baseline.
    x = np.array([0, 1, 2, 0, 1, 0, 2, 1]) * np.spacing(1e308) + 1e308
    y = x - x[0]
    expected = spectral_entropy(y, demean=True).value
    # When the original field is demeaned before spectral analysis.
    result = spectral_entropy(x, demean=True)
    # Then additive offsets do not alter the fluctuation spectrum.
    assert result.value == pytest.approx(expected, abs=1e-14)


def test_spectral_when_storage_budget_is_exceeded_rejects_before_fft() -> None:
    # Given a field exceeding a declared 1024-byte FFT working budget.
    data = np.ones((4, 4))
    # When spectral entropy is requested.
    # Then the storage guard rejects the request.
    with pytest.raises(ResourceError):
        spectral_entropy(data, max_memory_bytes=1024)


@pytest.mark.parametrize("memory", [0, 100, True])
def test_spectral_when_memory_budget_is_invalid_rejects_it(memory: int) -> None:
    # Given an invalid memory configuration.
    # When it crosses the options boundary.
    # Then it fails validation.
    with pytest.raises(ValidationError):
        spectral_entropy([1, 2], max_memory_bytes=memory)


def test_svd_when_trajectory_is_identity_has_equal_singular_values() -> None:
    # Given pair templates [[1,0],[0,1]], with singular values (1,1).
    data = [1, 0, 1]
    # When singular-value entropy is computed.
    result = svd_entropy(data)
    # Then equal singular values give one bit.
    assert result.value == pytest.approx(1)


def test_svd_when_known_singular_values_are_unequal_uses_values_not_squared_values() -> None:
    # Given disjoint local templates forming diag(2,1).
    data = [2, 0, 0, 1]
    expected = -(2 / 3) * math.log2(2 / 3) - (1 / 3) * math.log2(1 / 3)
    # When origin stride two isolates those templates.
    result = svd_entropy(data, embedding=EmbeddingConfig(stride=2))
    # Then weights are (2/3,1/3), rather than squared-value weights (4/5,1/5).
    assert result.value == pytest.approx(expected)


def test_svd_when_input_is_spatial_preserves_rectangular_embedding() -> None:
    # Given native horizontal templates (2,0) and (0,1).
    data = np.array([[2, 0], [0, 1]])
    expected = -(2 / 3) * math.log2(2 / 3) - (1 / 3) * math.log2(1 / 3)
    # When 1x2 windows are extracted along both valid row origins.
    result = svd_entropy(data, embedding=EmbeddingConfig(shape=(1, 2)))
    # Then the spatial trajectory matrix is exactly the independent diagonal example.
    assert result.value == pytest.approx(expected)
    assert result.n_observations == 2


def test_svd_when_trajectory_has_rank_one_has_zero_entropy() -> None:
    # Given a constant trajectory matrix with exactly one nonzero singular value.
    data = np.ones((3, 3))
    # When uncentered SVD entropy is computed.
    result = svd_entropy(data)
    # Then entropy tends to zero within numerical decomposition precision.
    assert result.value == pytest.approx(0, abs=1e-12)


@pytest.mark.parametrize("demean", [False, True])
def test_svd_when_trajectory_has_zero_mass_is_undefined(demean: bool) -> None:
    # Given a zero trajectory matrix.
    data = np.zeros((3, 3))
    # When SVD entropy is computed.
    result = svd_entropy(data, demean=demean)
    # Then no singular-value probability distribution can be formed.
    assert result.status is Status.UNDEFINED


def test_svd_when_column_centering_removes_constant_trajectory_is_undefined() -> None:
    # Given identical nonzero local templates at every origin.
    data = np.ones((3, 3))
    # When each trajectory column is centered across origins.
    result = svd_entropy(data, demean=True)
    # Then all singular values are zero.
    assert result.status is Status.UNDEFINED


def test_svd_when_normalized_identity_has_unit_entropy() -> None:
    # Given two equally weighted singular values.
    data = [1, 0, 1]
    # When entropy is divided by the two-singular-value maximum.
    result = svd_entropy(data, normalize=True)
    # Then it attains the maximum.
    assert result.value == pytest.approx(1)


def test_svd_when_normalized_trajectory_has_one_singular_value_is_undefined() -> None:
    # Given a trajectory with one column.
    data = [1, 2, 3]
    # When singleton-alphabet normalization is requested.
    result = svd_entropy(data, embedding=EmbeddingConfig(shape=1), normalize=True)
    # Then the zero normalization denominator is explicit.
    assert result.status is Status.UNDEFINED


def test_svd_when_column_centering_is_applied_has_expected_rank_one_entropy() -> None:
    # Given identity trajectory rows whose column-centered form has rank one.
    data = [1, 0, 1]
    # When nonconstant columns are centered across their two origins.
    result = svd_entropy(data, demean=True)
    # Then singular-value mass lies in one mode.
    assert result.value == pytest.approx(0, abs=1e-12)


def test_svd_when_amplitudes_are_extreme_is_scale_invariant() -> None:
    # Given a diagonal trajectory whose direct decomposition scale is extreme.
    data = np.array([2, 0, 0, 1], dtype=np.float64) * 1e307
    expected = -(2 / 3) * math.log2(2 / 3) - (1 / 3) * math.log2(1 / 3)
    # When SVD entropy is computed after numerically safe common scaling.
    result = svd_entropy(data, embedding=EmbeddingConfig(stride=2))
    # Then the normalized singular-value result is unchanged.
    assert result.value == pytest.approx(expected)


def test_svd_when_offset_is_huge_preserves_column_centered_fluctuations() -> None:
    # Given exactly represented fluctuations over a huge common baseline.
    x = np.array([0, 1, 2, 0, 1, 0, 2, 1]) * np.spacing(1e308) + 1e308
    y = x - x[0]
    expected = svd_entropy(y, demean=True).value
    # When trajectory columns are centered in the original high-offset field.
    result = svd_entropy(x, demean=True)
    # Then additive offsets do not alter normalized singular-value weights.
    assert result.value == pytest.approx(expected, abs=1e-14)


def test_svd_when_working_storage_budget_is_exceeded_rejects_it() -> None:
    # Given a base trajectory fitting 1024 bytes whose SVD working arrays exceed it.
    data = np.arange(15)
    # When the explicit resource limit is applied.
    # Then decomposition is guarded.
    with pytest.raises(ResourceError, match="max_memory_bytes"):
        svd_entropy(data, embedding=EmbeddingConfig(max_memory_bytes=1024))
