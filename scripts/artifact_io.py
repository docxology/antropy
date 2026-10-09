# Copyright (c) 2026 Daniel Ari Friedman
"""Confined artifact reads and strict byte/JSON boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import canonical_json


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
