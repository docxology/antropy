# Copyright (c) 2026 Daniel Ari Friedman
"""Require actual template provenance and exact data-driven publication bindings."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictInt
from pypdf import PdfReader

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import canonical_json
from scripts.artifact_io import digest, read_json
from scripts.manuscript_data import read_data
from scripts.manuscript_hydration import renderer_config, section_texts
from scripts.manuscript_profile import ManuscriptContext, load_context
from scripts.manuscript_variables import publication_variables
from scripts.render_manuscript import validate_latex_output
from scripts.template_provenance import TemplateIdentity, template_identity
from scripts.validate_benchmarks import validate_benchmarks
from scripts.validate_power import validate_power
from scripts.validate_study import validate_study


class RendererReceipt(BaseModel):
    """Strict projection of the native renderer's source and artifact receipt."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1]
    renderer: TemplateIdentity
    entrypoint: str
    section_order: tuple[str, ...]
    resolved_sources: dict[str, str]
    profile_sha256: str
    variables_sha256: str
    staged_figure_sha256: dict[str, str]
    tex_sha256: str
    toc_sha256: str
    pdf_sha256: str
    pdf_pages: StrictInt = Field(gt=0)
    source_date_epoch: StrictInt = Field(ge=0)


def renderer_receipt(root: Path) -> RendererReceipt:
    """Parse a nonvacuous receipt without coercing boolean page counts."""
    return RendererReceipt.model_validate_json(
        (root / "output/provenance/manuscript-template.json").read_text()
    )


def expected_claim_ids(root: Path) -> set[str]:
    """Derive mandatory claim identities from the selected and present producer sources."""
    context = load_context(root)
    data = read_data(root, context)
    ids = {"hdse-contract", "related-contracts", "synthetic-estimates", "synthetic-design"}
    if data.study is not None:
        ids.update({"study-estimates", "study-design"})
    if data.complexity is not None:
        ids.add("complexity-plan")
    if data.benchmark is not None:
        ids.add("measured-runtime")
    if data.power is not None:
        ids.update({"power-design", "power-estimates", "inference-method"})
    if (
        data.study is not None
        or data.complexity is not None
        or data.benchmark is not None
        or data.power is not None
    ):
        ids.add("template-renderer")
    return ids


def validate_renderer(root: Path) -> None:
    """Require receipt identities, all resolved sections and native compiler-output hashes."""
    context = load_context(root)
    receipt = renderer_receipt(root)
    installed = template_identity(context)
    if (
        receipt.entrypoint != "infrastructure.rendering.pdf_renderer.PDFRenderer.render_combined"
        or receipt.renderer.model_dump(exclude={"tools"}) != installed.model_dump(exclude={"tools"})
    ):
        raise ParameterError(
            "publication", "Actual renderer identity differs from the configured template"
        )
    if receipt.section_order != context.profile.sections:
        raise ParameterError(
            "publication", "Rendered section order differs from the complete profile"
        )
    if (
        receipt.variables_sha256 != digest(root / "output/data/manuscript_variables.json")
        or receipt.profile_sha256 != digest(root / "docs/manuscript/project.yaml")
        or receipt.pdf_sha256 != digest(root / "output/pdf/antropy-methods.pdf")
    ):
        raise ParameterError(
            "publication", "Renderer receipt does not bind current variables/profile/PDF"
        )
    expected = publication_variables(root, context, read_data(root, context))
    texts = section_texts(root, context, expected)
    for section, text in zip(context.profile.sections, texts, strict=True):
        source = f"output/manuscript/{section}"
        if (
            receipt.resolved_sources.get(source) != digest(root / source)
            or (root / source).read_text() != text
        ):
            raise ParameterError("publication", "A rendered section is missing or stale")
    validate_renderer_auxiliary(root, context, receipt)


def validate_renderer_auxiliary(
    root: Path, context: ManuscriptContext, receipt: RendererReceipt
) -> None:
    """Bind configuration, bibliography, preamble and compiler files to native inputs."""
    validate_latex_output(root / "output/manuscript/rendered.log")
    config = (root / "output/manuscript/config.yaml").read_text()
    if config != renderer_config(context)["yaml"]:
        raise ParameterError("publication", "Rendered configuration differs from the profile")
    for name in ("preamble.md", "references.bib"):
        if (root / f"output/manuscript/{name}").read_bytes() != (
            root / f"docs/manuscript/{name}"
        ).read_bytes():
            raise ParameterError("publication", "Rendered auxiliary source is stale")
    for field, path in (
        ("tex_sha256", "output/manuscript/rendered.tex"),
        ("toc_sha256", "output/manuscript/rendered.toc"),
    ):
        if getattr(receipt, field) != digest(root / path):
            raise ParameterError(
                "publication", "Compiler output differs from the actual renderer receipt"
            )


def validate_publication(root: Path, authenticated: set[str]) -> None:
    """Authenticate configured producers, resolved values, section order and native PDF outputs."""
    context = load_context(root)
    data = read_data(root, context)
    required = {
        "docs/manuscript/project.yaml",
        "output/data/manuscript_variables.json",
        "output/provenance/manuscript-template.json",
        "output/manuscript/config.yaml",
        "output/manuscript/rendered.tex",
        "output/manuscript/rendered.toc",
        "output/manuscript/rendered.log",
    }
    required.update(
        f"{folder}/{name}"
        for folder in ("docs/manuscript", "output/manuscript")
        for name in ("preamble.md", "references.bib")
    )
    required.update(f"docs/manuscript/{section}" for section in context.profile.sections)
    required.update(f"output/manuscript/{section}" for section in context.profile.sections)
    if data.study is not None:
        required.update(
            {
                "study_plan.yaml",
                "output/study/report.json",
                "output/study/results.csv",
                "output/study/summary.json",
            }
        )
        required.update(record.input_file for record in data.study.records)
        _ = validate_study(root)
    if data.complexity is not None:
        required.add("output/study/complexity.json")
    if data.benchmark is not None:
        required.update({"benchmark_plan.yaml", "output/study/benchmark.json"})
        required.update(record.input_file for record in data.benchmark.records)
        _ = validate_benchmarks(root)
    if data.power is not None:
        required.update(
            {
                "power_plan.yaml",
                "docs/power-design.md",
                "docs/inference.md",
                "output/power/report.json",
                "output/power/decisions.csv",
                "output/power/summary.csv",
            }
        )
        required.update(pool.input_file for pool in data.power.pools)
        _ = validate_power(root)
    for figure in context.profile.figures:
        if (
            figure.dependency == "baseline"
            or (figure.dependency == "study" and data.study is not None)
            or (figure.dependency == "benchmark" and data.benchmark is not None)
            or (figure.dependency == "power" and data.power is not None)
        ):
            required.add(figure.source)
    if not required <= authenticated:
        raise ParameterError(
            "publication", "Publication sources or configured producers are unmanifested"
        )
    expected = publication_variables(root, context, data)
    actual = read_json(root / "output/data/manuscript_variables.json")
    expected_json: dict[str, JsonValue] = dict(expected)
    if canonical_json(actual) != canonical_json(expected_json):
        raise ParameterError("publication", "Manuscript variables differ from authenticated data")
    validate_renderer(root)
    pdf = PdfReader(root / "output/pdf/antropy-methods.pdf")
    if len(pdf.pages) != renderer_receipt(root).pdf_pages or not pdf.outline:
        raise ParameterError("publication", "PDF page count or native document outline differs")
