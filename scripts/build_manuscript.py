#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd", "matplotlib>=3.10", "pyyaml>=6", "pypdf>=6", "typer>=0.16", "research-project-template[rendering]"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# research-project-template = { git = "https://github.com/docxology/template.git", rev = "d39f2478da2512b42ad961e98a5f3b854723f92e" }
# ///
# How to run: install uv at https://docs.astral.sh/uv/getting-started/installation/
# Frozen project environment: uv run python scripts/build_manuscript.py [OPTIONS]
# Standalone: uv run scripts/build_manuscript.py [OPTIONS]
# Executable: chmod +x scripts/build_manuscript.py && ./scripts/build_manuscript.py [OPTIONS]
# Copyright (c) 2026 Daniel Ari Friedman
"""Build configured manuscript sections with the pinned research-template renderer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final

import typer
from pydantic import JsonValue

from antropy_hd.orchestration import canonical_json

if __package__ in (None, ""):
    # Source-tree script execution shares the validated experiment model with module use.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.manuscript_claims import write_claims
from scripts.manuscript_data import file_sha256, read_data
from scripts.manuscript_hydration import hydrate, section_texts
from scripts.manuscript_profile import load_context
from scripts.manuscript_variables import publication_variables
from scripts.render_manuscript import render_pdf
from scripts.validate_benchmarks import validate_benchmarks
from scripts.validate_power import validate_power
from scripts.validate_study import validate_study

REQUIRED_ARTIFACTS: Final[tuple[str, ...]] = (
    "output/data/results.csv",
    "output/reports/experiments.json",
    "output/figures/hdse-tolerance.png",
    "output/provenance/experiment-config.json",
    "docs/manuscript/manuscript.md",
    "output/pdf/antropy-methods.pdf",
    "docs/manuscript/claims.json",
    "docs/manuscript/project.yaml",
    "output/data/manuscript_variables.json",
    "output/provenance/manuscript-template.json",
)


def manuscript_source(root: Path) -> str:
    """Resolve all declared sections without writing or recomputing scientific data."""
    context = load_context(root)
    data = read_data(root, context)
    values = publication_variables(root, context, data)
    return "\n\n".join(section_texts(root, context, values))


def write_manifest(root: Path) -> JsonValue:
    """Bind all required outputs plus every generated input and relevant source."""
    outputs: set[str] = set(REQUIRED_ARTIFACTS)
    outputs.remove("docs/manuscript/project.yaml")
    outputs.update(
        path.relative_to(root).as_posix() for path in (root / "output/data").glob("*.npy")
    )
    for directory in ("output/manuscript", "output/study", "output/power"):
        outputs.update(
            path.relative_to(root).as_posix()
            for path in (root / directory).rglob("*")
            if path.is_file()
        )
    inputs = {
        "experiment_plan.yaml",
        "domain_profile.yaml",
        "pyproject.toml",
        "uv.lock",
        "docs/implementation-contract.md",
        "docs/sources-related.md",
        "docs/manuscript/template.md",
        "docs/manuscript/project.yaml",
    }
    for folder in ("src", "scripts"):
        inputs.update(path.relative_to(root).as_posix() for path in (root / folder).rglob("*.py"))
    for pattern in ("*.py", "*.yaml", "*.md"):
        inputs.update(
            path.relative_to(root).as_posix() for path in (root / "examples").rglob(pattern)
        )
    inputs.update(path.relative_to(root).as_posix() for path in (root / "typings").rglob("*.pyi"))
    inputs.update(
        path.relative_to(root).as_posix()
        for path in (root / "docs/manuscript").glob("*")
        if path.is_file() and path.name not in {"manuscript.md", "claims.json", "project.yaml"}
    )
    for name in (
        "study_plan.yaml",
        "benchmark_plan.yaml",
        "power_plan.yaml",
        "docs/study-design.md",
        "docs/power-design.md",
        "docs/inference.md",
    ):
        if (root / name).is_file():
            inputs.add(name)
    prefix = load_context(root).profile.verification_prefix
    for name in (
        f"source-coverage-{prefix}.json",
        f"infrastructure-coverage-{prefix}.json",
        f"source-tests-{prefix}.log",
    ):
        relative = "output/reports/verification/" + name
        if (root / relative).is_file():
            inputs.add(relative)
    records: list[JsonValue] = []
    for relative in sorted(inputs | outputs):
        path = root / relative
        records.append(
            {
                "path": relative,
                "kind": "output" if relative in outputs else "input",
                "sha256": file_sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    payload: JsonValue = {
        "schema_version": 1,
        "required_artifacts": list(REQUIRED_ARTIFACTS),
        "artifacts": records,
    }
    destination = root / "output/provenance/manifest.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    _ = destination.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    return payload


def build(root: Path) -> Path:
    """Generate the source, render the PDF, and then hash the complete artifact set."""
    context = load_context(root)
    data = read_data(root, context)
    if data.study is not None:
        _ = validate_study(root)
    if data.benchmark is not None:
        _ = validate_benchmarks(root)
    if data.power is not None:
        _ = validate_power(root)
    values = publication_variables(root, context, data)
    _ = hydrate(root, context, values)
    markdown = "\n\n".join(section_texts(root, context, values))
    source = root / "docs/manuscript/manuscript.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    _ = source.write_text(markdown, encoding="utf-8")
    write_claims(root, data)
    pdf = root / "output/pdf/antropy-methods.pdf"
    render_pdf(root, markdown, pdf)
    _ = write_manifest(root)
    return pdf


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def main(root: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_ROOT) -> None:
    """Build from existing experiment artifacts; missing inputs are fatal."""
    pdf = build(root.resolve())
    print(f"Built {pdf}; manifest binds required artifacts and source inputs")


if __name__ == "__main__":
    typer.run(main)
