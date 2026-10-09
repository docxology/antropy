# Copyright (c) 2026 Daniel Ari Friedman
"""Reject rehashed publication mutations using actual native-renderer fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError
from scripts.artifact_io import digest
from scripts.validate_publication import validate_publication, validate_renderer
from tests.artifact_fixtures import artifacts as artifacts  # noqa: PLC0414
from tests.artifact_fixtures import baseline as baseline  # noqa: PLC0414


def authenticated(root: Path) -> set[str]:
    payload = json.loads((root / "output/provenance/manifest.json").read_text())
    return {record["path"] for record in payload["artifacts"]}


def test_native_publication_is_semantically_bound(baseline: Path) -> None:
    validate_publication(baseline, authenticated(baseline))


@pytest.mark.parametrize("change", ["entrypoint", "revision", "source", "order", "pages"])
def test_renderer_receipt_cannot_substitute_identity(artifacts: Path, change: str) -> None:
    path = artifacts / "output/provenance/manuscript-template.json"
    receipt = json.loads(path.read_text())
    if change == "entrypoint":
        receipt["entrypoint"] = "unrelated.renderer"
    elif change == "revision":
        receipt["renderer"]["revision"] = "0" * 40
    elif change == "source":
        receipt["renderer"]["installed_source_sha256"] = {}
    elif change == "order":
        receipt["section_order"].reverse()
    else:
        receipt["pdf_pages"] = True
    path.write_text(json.dumps(receipt))
    with pytest.raises((ParameterError, ValidationError)):
        validate_renderer(artifacts)


@pytest.mark.parametrize("change", ["variables", "profile", "pdf", "tex", "toc"])
def test_receipt_binds_actual_file_bytes(artifacts: Path, change: str) -> None:
    paths = {
        "variables": "output/data/manuscript_variables.json",
        "profile": "docs/manuscript/project.yaml",
        "pdf": "output/pdf/antropy-methods.pdf",
        "tex": "output/manuscript/rendered.tex",
        "toc": "output/manuscript/rendered.toc",
    }
    path = artifacts / paths[change]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ParameterError):
        validate_renderer(artifacts)


def test_rehashed_section_cannot_change_hydrated_content(artifacts: Path) -> None:
    receipt_path = artifacts / "output/provenance/manuscript-template.json"
    receipt = json.loads(receipt_path.read_text())
    relative = f"output/manuscript/{receipt['section_order'][0]}"
    path = artifacts / relative
    path.write_text(path.read_text() + "\nInvented manuscript statement.\n")
    receipt["resolved_sources"][relative] = digest(path)
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ParameterError, match="section"):
        validate_renderer(artifacts)


@pytest.mark.parametrize("name", ["config.yaml", "preamble.md", "references.bib"])
def test_rendered_auxiliary_cannot_change_profile_inputs(artifacts: Path, name: str) -> None:
    path = artifacts / f"output/manuscript/{name}"
    path.write_text(path.read_text() + "\nChanged auxiliary source.\n")
    with pytest.raises(ParameterError):
        validate_renderer(artifacts)


def test_manuscript_value_cannot_diverge_from_data(artifacts: Path) -> None:
    path = artifacts / "output/data/manuscript_variables.json"
    values = json.loads(path.read_text())
    values["BASELINE_SEED"] = "invented"
    path.write_text(json.dumps(values))
    with pytest.raises(ParameterError, match="variables"):
        validate_publication(artifacts, authenticated(artifacts))


@pytest.mark.parametrize(
    "relative", ["output/manuscript/rendered.toc", "output/manuscript/rendered.tex"]
)
def test_native_compiler_files_must_be_authenticated(artifacts: Path, relative: str) -> None:
    paths = authenticated(artifacts)
    paths.remove(relative)
    with pytest.raises(ParameterError, match="unmanifested"):
        validate_publication(artifacts, paths)


def test_false_page_count_is_rejected(artifacts: Path) -> None:
    path = artifacts / "output/provenance/manuscript-template.json"
    receipt = json.loads(path.read_text())
    receipt["pdf_pages"] += 1
    path.write_text(json.dumps(receipt))
    with pytest.raises(ParameterError, match="page count"):
        validate_publication(artifacts, authenticated(artifacts))


@pytest.mark.parametrize(
    "diagnostic",
    ["! Undefined control sequence.", r"Overfull \hbox (109.7pt too wide) in paragraph"],
)
def test_native_diagnostic_failure_is_not_hidden_by_pdf(artifacts: Path, diagnostic: str) -> None:
    path = artifacts / "output/manuscript/rendered.log"
    path.write_text(path.read_text() + "\n" + diagnostic + "\n")
    with pytest.raises(ParameterError, match="LaTeX diagnostics"):
        validate_renderer(artifacts)
