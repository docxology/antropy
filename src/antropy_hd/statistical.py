# Copyright (c) 2026 Daniel Ari Friedman
"""Statistical complexity on an explicitly declared, fixed probability alphabet."""

import math
from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from antropy_hd._information import parse_probabilities, shannon_value
from antropy_hd.errors import ParameterError
from antropy_hd.information import jensen_shannon_divergence
from antropy_hd.models import EntropyResult


class StatisticalComplexityConfig(BaseModel):
    """Fix the complete alphabet, including zero-mass cells, and logarithmic units."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    alphabet_size: StrictInt = Field(ge=2)
    base: float = Field(default=2.0, gt=1, allow_inf_nan=False)


def statistical_complexity(
    probabilities: ArrayLike, *, config: StatisticalComplexityConfig
) -> EntropyResult:
    """Return normalized Shannon entropy times normalized Jensen-Shannon divergence.

    The reference is uniform on all declared cells. Disequilibrium divides by
    JSD(delta, uniform), the maximum for this alphabet and equal mixture weights.
    This is a finite-alphabet descriptive statistic, not thermodynamic complexity.
    """
    array = parse_probabilities(probabilities)
    size = config.alphabet_size
    if array.size != size:
        raise ParameterError(
            "alphabet_size", "must equal all probability tensor cells, including zeros"
        )
    uniform = np.full(array.shape, 1 / size, dtype=np.float64)
    entropy = shannon_value(array, config.base)
    maximum_entropy = math.log(size) / math.log(config.base)
    delta_mixture = (size + 1) / (2 * size)
    mixture_entropy = -delta_mixture * math.log(delta_mixture) - (size - 1) / (2 * size) * math.log(
        1 / (2 * size)
    )
    maximum_divergence = (mixture_entropy - math.log(size) / 2) / math.log(config.base)
    divergence = jensen_shannon_divergence(array, uniform, base=config.base).as_float()
    normalized_entropy = entropy / maximum_entropy
    normalized_disequilibrium = divergence / maximum_divergence
    return EntropyResult(
        measure="statistical_complexity",
        value=normalized_entropy * normalized_disequilibrium,
        n_observations=size,
        parameters={
            "alphabet_size": size,
            "base": config.base,
            "zero_policy": "retain",
            "mixture_weight": 0.5,
        },
        diagnostics={
            "normalized_entropy": normalized_entropy,
            "normalized_disequilibrium": normalized_disequilibrium,
            "jensen_shannon_max": maximum_divergence,
            "positive_cells": int(np.count_nonzero(array)),
            "observation_kind": "probability_cells",
        },
    )
