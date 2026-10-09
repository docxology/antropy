# Copyright (c) 2026 Daniel Ari Friedman
"""HDSE, one-dimensional SampEn and explicit spatial ApEn/FuzzyEn extensions."""

import math

import numpy as np
from numpy.typing import ArrayLike
from pydantic import JsonValue

from antropy_hd.embedding import (
    Templates,
    extended_shape,
    local_templates,
    paired_templates,
    resolve_geometry,
)
from antropy_hd.errors import ParameterError
from antropy_hd.fuzzy import fuzzy_entropy
from antropy_hd.models import EmbeddingConfig, EntropyResult, MatchConfig, Status
from antropy_hd.pairs import distance_block, guard_pairs, match_counts
from antropy_hd.validation import as_real_array, threshold_for

__all__ = ["approximate_entropy", "fuzzy_entropy", "hdse", "sample_entropy"]


def _parameters(embedding: EmbeddingConfig, match: MatchConfig) -> dict[str, JsonValue]:
    return {"embedding": embedding.model_dump(mode="json"), "match": match.model_dump(mode="json")}


def hdse(
    data: ArrayLike, *, embedding: EmbeddingConfig | None = None, match: MatchConfig | None = None
) -> EntropyResult:
    """Estimate Xia-Wang HDSE, or an explicitly configured spatial generalization.

    Defaults follow equations (1)-(6): common origins, strict Chebyshev matches,
    global population SD and tuple self exclusion. No-match 0/0 is undefined.
    """
    array = as_real_array(data)
    geometry = embedding or EmbeddingConfig()
    matching = match or MatchConfig()
    threshold = threshold_for(array, matching)
    templates = paired_templates(array, geometry)
    base, pairs = match_counts(
        templates.base, geometry, matching, threshold, live_bytes=templates.extended.values.nbytes
    )
    extended, _ = match_counts(
        templates.extended, geometry, matching, threshold, live_bytes=templates.base.values.nbytes
    )
    if base == 0:
        status, value = Status.UNDEFINED, None
    elif extended == 0:
        status, value = Status.INFINITE, None
    else:
        status, value = Status.FINITE, math.log(base) - math.log(extended)
    diagnostics: dict[str, JsonValue] = {
        "base_matches": base,
        "extended_matches": extended,
        "eligible_pairs": pairs,
        "threshold": threshold,
        "base_probability": base / pairs if pairs else None,
        "extended_probability": extended / pairs if pairs else None,
        "input_shape": list(array.shape),
        "base_shape": list(templates.base.shape),
        "extended_shape": list(templates.extended.shape),
    }
    return EntropyResult(
        measure="hdse",
        value=value,
        status=status,
        n_observations=len(templates.base.values),
        parameters=_parameters(geometry, matching),
        diagnostics=diagnostics,
    )


def sample_entropy(
    data: ArrayLike, *, embedding: EmbeddingConfig | None = None, match: MatchConfig | None = None
) -> EntropyResult:
    """Conventional 1D common-origin SampEn with a closed threshold by default."""
    array = as_real_array(data)
    if array.ndim != 1:
        raise ParameterError("data", "sample_entropy requires 1D; use hdse for spatial arrays")
    result = hdse(array, embedding=embedding, match=match or MatchConfig(closed=True))
    return result.model_copy(update={"measure": "sample_entropy"})


def _phi(
    templates: Templates,
    geometry: EmbeddingConfig,
    matching: MatchConfig,
    threshold: float,
    *,
    live_bytes: int = 0,
) -> float | None:
    guard_pairs(templates, geometry, matching, live_bytes=live_bytes + len(templates.values) * 8)
    count = len(templates.values)
    row_counts = np.zeros(count, dtype=np.int64)
    block = matching.block_size
    for start in range(0, count, block):
        for other in range(0, count, block):
            distances = distance_block(
                templates.values[start : start + block],
                templates.values[other : other + block],
                matching.metric,
            )
            close = distances <= threshold if matching.closed else distances < threshold
            row_counts[start : start + block] += np.count_nonzero(close, axis=1)
    if bool(np.any(row_counts == 0)):
        return None
    return float(np.mean(np.log(row_counts / count)))


def approximate_entropy(
    data: ArrayLike, *, embedding: EmbeddingConfig | None = None, match: MatchConfig | None = None
) -> EntropyResult:
    """ApEn with full separate origin populations and included self matches.

    For ND input this is a spatial extension of Pincus's 1D statistic. Origin
    exclusions are unsupported because ApEn intentionally includes self matches.
    """
    array = as_real_array(data)
    geometry = embedding or EmbeddingConfig()
    matching = match or MatchConfig(closed=True)
    if matching.exclusion.value != "self" or matching.theiler != 0:
        raise ParameterError(
            "match", "approximate entropy includes self matches and rejects exclusions"
        )
    shape = resolve_geometry(geometry.shape, array.ndim, "shape")
    larger = extended_shape(shape, geometry.extend_axes)
    extended_geometry = EmbeddingConfig.model_validate(geometry.model_dump() | {"shape": larger})
    threshold = threshold_for(array, matching)
    base = local_templates(array, geometry)
    base_count = len(base.values)
    phi_base = _phi(base, geometry, matching, threshold)
    # WHY: ApEn's different origin populations need not coexist in memory.
    del base
    extended = local_templates(array, extended_geometry)
    phi_extended = _phi(extended, geometry, matching, threshold)
    value = None if phi_base is None or phi_extended is None else phi_base - phi_extended
    return EntropyResult(
        measure="approximate_entropy",
        value=value,
        status=Status.UNDEFINED if value is None else Status.FINITE,
        n_observations=base_count,
        parameters=_parameters(geometry, matching),
        diagnostics={
            "threshold": threshold,
            "extended_observations": len(extended.values),
            "phi_base": phi_base,
            "phi_extended": phi_extended,
        },
    )
