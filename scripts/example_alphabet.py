# Copyright (c) 2026 Daniel Ari Friedman
"""Fixed-alphabet analysis reusing the library's shared symbolization boundary."""

from importlib.metadata import version
from itertools import pairwise
from typing import assert_never

import numpy as np

from antropy_hd.information import jensen_shannon_divergence, shannon_entropy
from antropy_hd.orchestration import array_sha256
from antropy_hd.statistical import StatisticalComplexityConfig, statistical_complexity
from antropy_hd.symbolization import SymbolizationConfig, fixed_alphabet
from scripts.example_models import AlphabetPlan
from scripts.example_reports import AlphabetReport


def categories_for(config: SymbolizationConfig) -> tuple[str, ...]:
    """Describe cut equality consistently with the shared symbolizer's policy."""
    cuts = config.cuts
    match config.side:
        case "right":
            return (
                f"x < {cuts[0]}",
                *(f"{left} <= x < {right}" for left, right in pairwise(cuts)),
                f"x >= {cuts[-1]}",
            )
        case "left":
            return (
                f"x <= {cuts[0]}",
                *(f"{left} < x <= {right}" for left, right in pairwise(cuts)),
                f"x > {cuts[-1]}",
            )
        case unreachable:
            assert_never(unreachable)


def run_alphabet(plan: AlphabetPlan) -> AlphabetReport:
    """Keep the full declared alphabet when calculating entropy and complexity."""
    field = np.random.default_rng(plan.seed).normal(
        plan.field.mean, plan.field.standard_deviation, size=plan.input_shape
    )
    for item in plan.overrides:
        field[item.index] = item.value
    symbols = fixed_alphabet(field, config=plan.symbolization)
    probabilities = np.asarray(symbols.probabilities, dtype=np.float64)
    alphabet_size = len(symbols.counts)
    uniform = np.full(alphabet_size, 1 / alphabet_size, dtype=np.float64)
    delta = np.zeros(alphabet_size, dtype=np.float64)
    delta[0] = 1
    config = StatisticalComplexityConfig(alphabet_size=alphabet_size, base=plan.entropy_base)
    return AlphabetReport(
        package_version=version("antropy-hd"),
        seed=plan.seed,
        input_shape=field.shape,
        input_sha256=array_sha256(field),
        cuts=plan.symbolization.cuts,
        cut_side=plan.symbolization.side,
        categories=categories_for(plan.symbolization),
        counts=symbols.counts,
        probabilities=symbols.probabilities,
        unoccupied_categories=tuple(i for i, count in enumerate(symbols.counts) if count == 0),
        shannon_bits=shannon_entropy(probabilities, base=plan.entropy_base),
        normalized_shannon=shannon_entropy(probabilities, base=plan.entropy_base, normalize=True),
        js_to_uniform_bits=jensen_shannon_divergence(
            probabilities, uniform, base=plan.entropy_base
        ),
        statistical_complexity=statistical_complexity(probabilities, config=config),
        uniform_reference_complexity=statistical_complexity(uniform, config=config),
        delta_reference_complexity=statistical_complexity(delta, config=config),
    )
