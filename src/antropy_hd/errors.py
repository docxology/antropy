# Copyright (c) 2026 Daniel Ari Friedman
"""Typed failures for invalid requests and infeasible exact computations."""

from dataclasses import dataclass
from typing import override


@dataclass(frozen=True, slots=True)
class AntropyError(ValueError):
    """A request cannot satisfy the declared numerical contract."""

    parameter: str
    reason: str

    @override
    def __str__(self) -> str:
        """Describe the invalid parameter and the violated contract."""
        return f"{self.parameter}: {self.reason}"


class ParameterError(AntropyError):
    """A parameter or numerical input is invalid."""


class ResourceError(AntropyError):
    """The exact computation exceeds an explicit resource limit."""
