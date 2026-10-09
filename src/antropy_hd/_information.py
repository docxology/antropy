# Copyright (c) 2026 Daniel Ari Friedman
"""Validated probability boundaries and shared numerical information helpers."""

import math
from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, StrictInt

from antropy_hd.errors import ParameterError
from antropy_hd.models import EntropyResult, Status
from antropy_hd.validation import as_real_array


class LogOptions(BaseModel):
    """Validated logarithmic units shared by the information-based measures."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    base: float = Field(default=2.0, gt=1, allow_inf_nan=False)
    normalize: StrictBool = False


class OrderOptions(BaseModel):
    """Require a numeric nonnegative entropy order at the API boundary."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    order: float = Field(ge=0)


class MixtureOptions(BaseModel):
    """Require a finite mixture probability at the API boundary."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    weight: float = Field(ge=0, le=1, allow_inf_nan=False)


def parse_probabilities(data: ArrayLike) -> NDArray[np.float64]:
    """Parse an actual probability distribution without accepting raw counts."""
    array = as_real_array(data)
    if bool(np.any(array < 0)) or bool(np.any(array > 1)):
        raise ParameterError("probabilities", "entries must lie between zero and one")
    total = math.fsum(float(value) for value in array.flat)
    if not math.isclose(total, 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise ParameterError("probabilities", "entries must sum to one within 1e-12")
    # WHY: correct only accepted floating-point summation residuals, never raw counts.
    return array / total


def shannon_value(array: NDArray[np.float64], base: float) -> float:
    """Compute Shannon entropy while defining zero-mass contributions as zero."""
    positive = array[array > 0]
    return max(0.0, -float(np.sum(positive * np.log(positive))) / math.log(base))


def probability_result(
    measure: str, value: float | None, array: NDArray[np.float64], parameters: dict[str, JsonValue]
) -> EntropyResult:
    """Label the probability-cell count rather than implying a sample size."""
    return EntropyResult(
        measure=measure,
        value=value,
        status=Status.UNDEFINED if value is None else Status.FINITE,
        n_observations=array.size,
        parameters=parameters,
        diagnostics={
            "positive_cells": int(np.count_nonzero(array)),
            "observation_kind": "probability_cells",
        },
    )


def normalize_value(value: float, size: int, enabled: bool, maximum: float) -> float | None:
    """Normalize by the declared alphabet maximum, explicitly handling size one."""
    if enabled:
        return value / maximum if size > 1 else None
    return value


class HistogramLimits(BaseModel):
    """Bound the memory allocation selected by histogram users."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    max_bins: StrictInt = Field(ge=1)


def partition_axes(axes: tuple[int, ...], ndim: int) -> tuple[int, ...]:
    """Require a nonempty proper set of probability-variable axes."""
    if not axes or len(set(axes)) != len(axes) or len(axes) >= ndim:
        raise ParameterError("axes", "requires a nonempty proper set of unique tensor axes")
    if any(type(axis) is not int or axis < 0 or axis >= ndim for axis in axes):
        raise ParameterError(
            "axes", "axes must be nonnegative integers within tensor dimensionality"
        )
    return tuple(axis for axis in range(ndim) if axis not in axes)
