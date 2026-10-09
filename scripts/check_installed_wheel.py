#!/usr/bin/env -S uv run --script
# Copyright (c) 2026 Daniel Ari Friedman
# /// script
# requires-python = ">=3.14"
# dependencies = ["numpy>=2.3", "typer>=0.16"]
# ///
# How to run: install uv with https://docs.astral.sh/uv/getting-started/installation/
# uv run scripts/check_installed_wheel.py --wheel dist/antropy_hd-0.1.0-py3-none-any.whl
# chmod +x scripts/check_installed_wheel.py && ./scripts/check_installed_wheel.py --wheel PATH
"""Install a wheel in a real isolated environment and exercise the installed CLI."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

import numpy as np
import typer


class WheelCheckError(RuntimeError):
    """An installed distribution violates its observable file/CLI contract."""

    phase: str

    def __init__(self, phase: str, detail: str) -> None:
        """Attach the failed phase to a useful error message."""
        self.phase = phase
        super().__init__(f"{phase}: {detail}")


def run(command: list[str], cwd: Path, environment: dict[str, str]) -> str:
    """Execute a fixed argument vector, preserving stderr and nonzero status."""
    process = subprocess.run(  # noqa: S603 - fixed executable vectors; test-owned wheel/data paths.
        command, cwd=cwd, env=environment, capture_output=True, text=True, check=False
    )
    if process.returncode:
        raise WheelCheckError(
            "subprocess",
            f"{command[0]} exited {process.returncode}\n{process.stdout}\n{process.stderr}",
        )
    return process.stdout


def check(wheel: Path) -> None:
    """Prove imports and analysis work outside the source checkout."""
    uv = shutil.which("uv")
    if uv is None:
        raise WheelCheckError("environment", "uv executable is required")
    if wheel.suffix != ".whl" or not wheel.is_file():
        raise WheelCheckError("wheel", "provide one existing wheel")
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("VIRTUAL_ENV", None)
    with TemporaryDirectory(prefix="antropy-wheel-") as directory:
        temporary = Path(directory)
        isolated = temporary / "environment"
        _ = run([uv, "venv", "--python", sys.executable, str(isolated)], temporary, environment)
        binary = isolated / ("Scripts" if os.name == "nt" else "bin")
        python = binary / ("python.exe" if os.name == "nt" else "python")
        executable = binary / ("antropy-hd.exe" if os.name == "nt" else "antropy-hd")
        project = Path(__file__).resolve().parents[1]
        locked = run(
            [
                uv,
                "export",
                "--frozen",
                "--no-dev",
                "--no-emit-project",
                "--format",
                "requirements-txt",
            ],
            project,
            environment,
        )
        requirements = temporary / "locked-requirements.txt"
        requirements.write_text(locked, encoding="utf-8")
        _ = run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(python),
                "--no-deps",
                "--requirement",
                str(requirements),
                str(wheel.resolve()),
            ],
            temporary,
            environment,
        )
        module_path = Path(
            run(
                [str(python), "-c", "import antropy_hd; print(antropy_hd.__file__)"],
                temporary,
                environment,
            ).strip()
        )
        if not module_path.resolve().is_relative_to(isolated.resolve()):
            raise WheelCheckError("import", "module was loaded outside the isolated environment")
        fixture = temporary / "probabilities.npy"
        np.save(fixture, np.array([0.25, 0.75]), allow_pickle=False)
        payload = json.loads(
            run(
                [str(executable), "analyze", str(fixture), "--measure", "shannon_entropy"],
                temporary,
                environment,
            )
        )
        estimate = payload["results"]["analysis"]
        if estimate["status"] != "finite" or not math.isclose(
            estimate["value"], 0.8112781244591328, rel_tol=1e-12
        ):
            raise WheelCheckError("analysis", "installed CLI failed the analytical Shannon example")
        if payload["input_file_sha256"] != hashlib.sha256(fixture.read_bytes()).hexdigest():
            raise WheelCheckError("provenance", "installed CLI did not bind actual input bytes")
        _ = run([str(executable), "methods"], temporary, environment)
        version = run([str(executable), "version"], temporary, environment).strip()
        print(
            f"Installed-wheel CLI passed: {version}; isolated import and analytical result verified"
        )


def main(wheel: Annotated[Path, typer.Option(exists=True, dir_okay=False)]) -> None:
    """Validate one built wheel through its installed command line interface."""
    check(wheel)


if __name__ == "__main__":
    typer.run(main)
