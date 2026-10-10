# Copyright (c) 2026 Daniel Ari Friedman
"""Real vector files and subprocess errors prove the comparison CLI's contracts."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from antropy_hd import PermutationConfig, permutation_test
from antropy_hd.cli_inference import load_observations
from antropy_hd.errors import ParameterError


def _compare(tmp_path: Path, *, output: bool = False) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "-m",
        "antropy_hd.cli",
        "compare",
        str(tmp_path / "first.npy"),
        str(tmp_path / "second.csv"),
        "--config",
        str(tmp_path / "config.json"),
    ]
    if output:
        command.extend(("--output", str(tmp_path / "result.json")))
    return subprocess.run(command, text=True, capture_output=True, check=False)  # noqa: S603 -- actual current interpreter and temporary scientific files


def _inputs(tmp_path: Path) -> PermutationConfig:
    np.save(tmp_path / "first.npy", np.array([1, 2, 3, 4], dtype=np.float64))
    np.savetxt(tmp_path / "second.csv", [3, 4, 5, 6], delimiter=",")
    config = PermutationConfig(seed=81, mode="exact")
    _ = (tmp_path / "config.json").write_text(config.model_dump_json())
    return config


def test_actual_comparison_and_hash_binding(tmp_path: Path) -> None:
    config = _inputs(tmp_path)
    command = _compare(tmp_path)
    assert command.returncode == 0, command.stderr
    payload = json.loads(command.stdout)
    assert payload["test"] == permutation_test(
        [1, 2, 3, 4], [3, 4, 5, 6], config=config
    ).model_dump(mode="json")
    for name in ("first", "second", "config"):
        filename = name + (".npy" if name == "first" else ".csv" if name == "second" else ".json")
        assert (
            payload[f"{name}_file_sha256"]
            == hashlib.sha256((tmp_path / filename).read_bytes()).hexdigest()
        )


def test_comparison_exclusive_output_and_real_failures(tmp_path: Path) -> None:
    _ = _inputs(tmp_path)
    assert _compare(tmp_path, output=True).returncode == 0
    assert _compare(tmp_path, output=True).returncode == 2
    before = (tmp_path / "result.json").read_bytes()
    np.save(tmp_path / "first.npy", np.ones((2, 2)))
    command = _compare(tmp_path)
    assert command.returncode == 2
    assert "one value per independent observation" in command.stderr
    assert (tmp_path / "result.json").read_bytes() == before
    _ = (tmp_path / "config.json").write_text('{"seed":81,"typo":true}')
    command = _compare(tmp_path)
    assert command.returncode == 2
    assert "typo" in command.stderr


@pytest.mark.parametrize("extension", [".txt", ".json"])
def test_unknown_vector_format(tmp_path: Path, extension: str) -> None:
    path = tmp_path / ("input" + extension)
    _ = path.write_text("1,2")
    with pytest.raises(ParameterError, match="vectors"):
        load_observations(path)
