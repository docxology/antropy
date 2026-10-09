# Copyright (c) 2026 Daniel Ari Friedman
"""Thin adapter to docxology/template's authenticated Pandoc/LaTeX PDF renderer."""

from __future__ import annotations

import json
import os
import re
import shutil
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.pdf_renderer import PDFRenderer
from pypdf import PdfReader

from antropy_hd.errors import ParameterError
from scripts.manuscript_data import file_sha256
from scripts.manuscript_profile import load_context
from scripts.template_provenance import template_identity

# Observed Pandoc width rounding was 0.11275 pt; permit only sub-point rounding,
# retaining diagnostics and rejecting overflow large enough to affect legibility.
MAX_OVERFULL_POINTS: Final[float] = 0.5


@contextmanager
def build_epoch(date: str) -> Generator[int]:
    """Pin the canonical renderer's supported epoch from the configured publication date."""
    try:
        epoch = int(datetime.fromisoformat(date).replace(tzinfo=UTC).timestamp())
    except ValueError as error:
        raise ParameterError("renderer", "Publication date is not a valid calendar date") from error
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = str(epoch)
    try:
        yield epoch
    finally:
        if previous is None:
            del os.environ["SOURCE_DATE_EPOCH"]
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous


def validate_latex_output(log: Path) -> None:
    """Reject diagnostic failures even when upstream wrote a superficially valid PDF."""
    if not log.is_file():
        raise ParameterError("renderer", "Final LaTeX diagnostic log is missing")
    text = log.read_text(encoding="utf-8")
    if re.search(
        r"^!|Missing character:|There were undefined references|Citation .* undefined|multiply[- ]defined",
        text,
        re.MULTILINE,
    ):
        raise ParameterError(
            "renderer", "LaTeX diagnostics contain errors, missing glyphs or unresolved references"
        )
    for line in text.splitlines():
        if line.startswith("Overfull "):
            matched = re.match(
                r"Overfull \\[hv]box \(([0-9]+(?:\.[0-9]+)?)pt too (?:wide|high)\)", line
            )
            if matched is None or float(matched.group(1)) > MAX_OVERFULL_POINTS:
                raise ParameterError(
                    "renderer", "LaTeX diagnostics contain unsupported or excessive layout overflow"
                )


def validate_images(root: Path, markdown: str) -> list[Path]:
    """Confine actual manuscript image references and reject malformed source syntax."""
    paths: list[Path] = []
    for line in markdown.splitlines():
        if line.strip().startswith("!["):
            matched = re.match(r"!\[.*\]\(([^)]+)\)", line.strip())
            if matched is None:
                raise ParameterError("manuscript", "Invalid manuscript image reference")
            path = (root / "docs/manuscript" / matched.group(1)).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ParameterError("manuscript", "Manuscript image escapes the repository")
            if not path.is_file():
                raise ParameterError("manuscript", f"Manuscript image is missing: {path.name}")
            paths.append(path)
    return paths


def render_pdf(root: Path, markdown: str, destination: Path) -> None:
    """Use real ordered section rendering, native mathematics, BibTeX and a generated TOC."""
    images = validate_images(root, markdown)
    context = load_context(root)
    identity = template_identity(context)
    directory = root / "output/manuscript"
    sources = [directory / section for section in context.profile.sections]
    if not all(path.is_file() for path in sources):
        raise ParameterError("manuscript", "Resolved section tree must exist before rendering")
    work = root / "work/manuscript-build"
    figures = work / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    staged: dict[str, str] = {}
    for source in images:
        previous = staged.get(source.name)
        digest = file_sha256(source)
        if previous is not None and previous != digest:
            raise ParameterError("manuscript", f"Figure basename collision: {source.name}")
        staged[source.name] = digest
        _ = shutil.copyfile(source, figures / source.name)
    configuration = RenderingConfig(
        manuscript_dir=str(directory),
        figures_dir=str(figures),
        output_dir=str(work),
        pdf_dir=str(work / "pdf"),
        latex_compiler=context.profile.compiler,
    )
    with build_epoch(context.profile.date) as epoch:
        rendered = PDFRenderer(configuration).render_combined(
            sources, directory, project_name=context.profile.document_id
        )
    validate_latex_output(rendered.parent / "_combined_manuscript.log")
    for suffix in ("tex", "toc", "log", "bbl", "blg"):
        source = rendered.parent / f"_combined_manuscript.{suffix}"
        if not source.is_file():
            raise ParameterError(
                "renderer", f"Required native rendering diagnostic missing: {suffix}"
            )
        _ = shutil.copyfile(source, directory / f"rendered.{suffix}")
    toc_path = rendered.parent / "_combined_manuscript.toc"
    tex_path = rendered.parent / "_combined_manuscript.tex"
    if not toc_path.is_file() or "\\contentsline" not in toc_path.read_text():
        raise ParameterError("manuscript", "Canonical renderer did not produce a real section TOC")
    reader = PdfReader(rendered)
    text = "\n".join(page.extract_text() for page in reader.pages)
    if not reader.pages or "Contents" not in text or "[?]" in text:
        raise ParameterError(
            "manuscript", "Rendered PDF lacks its TOC or contains unresolved citations"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    _ = shutil.copyfile(rendered, destination)
    receipt = {
        "schema_version": 1,
        "renderer": identity.model_dump(mode="json"),
        "entrypoint": "infrastructure.rendering.pdf_renderer.PDFRenderer.render_combined",
        "section_order": list(context.profile.sections),
        "resolved_sources": {
            path.relative_to(root).as_posix(): file_sha256(path) for path in sources
        },
        "profile_sha256": file_sha256(root / "docs/manuscript/project.yaml"),
        "variables_sha256": file_sha256(root / "output/data/manuscript_variables.json"),
        "staged_figure_sha256": staged,
        "tex_sha256": file_sha256(tex_path),
        "toc_sha256": file_sha256(toc_path),
        "pdf_sha256": file_sha256(destination),
        "pdf_pages": len(reader.pages),
        "source_date_epoch": epoch,
    }
    provenance = root / "output/provenance/manuscript-template.json"
    provenance.parent.mkdir(parents=True, exist_ok=True)
    _ = provenance.write_text(
        json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
