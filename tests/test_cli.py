# Copyright (c) 2026 Daniel Ari Friedman
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from antropy_hd.cli import app, emit, load_array
from scripts.check_installed_wheel import WheelCheckError, check, run

runner = CliRunner()


def test_help_methods_and_version() -> None:
    assert runner.invoke(app, ["--help"]).exit_code == 0
    methods = runner.invoke(app, ["methods"])
    assert methods.exit_code == 0
    assert json.loads(methods.stdout)["shannon_entropy"]["input_kind"] == "probabilities"
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert runner.invoke(app, ["version"]).stdout.strip() == project["project"]["version"]


@pytest.mark.parametrize("extension", ["npy", "csv"])
def test_real_inputs_and_exclusive_output(tmp_path: Path, extension: str) -> None:
    path = tmp_path / f"field.{extension}"
    array = np.ones((5, 5))
    if extension == "npy":
        np.save(path, array)
    else:
        np.savetxt(path, array, delimiter=",")
    output = tmp_path / "nested/result.json"
    args = [
        "analyze",
        str(path),
        "--output",
        str(output),
        "--parameters",
        '{"embedding":{"shape":2},"match":{"tolerance":0.5}}',
    ]
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    payload = json.loads(output.read_text())
    assert payload["results"]["analysis"]["status"] == "undefined"
    assert payload["results"]["analysis"]["value"] is None
    assert payload["input_file_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert runner.invoke(app, args).exit_code == 2
    assert runner.invoke(app, [*args, "--overwrite"]).exit_code == 0


def test_batch_from_real_json_and_stdout(tmp_path: Path) -> None:
    path = tmp_path / "field.npy"
    np.save(path, np.arange(12.0))
    config = tmp_path / "config.json"
    config.write_text(
        '{"schema_version":1,"analyses":[{"id":"hist","measure":"histogram_entropy","parameters":{"bins":4}}]}'
    )
    result = runner.invoke(app, ["batch", str(path), "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["results"]["hist"]["value"] == pytest.approx(2.0)
    config.write_text('{"analyses":[{"id":"hist","measure":"hdse"}],"unused":true}')
    assert runner.invoke(app, ["batch", str(path), "--config", str(config)]).exit_code == 2


def test_plan_json_exclusive_output_and_resource_violations(tmp_path: Path) -> None:
    path = tmp_path / "nested/plan.json"
    arguments = ["plan", "--shape", "[6,7,8]", "--output", str(path)]
    result = runner.invoke(app, arguments)
    assert result.exit_code == 0, result.output
    payload = json.loads(path.read_text())
    assert payload["input_elements"] == 336
    assert payload["stages"][0]["templates"] == 120
    assert payload["feasible"] is True
    assert runner.invoke(app, arguments).exit_code == 2
    assert runner.invoke(app, [*arguments, "--overwrite"]).exit_code == 0
    result = runner.invoke(
        app, ["plan", "--shape", "[6,7,8]", "--config", '{"embedding":{"max_templates":2}}']
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["feasible"] is False


@pytest.mark.parametrize(
    ("shape", "config"),
    [("[true,7]", "{}"), ("[]", "{}"), ("notjson", "{}"), ("[6,7]", '{"unused":1}')],
)
def test_plan_rejects_invalid_shapes_and_unconsumed_config(shape: str, config: str) -> None:
    result = runner.invoke(app, ["plan", "--shape", shape, "--config", config])
    assert result.exit_code == 2
    assert "Error:" in result.stderr


@pytest.mark.parametrize(
    "parameters", ["{broken", "[]", '{"wrong":1}', '{"embedding":{"max_templates":2}}']
)
def test_analyze_invalid_parameter_json(tmp_path: Path, parameters: str) -> None:
    path = tmp_path / "data.npy"
    np.save(path, np.arange(20.0))
    result = runner.invoke(app, ["analyze", str(path), "--parameters", parameters])
    assert result.exit_code == 2
    assert "Error:" in result.stderr


def test_safe_loading_rejects_object_nonfinite_and_unsupported_files(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.npy"
    np.save(path, np.array([{"payload": "never unpickle"}], dtype=object))
    with pytest.raises(ValueError, match="allow_pickle"):
        load_array(path)
    np.save(path, np.array([1.0, np.nan]))
    with pytest.raises(ValueError, match="finite"):
        load_array(path)
    text = tmp_path / "data.txt"
    text.write_text("1,2")
    assert runner.invoke(app, ["analyze", str(text)]).exit_code == 2
    missing = tmp_path / "missing.npy"
    assert runner.invoke(app, ["analyze", str(missing)]).exit_code == 2
    with pytest.raises(FileNotFoundError):
        load_array(missing)


def test_csv_single_row_retains_grid_and_emit_io_failure(tmp_path: Path) -> None:
    path = tmp_path / "row.csv"
    path.write_text("1,2,3\n")
    assert load_array(path).shape == (1, 3)
    with pytest.raises(IsADirectoryError):
        emit({}, tmp_path, overwrite=True)


@pytest.mark.integration
def test_module_cli_real_subprocess_from_outside_checkout(tmp_path: Path) -> None:
    path = tmp_path / "field.npy"
    np.save(path, np.array([0.25, 0.75]))
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    process = subprocess.run(  # noqa: S603 - fixed interpreter/module; test-owned numeric input.
        [
            sys.executable,
            "-m",
            "antropy_hd.cli",
            "analyze",
            str(path),
            "--measure",
            "shannon_entropy",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    value = json.loads(process.stdout)["results"]["analysis"]["value"]
    assert value == pytest.approx(0.8112781244591328)


def test_wheel_checker_rejects_absent_artifact(tmp_path: Path) -> None:
    with pytest.raises(WheelCheckError) as failure:
        check(tmp_path / "missing.whl")
    assert failure.value.phase == "wheel"


def test_wheel_checker_preserves_real_subprocess_failure(tmp_path: Path) -> None:
    command = [
        sys.executable,
        "-c",
        "import sys; print('stdout-evidence'); print('stderr-evidence', file=sys.stderr); sys.exit(3)",
    ]
    with pytest.raises(WheelCheckError) as failure:
        run(command, tmp_path, dict(os.environ))
    assert failure.value.phase == "subprocess"
    assert "stdout-evidence" in str(failure.value)
    assert "stderr-evidence" in str(failure.value)
