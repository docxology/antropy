# Copyright (c) 2026 Daniel Ari Friedman
"""Exact blocked distances; no approximate sampling or quadratic global matrix."""

from collections.abc import Iterator
from math import prod
from typing import assert_never

import numpy as np
from numpy.typing import NDArray

from antropy_hd.embedding import Templates
from antropy_hd.errors import ResourceError
from antropy_hd.models import EmbeddingConfig, Exclusion, MatchConfig, Metric


def distance_block(
    left: NDArray[np.float64], right: NDArray[np.float64], metric: Metric
) -> NDArray[np.float64]:
    """Compute distances without a block-by-block-by-feature temporary tensor."""
    distances = np.zeros((len(left), len(right)), dtype=np.float64)
    # WHY: an overflowing difference exceeds every allowed finite threshold.
    with np.errstate(over="ignore"):
        for column in range(left.shape[1]):
            delta = np.abs(left[:, column, None] - right[None, :, column])
            match metric:
                case Metric.CHEBYSHEV:
                    _ = np.maximum(distances, delta, out=distances)
                case Metric.EUCLIDEAN:
                    _ = np.hypot(distances, delta, out=distances)
                case Metric.CITYBLOCK:
                    distances += delta
                case unreachable:
                    assert_never(unreachable)
    return distances


def guard_pairs(
    templates: Templates, embedding: EmbeddingConfig, config: MatchConfig, *, live_bytes: int = 0
) -> None:
    """Reject pair or working-set requests beyond the declared hard limits."""
    count = len(templates.values)
    if count * (count - 1) // 2 > embedding.max_pairs:
        raise ResourceError("max_pairs", "candidate pair population exceeds configured limit")
    block = min(count, config.block_size)
    # Includes live templates, coordinates, distances, masks and per-axis scratch.
    storage = count * (prod(templates.shape) * 8 + templates.origins.shape[1] * 8)
    # Includes prior yielded arrays retained by consumers, kernel temporaries,
    # fuzzy selection/log-weight/exponential buffers, and NumPy object overhead.
    if storage + live_bytes + block * block * 160 + 4096 > embedding.max_memory_bytes:
        raise ResourceError("max_memory_bytes", "templates and pair blocks exceed configured limit")


def pair_blocks(
    templates: Templates, embedding: EmbeddingConfig, config: MatchConfig, *, live_bytes: int = 0
) -> Iterator[tuple[NDArray[np.float64], NDArray[np.bool_]]]:
    """Yield exact distances and eligible masks for unordered origin pairs."""
    guard_pairs(templates, embedding, config, live_bytes=live_bytes)
    count = len(templates.values)
    block = config.block_size
    for start in range(0, count, block):
        left = templates.values[start : start + block]
        left_origins = templates.origins[start : start + block]
        for other in range(start, count, block):
            right = templates.values[other : other + block]
            right_origins = templates.origins[other : other + block]
            eligible = np.ones((len(left), len(right)), dtype=np.bool_)
            if other == start:
                eligible &= np.triu(eligible, k=1)
            separation = np.zeros(eligible.shape, dtype=np.int64)
            for axis in range(templates.origins.shape[1]):
                delta = np.abs(left_origins[:, axis, None] - right_origins[None, :, axis])
                _ = np.maximum(separation, delta, out=separation)
                match config.exclusion:
                    case Exclusion.SELF:
                        pass
                    case Exclusion.COORDINATE:
                        eligible &= delta != 0
                    case unreachable:
                        assert_never(unreachable)
            eligible &= separation > config.theiler
            yield distance_block(left, right, config.metric), eligible


def match_counts(
    templates: Templates,
    embedding: EmbeddingConfig,
    config: MatchConfig,
    threshold: float,
    *,
    live_bytes: int = 0,
) -> tuple[int, int]:
    """Count matches and eligible unordered pairs exactly."""
    matches = 0
    eligible_pairs = 0
    for distances, eligible in pair_blocks(templates, embedding, config, live_bytes=live_bytes):
        close = distances <= threshold if config.closed else distances < threshold
        matches += int(np.count_nonzero(close & eligible))
        eligible_pairs += int(np.count_nonzero(eligible))
    return matches, eligible_pairs
