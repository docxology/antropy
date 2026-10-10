# Copyright (c) 2026 Daniel Ari Friedman
"""Explicit whole-observation file comparisons with byte-bound resampling configuration."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.inference import permutation_test
from antropy_hd.inference_models import PermutationConfig
from antropy_hd.validation import as_real_array


def load_observations(path: Path) -> NDArray[np.float64]:
    """Accept only an explicit vector, never treating grid cells as inferred replicates."""
    if path.suffix.lower() == ".npy":
        array = as_real_array(np.load(path, allow_pickle=False))
    elif path.suffix.lower() == ".csv":
        array = as_real_array(np.loadtxt(path, delimiter=",", ndmin=1))
    else:
        raise ParameterError("input", "Inference inputs require .npy or .csv vectors")
    if array.ndim != 1:
        raise ParameterError("input", "Inference requires one value per independent observation")
    return array


def compare_files(first: Path, second: Path, config_path: Path) -> dict[str, JsonValue]:
    """Bind both actual input files and the exact consumed immutable test configuration."""
    config = PermutationConfig.model_validate_json(config_path.read_text(encoding="utf-8"))
    result = permutation_test(load_observations(first), load_observations(second), config=config)
    return {
        "test": result.model_dump(mode="json"),
        "first_file_sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
        "second_file_sha256": hashlib.sha256(second.read_bytes()).hexdigest(),
        "config_file_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
    }
