# Copyright (c) 2026 Daniel Ari Friedman
"""Distribution entropy of local-template distances, rather than amplitudes."""

import math

import numpy as np
from numpy.typing import ArrayLike
from pydantic import JsonValue

from antropy_hd.embedding import local_templates
from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.models import EmbeddingConfig, EntropyResult, MatchConfig, Status
from antropy_hd.pairs import pair_blocks
from antropy_hd.validation import as_real_array


def distribution_entropy(
    data: ArrayLike,
    *,
    embedding: EmbeddingConfig | None = None,
    match: MatchConfig | None = None,
    bins: int = 16,
    normalize: bool = True,
) -> EntropyResult:
    """Shannon entropy of normalized pair-distance histogram (natural log).

    Distances are divided by their observed maximum, then histogrammed on [0,1].
    All-zero distances give zero entropy. Pair selection and distance settings
    apply; threshold settings are rejected because this statistic has no radius.
    """
    if isinstance(bins, bool) or not isinstance(bins, int) or not 2 <= bins <= 100000:
        raise ParameterError("bins", "requires an integer between 2 and 100000")
    array = as_real_array(data)
    geometry = embedding or EmbeddingConfig()
    # Histogram counts, edges and NumPy's histogram working arrays remain live.
    histogram_bytes = bins * 64 + 4096
    available = geometry.max_memory_bytes - histogram_bytes
    if available < 1024:
        raise ResourceError("max_memory_bytes", "distance histogram exceeds configured workspace")
    workspace = EmbeddingConfig.model_validate(
        geometry.model_dump() | {"max_memory_bytes": available}
    )
    matching = match or MatchConfig()
    if (matching.tolerance, matching.relative, matching.ddof, matching.closed) != (
        0.2,
        True,
        0,
        False,
    ):
        raise ParameterError(
            "match", "distribution entropy has no threshold; use default radius fields"
        )
    templates = local_templates(array, workspace)
    maximum = 0.0
    pairs = 0
    for distances, eligible in pair_blocks(templates, workspace, matching):
        selected = distances[eligible]
        pairs += len(selected)
        if len(selected):
            maximum = max(maximum, float(np.max(selected)))
    if not math.isfinite(maximum):
        raise ParameterError("data", "pair distances exceed float64 range")
    histogram = np.zeros(bins, dtype=np.int64)
    for distances, eligible in pair_blocks(templates, workspace, matching):
        selected = distances[eligible]
        normalized = selected / maximum if maximum else selected
        histogram += np.histogram(normalized, bins=bins, range=(0.0, 1.0))[0]
    value = None
    if pairs:
        probabilities = histogram[histogram > 0] / pairs
        value = -float(np.sum(probabilities * np.log(probabilities)))
        if normalize:
            value /= math.log(bins)
    counts: list[JsonValue] = [int(entry) for entry in histogram]
    return EntropyResult(
        measure="distribution_entropy",
        value=value,
        status=Status.UNDEFINED if value is None else Status.FINITE,
        n_observations=len(templates.values),
        parameters={
            "embedding": geometry.model_dump(mode="json"),
            "match": matching.model_dump(mode="json"),
            "bins": bins,
            "normalize": normalize,
            "base": "e",
        },
        diagnostics={"eligible_pairs": pairs, "maximum_distance": maximum, "bin_counts": counts},
    )
