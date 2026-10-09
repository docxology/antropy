#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd>=0.2"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# Copyright (c) 2026 Daniel Ari Friedman
"""Analyze native 2D/3D fields with anisotropic windows and explicit pair exclusions."""

import sys
from importlib.metadata import version
from typing import ClassVar, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from antropy_hd import (
    EmbeddingConfig,
    EntropyResult,
    Exclusion,
    MatchConfig,
    hdse,
    svd_entropy,
    weighted_permutation_entropy,
)
from antropy_hd.orchestration import array_sha256


class SpatialCase(BaseModel):
    """One generated field and results retaining each measure's effective geometry."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    input_shape: tuple[int, ...]
    input_sha256: str
    embedding: EmbeddingConfig
    match: MatchConfig
    hdse: EntropyResult
    weighted_permutation: EntropyResult
    svd: EntropyResult


class SpatialReport(BaseModel):
    """Reproducible seed and actual computed results, including nonfinite statuses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal[1] = 1
    package_version: str
    seed: int
    cases: tuple[SpatialCase, ...]


def main() -> None:
    """Generate bounded fields, extract native windows and emit one strict JSON object."""
    seed = 20261009
    designs = (
        (
            (8, 9),
            EmbeddingConfig(shape=(2, 1), delay=(2, 1), stride=(1, 2), extend_axes=(0,)),
            MatchConfig(tolerance=1.5, exclusion=Exclusion.SELF, theiler=1, block_size=4),
        ),
        (
            (6, 7, 8),
            EmbeddingConfig(shape=(1, 2, 2), delay=(1, 2, 1), stride=(2, 1, 2), extend_axes=(1,)),
            MatchConfig(tolerance=1.5, exclusion=Exclusion.COORDINATE, theiler=1, block_size=4),
        ),
    )
    cases: list[SpatialCase] = []
    for shape, embedding, matching in designs:
        rng = np.random.default_rng(np.random.SeedSequence([seed, *shape]))
        axes = np.indices(shape, dtype=np.float64)
        field = np.sin(axes[0] / 2) + 0.2 * np.sum(axes, axis=0) + rng.normal(0, 0.25, size=shape)
        cases.append(
            SpatialCase(
                input_shape=shape,
                input_sha256=array_sha256(field),
                embedding=embedding,
                match=matching,
                hdse=hdse(field, embedding=embedding, match=matching),
                weighted_permutation=weighted_permutation_entropy(
                    field, embedding=embedding, normalize=True
                ),
                svd=svd_entropy(field, embedding=embedding, demean=True, normalize=True),
            )
        )
    report = SpatialReport(package_version=version("antropy-hd"), seed=seed, cases=tuple(cases))
    _ = sys.stdout.write(report.model_dump_json() + "\n")


if __name__ == "__main__":
    main()
