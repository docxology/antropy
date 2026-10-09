# Copyright (c) 2026 Daniel Ari Friedman
"""antropy: spatial entropy with explicit geometry and reproducible diagnostics."""

from antropy_hd.distribution import distribution_entropy
from antropy_hd.errors import AntropyError, ParameterError, ResourceError
from antropy_hd.information import (
    conditional_entropy,
    histogram_entropy,
    jensen_shannon_divergence,
    joint_entropy,
    mutual_information,
    renyi_entropy,
    shannon_entropy,
    tsallis_entropy,
)
from antropy_hd.models import EmbeddingConfig, EntropyResult, Exclusion, MatchConfig, Metric, Status
from antropy_hd.multiscale import coarse_grain, multiscale_entropy
from antropy_hd.ordinal import permutation_entropy, weighted_permutation_entropy
from antropy_hd.spectral import spectral_entropy, svd_entropy
from antropy_hd.template_entropy import approximate_entropy, fuzzy_entropy, hdse, sample_entropy

__version__ = "0.1.0"

__all__ = [
    "AntropyError",
    "EmbeddingConfig",
    "EntropyResult",
    "Exclusion",
    "MatchConfig",
    "Metric",
    "ParameterError",
    "ResourceError",
    "Status",
    "approximate_entropy",
    "coarse_grain",
    "conditional_entropy",
    "distribution_entropy",
    "fuzzy_entropy",
    "hdse",
    "histogram_entropy",
    "jensen_shannon_divergence",
    "joint_entropy",
    "multiscale_entropy",
    "mutual_information",
    "permutation_entropy",
    "renyi_entropy",
    "sample_entropy",
    "shannon_entropy",
    "spectral_entropy",
    "svd_entropy",
    "tsallis_entropy",
    "weighted_permutation_entropy",
]
