# Copyright (c) 2026 Daniel Ari Friedman
"""Ordinal complexity from native-dimensional spatial windows."""

import math
from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike
from pydantic import ConfigDict, Field, StrictBool, StrictInt

from antropy_hd._information import LogOptions
from antropy_hd.embedding import local_templates, resolve_geometry
from antropy_hd.errors import ResourceError
from antropy_hd.information import shannon_entropy
from antropy_hd.models import EmbeddingConfig, EntropyResult, Status
from antropy_hd.validation import as_real_array


class _OrdinalOptions(LogOptions):
    """Bound ordinal alphabet complexity and select variance weighting."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    weighted: StrictBool = False
    max_pattern_length: StrictInt = Field(default=10, ge=2, le=32)


def permutation_entropy(
    data: ArrayLike,
    *,
    embedding: EmbeddingConfig | None = None,
    weighted: bool = False,
    base: float = 2.0,
    normalize: bool = False,
    max_pattern_length: int = 10,
) -> EntropyResult:
    """Compute entropy of local C-order permutations with stable positional ties.

    A scalar shape applies to every axis. Rectangular N-D windows are an explicit
    extension of time-series permutation entropy. Variance weighting is optional;
    normalized values divide by log(k!), where k is the local sample count.
    """
    options = _OrdinalOptions(
        base=base, normalize=normalize, weighted=weighted, max_pattern_length=max_pattern_length
    )
    config = EmbeddingConfig() if embedding is None else embedding
    array = as_real_array(data)
    shape = resolve_geometry(config.shape, array.ndim, "shape")
    length = math.prod(shape)
    if length > options.max_pattern_length:
        raise ResourceError("max_pattern_length", f"{length} samples exceed the ordinal limit")
    templates = local_templates(array, config)
    estimated = templates.values.nbytes * 6 + templates.origins.nbytes
    if estimated > config.max_memory_bytes:
        raise ResourceError(
            "max_memory_bytes", f"ordinal working arrays need at least {estimated} bytes"
        )
    ranks = np.argsort(templates.values, axis=1, kind="stable")
    patterns, inverse = np.unique(ranks, axis=0, return_inverse=True)
    count = len(templates.values)
    if options.weighted:
        low = np.min(templates.values, axis=1, keepdims=True)
        high = np.max(templates.values, axis=1, keepdims=True)
        shifted = templates.values - (low / 2 + high / 2)
        scale = float(np.max(np.abs(shifted)))
        weights = (
            np.zeros(count, dtype=np.float64) if scale == 0 else np.var(shifted / scale, axis=1)
        )
    else:
        weights = np.ones(count, dtype=np.float64)
    masses = np.bincount(inverse, weights=weights, minlength=len(patterns))
    total = float(np.sum(masses))
    value: float | None = None
    if total > 0:
        raw = shannon_entropy(masses / total, base=options.base).as_float()
        value = raw
        if options.normalize:
            value = raw / (math.lgamma(length + 1) / math.log(options.base)) if length > 1 else None
    return EntropyResult(
        measure="weighted_permutation" if options.weighted else "permutation",
        value=value,
        status=Status.UNDEFINED if value is None else Status.FINITE,
        n_observations=count,
        parameters={
            "embedding": config.model_dump(mode="json"),
            "base": options.base,
            "normalize": options.normalize,
            "weighted": options.weighted,
            "max_pattern_length": options.max_pattern_length,
        },
        diagnostics={
            "pattern_length": length,
            "observed_patterns": len(patterns),
            "positive_weight_patterns": int(np.count_nonzero(masses)),
            "ties": "stable_c_order",
            "weight_scaling": "local_midrange_then_global_max_abs" if options.weighted else "none",
        },
    )


def weighted_permutation_entropy(
    data: ArrayLike,
    *,
    embedding: EmbeddingConfig | None = None,
    base: float = 2.0,
    normalize: bool = False,
    max_pattern_length: int = 10,
) -> EntropyResult:
    """Compute permutation entropy weighted by each local population variance."""
    return permutation_entropy(
        data,
        embedding=embedding,
        weighted=True,
        base=base,
        normalize=normalize,
        max_pattern_length=max_pattern_length,
    )
