#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["antropy-hd", "matplotlib>=3.10", "pyyaml>=6", "reportlab>=4", "typer>=0.16"]
# [tool.uv.sources]
# antropy-hd = { path = "..", editable = true }
# ///
# How to run: install uv at https://docs.astral.sh/uv/getting-started/installation/
# Frozen project environment: uv run python scripts/build_manuscript.py [OPTIONS]
# Standalone: uv run scripts/build_manuscript.py [OPTIONS]
# Executable: chmod +x scripts/build_manuscript.py && ./scripts/build_manuscript.py [OPTIONS]
# Copyright (c) 2026 Daniel Ari Friedman
"""Build an inspectable Markdown manuscript and deterministic standalone PDF."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Annotated, Final

import typer
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import canonical_json

if __package__ in (None, ""):
    # Source-tree script execution shares the validated experiment model with module use.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.render_manuscript import render_pdf
from scripts.run_experiments import ExperimentPlan

REQUIRED_ARTIFACTS: Final[tuple[str, ...]] = (
    "output/data/results.csv",
    "output/reports/experiments.json",
    "output/figures/hdse-tolerance.png",
    "output/provenance/experiment-config.json",
    "docs/manuscript/manuscript.md",
    "output/pdf/antropy-methods.pdf",
    "docs/manuscript/claims.json",
)


def file_sha256(path: Path) -> str:
    """Hash actual bytes without relying on cached metadata."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manuscript_source(root: Path) -> str:
    """Bind the narrative and displayed estimates to the generated CSV."""
    csv_path = root / "output/data/results.csv"
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ParameterError("manuscript", "A manuscript requires nonempty experiment results")
    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in ("finite", "undefined", "infinite")
    }
    table = [
        "| Dimension | Structure | Relative radius r | HDSE (nats) | Status |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        if row["measure"] == "hdse":
            value = f"{float(row['value']):.6g}" if row["value"] else "-"
            table.append(
                f"| {row['ndim']} | {row['structure']} | {row['tolerance']} | {value} | {row['status']} |"
            )
    snapshot = json.loads((root / "output/provenance/experiment-config.json").read_text())
    plan = ExperimentPlan.model_validate(snapshot["plan"])
    template = (root / "docs/manuscript/template.md").read_text(encoding="utf-8")
    return template.format(
        row_count=len(rows),
        finite_count=counts["finite"],
        undefined_count=counts["undefined"],
        infinite_count=counts["infinite"],
        hdse_table="\n".join(table),
        csv_hash=file_sha256(csv_path),
        shapes=", ".join(" x ".join(map(str, shape)) for shape in plan.shapes),
        embedding_shape=plan.embedding_shape,
        tolerances=", ".join(map(str, plan.tolerances)),
    )


def write_manifest(root: Path) -> JsonValue:
    """Bind all required outputs plus every generated input and relevant source."""
    outputs = set(REQUIRED_ARTIFACTS)
    outputs.update(
        path.relative_to(root).as_posix() for path in (root / "output/data").glob("*.npy")
    )
    inputs = {
        "experiment_plan.yaml",
        "domain_profile.yaml",
        "pyproject.toml",
        "uv.lock",
        "docs/implementation-contract.md",
        "docs/sources-related.md",
        "docs/manuscript/template.md",
    }
    for folder in ("src", "scripts"):
        inputs.update(path.relative_to(root).as_posix() for path in (root / folder).rglob("*.py"))
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
    payload = {
        "schema_version": 1,
        "required_artifacts": list(REQUIRED_ARTIFACTS),
        "artifacts": records,
    }
    destination = root / "output/provenance/manifest.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    return payload


def build(root: Path) -> Path:
    """Generate the source, render the PDF, and then hash the complete artifact set."""
    markdown = manuscript_source(root)
    source = root / "docs/manuscript/manuscript.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(markdown, encoding="utf-8")
    claims = {
        "schema_version": 1,
        "results_csv_sha256": file_sha256(root / "output/data/results.csv"),
        "claims": [
            {
                "id": "hdse-contract",
                "kind": "method",
                "sources": ["docs/implementation-contract.md"],
            },
            {"id": "related-contracts", "kind": "method", "sources": ["docs/sources-related.md"]},
            {
                "id": "synthetic-estimates",
                "kind": "measured",
                "sources": ["output/data/results.csv", "output/reports/experiments.json"],
            },
            {
                "id": "synthetic-design",
                "kind": "configuration",
                "sources": ["experiment_plan.yaml", "output/provenance/experiment-config.json"],
            },
        ],
    }
    (source.parent / "claims.json").write_text(canonical_json(claims) + "\n", encoding="utf-8")
    pdf = root / "output/pdf/antropy-methods.pdf"
    render_pdf(root, markdown, pdf)
    write_manifest(root)
    return pdf


DEFAULT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def main(root: Annotated[Path, typer.Option(file_okay=False)] = DEFAULT_ROOT) -> None:
    """Build from existing experiment artifacts; missing inputs are fatal."""
    pdf = build(root.resolve())
    print(f"Built {pdf}; manifest binds required artifacts and source inputs")


if __name__ == "__main__":
    typer.run(main)
