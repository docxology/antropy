#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd", "matplotlib>=3.10", "pyyaml>=6", "typer>=0.16"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# How to run: install uv at https://docs.astral.sh/uv/getting-started/installation/
# Frozen project environment: uv run python scripts/run_experiments.py [OPTIONS]
# Standalone: uv run scripts/run_experiments.py [OPTIONS]
# Executable: chmod +x scripts/run_experiments.py && ./scripts/run_experiments.py [OPTIONS]
# Copyright (c) 2026 Daniel Ari Friedman
"""Run bounded, deterministic synthetic experiments from a validated YAML plan."""

from __future__ import annotations

import csv
import hashlib
import math
import sys
from pathlib import Path
from typing import Annotated, ClassVar, Final, Literal, TypedDict, assert_never

import numpy as np
import typer
import yaml
from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictInt, model_validator

from antropy_hd.errors import ParameterError
from antropy_hd.models import EntropyResult
from antropy_hd.orchestration import AnalysisSpec, BatchConfig, canonical_json, run_batch

if __package__ in (None, ""):
    # Direct source-tree scripts share the same plotting module as tests.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.plot_experiments import plot_results


class ExperimentPlan(BaseModel):
    """All experiment controls are explicit, validated and consumed."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False
    )
    schema_version: Literal[1] = 1
    seed: StrictInt = Field(ge=0)
    shapes: tuple[tuple[StrictInt, ...], ...] = Field(min_length=1)
    structures: tuple[Literal["periodic", "noise", "mixed"], ...] = Field(min_length=1)
    tolerances: tuple[float, ...] = Field(min_length=1)
    embedding_shape: StrictInt = Field(default=2, ge=1)
    period: float = Field(default=8.0, gt=0)
    noise_amplitude: float = Field(default=0.35, gt=0)
    histogram_bins: StrictInt = Field(default=16, ge=2)
    max_templates: StrictInt = Field(default=1000, ge=2)
    max_pairs: StrictInt = Field(default=500000, ge=1)

    @model_validator(mode="after")
    def validate_geometry(self) -> ExperimentPlan:
        """Reject empty, duplicate, infeasible or excessively large designs."""
        if len(set(self.shapes)) != len(self.shapes):
            raise ParameterError("shapes", "Experiment shapes must be unique")
        if len(set(self.structures)) != len(self.structures):
            raise ParameterError("structures", "Structures must be unique")
        if len(set(self.tolerances)) != len(self.tolerances) or min(self.tolerances) <= 0:
            raise ParameterError("tolerances", "Tolerances must be unique and positive")
        for shape in self.shapes:
            if not shape or min(shape) <= self.embedding_shape:
                raise ParameterError(
                    "shapes", "Each spatial axis must support the extended template"
                )
            if math.prod(shape) > 100000:
                raise ParameterError(
                    "shapes", "Synthetic input exceeds the 100000-element experiment budget"
                )
        return self


def sha256(path: Path) -> str:
    """Hash actual file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


type Structure = Literal["periodic", "noise", "mixed"]


class ExperimentRow(TypedDict):
    """Flat result row with estimator and provenance fields."""

    field_id: str
    ndim: int
    shape: str
    structure: Structure
    analysis_id: str
    measure: str
    tolerance: float | None
    value: float | None
    status: str
    n_observations: int
    input_sha256: str
    config_sha256: str
    parameters_json: str
    diagnostics_json: str


def analyses_for(plan: ExperimentPlan) -> tuple[AnalysisSpec, ...]:
    """Specify the complete expected method/tolerance matrix from the plan."""
    embedding: dict[str, JsonValue] = {
        "shape": plan.embedding_shape,
        "max_templates": plan.max_templates,
        "max_pairs": plan.max_pairs,
    }
    analyses = [
        AnalysisSpec(
            id=f"hdse-r{tolerance:g}",
            measure="hdse",
            parameters={"embedding": embedding, "match": {"tolerance": tolerance}},
        )
        for tolerance in plan.tolerances
    ]
    analyses.extend(
        [
            AnalysisSpec(
                id="histogram",
                measure="histogram_entropy",
                parameters={"bins": plan.histogram_bins},
            ),
            AnalysisSpec(
                id="permutation",
                measure="permutation_entropy",
                parameters={"embedding": embedding, "normalize": True},
            ),
            AnalysisSpec(id="spectral", measure="spectral_entropy", parameters={"normalize": True}),
        ]
    )
    return tuple(analyses)


