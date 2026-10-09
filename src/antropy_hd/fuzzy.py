# Copyright (c) 2026 Daniel Ari Friedman
"""Log-domain spatial fuzzy entropy with explicit numeric range failures."""

import math

import numpy as np
from numpy.typing import ArrayLike
from pydantic import JsonValue

from antropy_hd.embedding import Templates, paired_templates
from antropy_hd.errors import ParameterError
from antropy_hd.models import EmbeddingConfig, EntropyResult, MatchConfig, Status
from antropy_hd.pairs import guard_pairs, pair_blocks
from antropy_hd.validation import as_real_array, threshold_for


def _log_membership(
    templates: Templates,
    geometry: EmbeddingConfig,
    matching: MatchConfig,
    threshold: float,
    power: float,
    center: bool,
    *,
    live_bytes: int = 0,
) -> tuple[float, int]:
    values = templates.values
    # Radius-rescaled coordinates preserve memberships and avoid centering overflow.
    guard_pairs(
        templates, geometry, matching, live_bytes=live_bytes + values.nbytes * 3 + len(values) * 32
    )
    midpoints = (
        (np.min(values, axis=1, keepdims=True) / 2 + np.max(values, axis=1, keepdims=True) / 2)
        if center
        else float(np.min(values)) / 2 + float(np.max(values)) / 2
    )
    shifted = values - midpoints
    with np.errstate(over="ignore"):
        scaled = shifted / threshold
    if not bool(np.all(np.isfinite(scaled))):
        raise ParameterError("tolerance", "fuzzy kernel coordinate ratio exceeds float64 range")
    if center:
        scale = float(np.max(np.abs(scaled)))
        means = (
            np.zeros((len(values), 1))
            if scale == 0
            else np.mean(scaled / scale, axis=1, keepdims=True) * scale
        )
        values = scaled - means
    else:
        values = scaled
    centered = Templates(values, templates.origins, templates.shape)
    log_sum = -math.inf
    pairs = 0
    for distances, eligible in pair_blocks(
        centered,
        geometry,
        matching,
        live_bytes=live_bytes
        + templates.values.nbytes
        + scaled.nbytes
        + shifted.nbytes
        + len(values) * 32,
    ):
        selected = distances[eligible]
        pairs += len(selected)
        if len(selected):
            if not bool(np.all(np.isfinite(selected))):
                raise ParameterError("data", "fuzzy kernel distance exceeds float64 range")
            with np.errstate(over="ignore"):
                weights = -(selected**power)
            if not bool(np.all(np.isfinite(weights))):
                raise ParameterError("power", "fuzzy log membership exceeds float64 range")
            peak = float(np.max(weights))
            log_sum = float(
                np.logaddexp(log_sum, peak + math.log(float(np.sum(np.exp(weights - peak)))))
            )
    return (log_sum - math.log(pairs), pairs) if pairs else (-math.inf, 0)


def fuzzy_entropy(
    data: ArrayLike,
    *,
    embedding: EmbeddingConfig | None = None,
    match: MatchConfig | None = None,
    power: float = 2.0,
    center: bool = True,
) -> EntropyResult:
    """Spatial FuzzyEn using exp(-(distance/threshold)**power), in log space.

    Independent template mean centering is enabled by default. This variant may
    be negative because centered extension distances are not necessarily nested.
    """
    if not math.isfinite(power) or power <= 0:
        raise ParameterError("power", "requires a finite positive exponent")
    array = as_real_array(data)
    geometry = embedding or EmbeddingConfig()
    matching = match or MatchConfig()
    threshold = threshold_for(array, matching)
    templates = paired_templates(array, geometry)
    parameters: dict[str, JsonValue] = {
        "embedding": geometry.model_dump(mode="json"),
        "match": matching.model_dump(mode="json"),
        "power": power,
        "center": center,
    }
    if threshold == 0:
        return EntropyResult(
            measure="fuzzy_entropy",
            value=None,
            status=Status.UNDEFINED,
            n_observations=len(templates.base.values),
            parameters=parameters,
            diagnostics={"threshold": threshold, "reason": "zero kernel width"},
        )
    base, pairs = _log_membership(
        templates.base,
        geometry,
        matching,
        threshold,
        power,
        center,
        live_bytes=templates.extended.values.nbytes,
    )
    extended, _ = _log_membership(
        templates.extended,
        geometry,
        matching,
        threshold,
        power,
        center,
        live_bytes=templates.base.values.nbytes,
    )
    value = base - extended if math.isfinite(base) and math.isfinite(extended) else None
    return EntropyResult(
        measure="fuzzy_entropy",
        value=value,
        status=Status.UNDEFINED if value is None else Status.FINITE,
        n_observations=len(templates.base.values),
        parameters=parameters,
        diagnostics={
            "threshold": threshold,
            "eligible_pairs": pairs,
            "log_base_membership": base if math.isfinite(base) else None,
            "log_extended_membership": extended if math.isfinite(extended) else None,
        },
    )
