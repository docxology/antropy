# Copyright (c) 2026 Daniel Ari Friedman
"""File-oriented command line interface for strict JSON entropy analysis."""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Annotated

import numpy as np
import typer
from numpy.typing import NDArray
from pydantic import JsonValue, ValidationError

from antropy_hd._complexity import InputShape
from antropy_hd.cli_inference import compare_files
from antropy_hd.complexity import ComplexityConfig, estimate_complexity
from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import METHODS, AnalysisSpec, BatchConfig, canonical_json, run_batch
from antropy_hd.validation import as_real_array

app = typer.Typer(no_args_is_help=True, help="Dimension-agnostic entropy analysis.")


def load_array(path: Path) -> NDArray[np.float64]:
    """Read numeric NPY without pickle, or a comma-separated two-dimensional grid."""
    if path.suffix.lower() == ".npy":
        return as_real_array(np.load(path, allow_pickle=False))
    if path.suffix.lower() == ".csv":
        return as_real_array(np.loadtxt(path, delimiter=",", ndmin=2))
    raise ParameterError(
        "input", "Input must be .npy (arbitrary dimensions) or .csv (two-dimensional grid)"
    )


def emit(payload: JsonValue, output: Path | None, *, overwrite: bool) -> None:
    """Emit strict JSON, creating files exclusively unless replacement is requested."""
    rendered = canonical_json(payload) + "\n"
    if output is None:
        typer.echo(rendered, nl=False)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w" if overwrite else "x", encoding="utf-8") as stream:
        _ = stream.write(rendered)


def execute(input_path: Path, config: BatchConfig, output: Path | None, *, overwrite: bool) -> None:
    """Bind actual input file bytes to an analysis batch."""
    result = run_batch(load_array(input_path), config)
    payload = result.model_dump(mode="json")
    payload["input_file_sha256"] = hashlib.sha256(input_path.read_bytes()).hexdigest()
    emit(payload, output, overwrite=overwrite)


@app.command("analyze")
def analyze_command(
    input_path: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False)],
    measure: Annotated[str, typer.Option(help="Registered method; see methods.")] = "hdse",
    parameters: Annotated[
        str, typer.Option(help="JSON object of explicit method parameters.")
    ] = "{}",
    output: Annotated[
        Path | None, typer.Option(help="Strict JSON output; defaults to stdout.")
    ] = None,
    overwrite: Annotated[
        bool, typer.Option(help="Allow replacing an existing output file.")
    ] = False,
) -> None:
    """Analyze one real numeric file."""
    try:
        spec = AnalysisSpec(id="analysis", measure=measure, parameters=json.loads(parameters))
        execute(input_path, BatchConfig(analyses=(spec,)), output, overwrite=overwrite)
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


@app.command("batch")
def batch_command(
    input_path: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False)],
    config: Annotated[Path, typer.Option(exists=True, file_okay=True, dir_okay=False)],
    output: Annotated[Path | None, typer.Option()] = None,
    overwrite: Annotated[bool, typer.Option()] = False,
) -> None:
    """Run all configured analyses; reject unknown keys and duplicate ids."""
    try:
        parsed = BatchConfig.model_validate_json(config.read_text(encoding="utf-8"))
        execute(input_path, parsed, output, overwrite=overwrite)
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


@app.command("methods")
def methods_command() -> None:
    """List registry names and whether inputs are observations or probabilities."""
    emit(
        {name: {"input_kind": method.input_kind} for name, method in sorted(METHODS.items())},
        None,
        overwrite=False,
    )


@app.command("compare")
def compare_command(
    first: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False)],
    second: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False)],
    config: Annotated[Path, typer.Option(exists=True, file_okay=True, dir_okay=False)],
    output: Annotated[Path | None, typer.Option()] = None,
    overwrite: Annotated[bool, typer.Option()] = False,
) -> None:
    """Compare two explicit observation vectors using a fully declared permutation test."""
    try:
        emit(compare_files(first, second, config), output, overwrite=overwrite)
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


@app.command("version")
def version_command() -> None:
    """Print the installed distribution version."""
    typer.echo(package_version("antropy-hd"))


@app.command("plan")
def plan_command(
    shape: Annotated[
        str, typer.Option(help="JSON axis lengths, e.g. [64,64]; no array allocated.")
    ],
    config: Annotated[str, typer.Option(help="JSON ComplexityConfig.")] = "{}",
    output: Annotated[Path | None, typer.Option()] = None,
    overwrite: Annotated[bool, typer.Option()] = False,
) -> None:
    """Estimate scheduled work and conservative guards; report resource violations."""
    try:
        parsed_shape = InputShape.model_validate_json('{"shape":' + shape + "}").shape
        parsed_config = ComplexityConfig.model_validate_json(config)
        estimate = estimate_complexity(parsed_shape, parsed_config)
        payload = estimate.model_dump(mode="json")
        payload.update(
            feasible=estimate.feasible,
            guard_peak_bytes=estimate.guard_peak_bytes,
            distance_component_visits=estimate.distance_component_visits,
        )
        emit(payload, output, overwrite=overwrite)
    except (OSError, ValueError, TypeError, ValidationError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


if __name__ == "__main__":
    app()
