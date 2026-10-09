# Copyright (c) 2026 Daniel Ari Friedman
"""antropy: spatial entropy with explicit geometry and reproducible diagnostics."""

from antropy_hd.complexity import (
    ComplexityConfig,
    ComplexityEstimate,
    ComplexityMeasure,
    estimate_complexity,
)
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
from antropy_hd.statistical import StatisticalComplexityConfig, statistical_complexity
from antropy_hd.template_entropy import approximate_entropy, fuzzy_entropy, hdse, sample_entropy

__version__ = "0.2.0"

__all__ = [
    "AntropyError",
    "ComplexityConfig",
    "ComplexityEstimate",
    "ComplexityMeasure",
    "EmbeddingConfig",
    "EntropyResult",
    "Exclusion",
    "MatchConfig",
    "Metric",
    "ParameterError",
    "ResourceError",
    "StatisticalComplexityConfig",
    "Status",
    "approximate_entropy",
    "coarse_grain",
    "conditional_entropy",
    "distribution_entropy",
    "estimate_complexity",
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
    "statistical_complexity",
    "svd_entropy",
    "tsallis_entropy",
    "weighted_permutation_entropy",
]
