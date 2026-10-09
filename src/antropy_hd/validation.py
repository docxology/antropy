# Copyright (c) 2026 Daniel Ari Friedman
"""Numerical input boundaries; all methods reject missing or nonfinite data."""

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from antropy_hd.errors import ParameterError
from antropy_hd.models import MatchConfig


def as_real_array(data: ArrayLike) -> NDArray[np.float64]:
    """Parse nonempty nonscalar real numeric input without mutating its owner."""
    raw = np.asarray(data)
    if raw.ndim == 0 or raw.size == 0:
        raise ParameterError("data", "requires a nonempty array with at least one axis")
    if raw.dtype.kind not in "iuf":
        raise ParameterError("data", "requires real numeric values, excluding booleans")
    array: NDArray[np.float64] = np.asarray(raw, dtype=np.float64)
    if not bool(np.all(np.isfinite(array))):
        raise ParameterError("data", "all values must be finite and float64-representable")
    return array


def threshold_for(data: NDArray[np.float64], config: MatchConfig) -> float:
    """Resolve absolute tolerance once from the full input and declared SD convention."""
    if config.ddof >= data.size:
        raise ParameterError("ddof", "must be smaller than the number of input elements")
    if not config.relative:
        return config.tolerance
    # WHY: rescaling prevents overflow in variance for large finite values.
    low, high = float(np.min(data)), float(np.max(data))
    # Midrange translation preserves differences between nearby large floats.
    # Halving before addition avoids overflow for either sign of finite input.
    midpoint = low / 2 + high / 2
    shifted = data - midpoint
    scale = float(np.max(np.abs(shifted)))
    threshold = 0.0
    if scale and config.tolerance:
        sd = float(np.std(shifted / scale, ddof=config.ddof))
        # WHY: frexp avoids intermediate overflow/underflow in any product order.
        sd_mantissa, sd_exponent = math.frexp(sd)
        radius_mantissa, radius_exponent = math.frexp(config.tolerance)
        scale_mantissa, scale_exponent = math.frexp(scale)
        try:
            threshold = math.ldexp(
                sd_mantissa * radius_mantissa * scale_mantissa,
                sd_exponent + radius_exponent + scale_exponent,
            )
        except OverflowError as error:
            raise ParameterError("tolerance", "resolved threshold exceeds float64 range") from error
    if not math.isfinite(threshold):
        raise ParameterError("tolerance", "resolved threshold exceeds float64 range")
    return threshold