def synthesize(plan: ExperimentPlan, shape: tuple[int, ...], structure: Structure) -> np.ndarray:
    """Build a periodic field, independent Gaussian field, or their explicit mixture."""
    coordinates = np.indices(shape, dtype=np.float64)
    periodic = np.sin(2 * np.pi * coordinates / plan.period).sum(axis=0) / math.sqrt(len(shape))
    seed = np.random.SeedSequence([plan.seed, *shape, plan.structures.index(structure)])
    noise = np.random.default_rng(seed).normal(size=shape)
    match structure:
        case "periodic":
            return periodic
        case "noise":
            return noise
        case "mixed":
            return periodic + plan.noise_amplitude * noise
        case unreachable:
            assert_never(unreachable)


def execute_experiments(root: Path, plan_path: Path) -> list[ExperimentRow]:
    """Write seeded inputs, strict JSON batches, a cross-measure CSV and one figure."""
    plan = ExperimentPlan.model_validate(yaml.safe_load(plan_path.read_text(encoding="utf-8")))
    output = root / "output"
    for folder in ("data", "figures", "reports", "provenance"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    snapshot = {"plan": plan.model_dump(mode="json"), "plan_sha256": sha256(plan_path)}
    (output / "provenance" / "experiment-config.json").write_text(
        canonical_json(snapshot) + "\n", encoding="utf-8"
    )
    rows: list[ExperimentRow] = []
    batches: list[JsonValue] = []
    for shape in plan.shapes:
        for structure in plan.structures:
            field_id = f"{structure}-{'x'.join(map(str, shape))}"
            array = synthesize(plan, shape, structure)
            input_path = output / "data" / f"{field_id}.npy"
            np.save(input_path, array, allow_pickle=False)
            analyses = analyses_for(plan)
            batch = run_batch(array, BatchConfig(analyses=analyses))
            batches.append(
                {
                    "field_id": field_id,
                    "input_file": input_path.relative_to(root).as_posix(),
                    "input_file_sha256": sha256(input_path),
                    "batch": batch.model_dump(mode="json"),
                }
            )
            for analysis in analyses:
                result = batch.results[analysis.id]
                match result:
                    case EntropyResult():
                        pass
                    case tuple():
                        raise ParameterError(
                            "experiments", "Experiments require scalar-result measures"
                        )
                    case unreachable:
                        assert_never(unreachable)
                tolerance = next(
                    (radius for radius in plan.tolerances if analysis.id == f"hdse-r{radius:g}"),
                    None,
                )
                rows.append(
                    {
                        "field_id": field_id,
                        "ndim": len(shape),
                        "shape": "x".join(map(str, shape)),
                        "structure": structure,
                        "analysis_id": analysis.id,
                        "measure": analysis.measure,
                        "tolerance": tolerance,
                        "value": result.value,
                        "status": str(result.status),
                        "n_observations": result.n_observations,
                        "input_sha256": batch.input_sha256,
                        "config_sha256": batch.config_sha256,
                        "parameters_json": canonical_json(result.parameters),
                        "diagnostics_json": canonical_json(result.diagnostics),
                    }
                )
    result_path = output / "reports" / "experiments.json"
    result_path.write_text(
        canonical_json({"schema_version": 1, "batches": batches}) + "\n", encoding="utf-8"
    )
    with (output / "data" / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    plot_results(rows, output / "figures" / "hdse-tolerance.png", plan)
    return rows


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def main(
    plan: Annotated[Path, typer.Option(exists=True, dir_okay=False)] = Path("experiment_plan.yaml"),
    root: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_ROOT,
) -> None:
    """Run the explicit experiment plan from the repository root."""
    rows = execute_experiments(root.resolve(), plan.resolve())
    print(f"Generated {len(rows)} measured rows with explicit finite/infinite/undefined statuses")


if __name__ == "__main__":
    typer.run(main)
