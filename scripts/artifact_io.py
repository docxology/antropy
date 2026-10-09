# Copyright (c) 2026 Daniel Ari Friedman
"""Confined artifact reads and strict byte/JSON boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import canonical_json


def replay_equivalent(array: NDArray[np.float64], reference: NDArray[np.float64]) -> bool:
    """Apply the declared finite float64 design-replay policy, preserving exact shape."""
    if array.shape != reference.shape:
        return False
    if not np.isfinite(array).all() or not np.isfinite(reference).all():
        return False
    budget = (16 + 8 * reference.ndim) * float(np.finfo(np.float64).eps)
    gamma = budget / (1 - budget)
    limit = 2 * gamma * np.maximum(1.0, np.abs(reference))
    return bool(np.all(np.abs(array - reference) <= limit))


def bounded_path(root: Path, relative: str) -> Path:
    """Reject absolute paths, traversal and escaping symlinks."""
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ParameterError("artifacts", f"Artifact path is not repository-relative: {relative}")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ParameterError("artifacts", f"Artifact path escapes repository: {relative}")
    if not resolved.is_file():
        raise ParameterError("artifacts", f"Required artifact missing: {relative}")
    return resolved


def digest(path: Path) -> str:
    """Hash actual file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> JsonValue:
    """Reject all nonfinite JSON numbers, including those outside model fields."""
    value = json.loads(path.read_text(encoding="utf-8"))
    _ = canonical_json(value)
    return value
