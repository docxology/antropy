# Copyright (c) 2026 Daniel Ari Friedman
"""Real block averages and explicit multiscale tolerance policies."""

import numpy as np
import pytest
from pydantic import ValidationError

from antropy_hd import (
    EmbeddingConfig,
    MatchConfig,
    ParameterError,
    coarse_grain,
    hdse,
    multiscale_entropy,
)


def test_rectangular_coarse_grain_trims_remainder() -> None:
    # Given a rectangular field with high-boundary remainder.
    data = np.arange(35).reshape(5, 7)
    # When 2-by-3 block averages are computed.
    result = coarse_grain(data, (2, 3))
    # Then each native block average and trimming agrees by hand.
    assert result == pytest.approx(np.array([[4.5, 7.5], [18.5, 21.5]]))


def test_original_tolerance_is_preserved_across_scales() -> None:
    # Given noisy input with different coarse-grained variance.
    data = np.random.default_rng(82).normal(size=60)
    match = MatchConfig(tolerance=1.5)
    expected = 1.5 * data.std()
    # When default multiscale HDSE is computed.
    results = multiscale_entropy(data, scales=(1, 2, 3), match=match)
    # Then all scales share the original radius.
    assert [result.diagnostics["threshold"] for result in results] == pytest.approx([expected] * 3)


def test_scale_specific_tolerance_is_explicit() -> None:
    # Given an explicit recomputed-SD variant.
    data = np.random.default_rng(10).normal(size=(12, 12))
    # When a rectangular scale is applied.
    result = multiscale_entropy(
        data,
        scales=((2, 1),),
        embedding=EmbeddingConfig(shape=1),
        match=MatchConfig(tolerance=1.5),
        preserve_tolerance=False,
    )[0]
    # Then it agrees with HDSE on the coarse-grained field.
    expected = hdse(
        coarse_grain(data, (2, 1)),
        embedding=EmbeddingConfig(shape=1),
        match=MatchConfig(tolerance=1.5),
    )
    assert result.as_float() == expected.as_float()


def test_absolute_tolerance_is_unaffected_by_scale_policy() -> None:
    # Given an absolute radius.
    # When multiscale analysis changes geometry.
    result = multiscale_entropy(
        np.arange(20),
        scales=(1, 2),
        embedding=EmbeddingConfig(shape=1),
        match=MatchConfig(tolerance=2, relative=False),
    )
    # Then both scales keep the declared numeric width.
    assert [entry.diagnostics["threshold"] for entry in result] == [2.0, 2.0]


@pytest.mark.parametrize("scale", [0, -1, True, 1.5, 100, (2, 2)])
def test_invalid_scale_is_rejected(scale: float | tuple[int, ...]) -> None:
    # Given a malformed or incompatible scale.
    # When coarse-graining is requested.
    with pytest.raises((ParameterError, ValidationError)):
        coarse_grain(np.arange(10), scale)
    # Then no silently substituted scale is used.


def test_empty_multiscale_request_is_rejected() -> None:
    # Given no scales.
    # When the multiscale API is called.
    with pytest.raises(ParameterError):
        multiscale_entropy(np.arange(10), scales=())
    # Then an empty report cannot masquerade as success.


def test_zero_field_coarse_grain_is_zero() -> None:
    # Given a zero field.
    # When scaled averages are requested.
    result = coarse_grain(np.zeros((6, 6)), 2)
    # Then no division-by-zero occurs.
    assert np.array_equal(result, np.zeros((3, 3)))
