#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd>=0.2"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# Copyright (c) 2026 Daniel Ari Friedman
"""Preserve zero categories and explicit tails in fixed-alphabet entropy/complexity."""

import sys
from importlib.metadata import version
from itertools import pairwise
from typing import ClassVar, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from antropy_hd import (
    EntropyResult,
    StatisticalComplexityConfig,
    jensen_shannon_divergence,
    shannon_entropy,
    statistical_complexity,
)
from antropy_hd.orchestration import array_sha256


class AlphabetReport(BaseModel):
    """Fixed cut geometry, all computed counts and the complete probability alphabet."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", allow_inf_nan=False
    )
    schema_version: Literal[1] = 1
    package_version: str
    seed: int
    input_shape: tuple[int, ...]
    input_sha256: str
    cuts: tuple[float, ...]
    cut_side: Literal["right"] = "right"
    categories: tuple[str, ...]
    counts: tuple[int, ...]
    probabilities: tuple[float, ...]
    unoccupied_categories: tuple[int, ...]
    shannon_bits: EntropyResult
    normalized_shannon: EntropyResult
    js_to_uniform_bits: EntropyResult
    statistical_complexity: EntropyResult
    uniform_reference_complexity: EntropyResult
    delta_reference_complexity: EntropyResult


def main() -> None:
    """Quantize a real generated array without adapting cuts or deleting zero bins."""
    seed = 20261009
    field = np.random.default_rng(seed).normal(0, 0.25, size=(12, 14))
    field[0, 0], field[0, 1] = -3, 3
    cuts = np.linspace(-2, 2, 15, dtype=np.float64)
    symbols = np.searchsorted(cuts, field, side="right")
    alphabet_size = len(cuts) + 1
    counts = np.bincount(symbols.ravel(), minlength=alphabet_size)
    probabilities = counts / field.size
    uniform = np.full(alphabet_size, 1 / alphabet_size, dtype=np.float64)
    delta = np.zeros(alphabet_size, dtype=np.float64)
    delta[0] = 1
    categories = (
        f"x < {float(cuts[0])}",
        *(f"{float(left)} <= x < {float(right)}" for left, right in pairwise(cuts)),
        f"x >= {float(cuts[-1])}",
    )
    config = StatisticalComplexityConfig(alphabet_size=alphabet_size)
    report = AlphabetReport(
        package_version=version("antropy-hd"),
        seed=seed,
        input_shape=field.shape,
        input_sha256=array_sha256(field),
        cuts=tuple(float(value) for value in cuts),
        categories=categories,
        counts=tuple(int(value) for value in counts),
        probabilities=tuple(float(value) for value in probabilities),
        unoccupied_categories=tuple(int(value) for value in np.flatnonzero(counts == 0)),
        shannon_bits=shannon_entropy(probabilities),
        normalized_shannon=shannon_entropy(probabilities, normalize=True),
        js_to_uniform_bits=jensen_shannon_divergence(probabilities, uniform),
        statistical_complexity=statistical_complexity(probabilities, config=config),
        uniform_reference_complexity=statistical_complexity(uniform, config=config),
        delta_reference_complexity=statistical_complexity(delta, config=config),
    )
    _ = sys.stdout.write(report.model_dump_json() + "\n")


if __name__ == "__main__":
    main()
