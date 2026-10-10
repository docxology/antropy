# Copyright (c) 2026 Daniel Ari Friedman
"""Fixed finite alphabets that retain empty categories and unbounded amplitude tails."""

from __future__ import annotations

from typing import ClassVar, Literal

import numpy as np
from numpy.typing import ArrayLike
from pydantic import BaseModel, ConfigDict, Field, model_validator

from antropy_hd.errors import ParameterError
from antropy_hd.validation import as_real_array


class SymbolizationConfig(BaseModel):
    """Strictly increasing fixed cuts; no data-dependent refitting or deletion of zero bins."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    cuts: tuple[float, ...] = Field(min_length=1)
    side: Literal["left", "right"] = "right"

    @model_validator(mode="after")
    def increasing_cuts(self) -> SymbolizationConfig:
        """Prevent ambiguous intervals and category counts before assigning observations."""
        if any(left >= right for left, right in zip(self.cuts, self.cuts[1:], strict=False)):
            raise ParameterError("cuts", "Fixed cuts must be strictly increasing")
        return self


class SymbolizationResult(BaseModel):
    """The full declared alphabet, including both tails and every unoccupied category."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    config: SymbolizationConfig
    input_shape: tuple[int, ...]
    observations: int
    counts: tuple[int, ...]
    probabilities: tuple[float, ...]


def fixed_alphabet(data: ArrayLike, *, config: SymbolizationConfig) -> SymbolizationResult:
    """Map every finite observation to a configured category on an arbitrary-dimensional grid."""
    array = as_real_array(data)
    alphabet_size = len(config.cuts) + 1
    counts = np.bincount(
        np.searchsorted(config.cuts, array.ravel(), side=config.side), minlength=alphabet_size
    )
    return SymbolizationResult(
        config=config,
        input_shape=array.shape,
        observations=array.size,
        counts=tuple(int(value) for value in counts),
        probabilities=tuple(float(value) / array.size for value in counts),
    )
