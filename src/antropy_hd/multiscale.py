# Copyright (c) 2026 Daniel Ari Friedman
"""Explicit ND coarse-graining and original-tolerance multiscale HDSE."""

from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

from antropy_hd.embedding import resolve_geometry
from antropy_hd.errors import ParameterError
from antropy_hd.models import EmbeddingConfig, EntropyResult, MatchConfig
from antropy_hd.template_entropy import hdse
from antropy_hd.validation import as_real_array, threshold_for


def coarse_grain(data: ArrayLike, scale: int | tuple[int, ...]) -> NDArray[np.float64]:
    """Average aligned ND blocks, trimming incomplete blocks at the high boundary."""
    array = as_real_array(data)
    parsed = EmbeddingConfig(shape=scale)
    factors = resolve_geometry(parsed.shape, array.ndim, "scale")
    sizes = tuple(size // factor for size, factor in zip(array.shape, factors, strict=True))
    if min(sizes) < 1:
        raise ParameterError("scale", "scale exceeds at least one input axis")
    trimmed = array[
        tuple(slice(0, size * factor) for size, factor in zip(sizes, factors, strict=True))
    ]
    shape = tuple(entry for pair in zip(sizes, factors, strict=True) for entry in pair)
    axes = tuple(range(1, 2 * array.ndim, 2))
    magnitude = float(np.max(np.abs(trimmed)))
    if magnitude == 0:
        return np.zeros(sizes, dtype=np.float64)
    return np.mean((trimmed / magnitude).reshape(shape), axis=axes) * magnitude


def multiscale_entropy(
    data: ArrayLike,
    *,
    scales: Sequence[int | tuple[int, ...]] = (1, 2, 3),
    embedding: EmbeddingConfig | None = None,
    match: MatchConfig | None = None,
    preserve_tolerance: bool = True,
) -> tuple[EntropyResult, ...]:
    """Evaluate HDSE after coarse-graining; retain original SD radius by default.

    With 1D input this is the common-origin multiscale SampEn construction using
    the HDSE strict boundary. Invalid scales fail the whole request explicitly.
    """
    array = as_real_array(data)
    if not scales:
        raise ParameterError("scales", "requires at least one scale")
    matching = match or MatchConfig()
    threshold = threshold_for(array, matching)
    effective = (
        MatchConfig.model_validate(
            matching.model_dump() | {"tolerance": threshold, "relative": False}
        )
        if preserve_tolerance
        else matching
    )
    results: list[EntropyResult] = []
    for scale in scales:
        coarse = coarse_grain(array, scale)
        result = hdse(coarse, embedding=embedding, match=effective)
        results.append(
            result.model_copy(
                update={
                    "measure": "multiscale_hdse",
                    "parameters": result.parameters
                    | {
                        "scale": list(resolve_geometry(scale, array.ndim, "scale")),
                        "preserve_tolerance": preserve_tolerance,
                        "original_match": matching.model_dump(mode="json"),
                    },
                    "diagnostics": result.diagnostics | {"original_shape": list(array.shape)},
                }
            )
        )
    return tuple(results)
