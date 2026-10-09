# Copyright (c) 2026 Daniel Ari Friedman
"""Numerical replay preserves exact discrete evidence and bounds float64 roundoff."""

from __future__ import annotations

import math
from typing import assert_never

import numpy as np
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.models import EntropyResult
from antropy_hd.orchestration import AnalysisResult, canonical_json


def numeric_equivalent(stored: JsonValue, replayed: JsonValue) -> bool:
    """Compare counts/identities exactly and real-valued diagnostics within a declared budget."""
    match stored, replayed:
        case (int(), int()) | (str(), str()) | (None, None):
            return type(stored) is type(replayed) and stored == replayed
        case float(), float():
            tolerance = 64 * float(np.finfo(np.float64).eps) * max(1.0, abs(replayed))
            return (
                math.isfinite(stored)
                and math.isfinite(replayed)
                and abs(stored - replayed) <= tolerance
            )
        case list(), list():
            return len(stored) == len(replayed) and all(
                numeric_equivalent(a, b) for a, b in zip(stored, replayed, strict=True)
            )
        case dict(), dict():
            return stored.keys() == replayed.keys() and all(
                numeric_equivalent(stored[key], replayed[key]) for key in stored
            )
        case (
            (str() | int() | float() | bool() | list() | dict() | None),
            (str() | int() | float() | bool() | list() | dict() | None),
        ):
            return False
        case unreachable:
            assert_never(unreachable)


def result_equivalent(stored: EntropyResult, replayed: EntropyResult) -> bool:
    """Require exact status/configuration and counts before bounded floating replay."""
    return (
        stored.measure == replayed.measure
        and stored.status == replayed.status
        and stored.n_observations == replayed.n_observations
        and canonical_json(stored.parameters) == canonical_json(replayed.parameters)
        and numeric_equivalent(stored.value, replayed.value)
        and numeric_equivalent(stored.diagnostics, replayed.diagnostics)
    )


def scalar_result(result: AnalysisResult) -> EntropyResult:
    """Require a scalar at a scalar study's result boundary."""
    match result:
        case EntropyResult():
            return result
        case tuple():
            raise ParameterError("results", "Scalar studies cannot contain multiscale tuples")
        case unreachable:
            assert_never(unreachable)
