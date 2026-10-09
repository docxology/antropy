# Copyright (c) 2026 Daniel Ari Friedman
"""Render restricted Markdown manuscripts into deterministic reportlab PDFs."""

from __future__ import annotations

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from antropy_hd.errors import ParameterError


def paragraph_text(text: str) -> str:
    """Escape manuscript prose for reportlab's restricted paragraph markup."""
    return escape(re.sub(r"`([^`]+)`", r"\1", text))


def render_image(root: Path, line: str) -> Image:
    """Resolve a confined Markdown figure reference and preserve aspect ratio."""
    image_path = re.fullmatch(r"!\[.*\]\((.*)\)", line)
    if image_path is None:
        raise ParameterError("manuscript", "Invalid manuscript image reference")
    path = (root / "docs/manuscript" / image_path.group(1)).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ParameterError("manuscript", "Manuscript image escapes the repository")
    image = Image(str(path))
    ratio = image.imageHeight / image.imageWidth
    image.drawWidth = 6.5 * inch
    image.drawHeight = image.drawWidth * ratio
    return image


def render_table(lines: list[str], index: int, styles: StyleSheet1) -> tuple[Table, int]:
    """Render a Markdown table with repeated headers and alternating row shading."""
    cells = []
    while index < len(lines) and lines[index].strip().startswith("|"):
        parts = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        if not all(re.fullmatch(r"[-:]+", cell) for cell in parts):
            cells.append(
                [Paragraph(paragraph_text(cell), styles["ManuscriptBody"]) for cell in parts]
            )
        index += 1
    if not cells:
        raise ParameterError("manuscript", "Manuscript table requires a header and data")
    table = Table(cells, colWidths=[6.5 * inch / len(cells[0])] * len(cells[0]), repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef3")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#8b9aab")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table, index


def render_pdf(root: Path, markdown: str, destination: Path) -> None:
    """Render headings, prose, tables and figures with readable page geometry."""
    styles = getSampleStyleSheet()
    styles["Heading2"].keepWithNext = True
    styles.add(
        ParagraphStyle(
            name="ManuscriptBody", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=8
        )
    )
    styles.add(
        ParagraphStyle(
            name="ManuscriptTitle",
            parent=styles["Title"],
            fontSize=19,
            leading=23,
            alignment=TA_CENTER,
            spaceAfter=15,
        )
    )
    story = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(paragraph_text(line[2:]), styles["ManuscriptTitle"]))
        elif line.startswith("## "):
            story.append(Paragraph(paragraph_text(line[3:]), styles["Heading2"]))
        elif line.startswith("!["):
            story.extend([render_image(root, line), Spacer(1, 8)])
        elif line.startswith("|"):
            table, index = render_table(lines, index, styles)
            story.extend([table, Spacer(1, 8)])
            continue
        else:
            paragraph = [line]
            while (
                index + 1 < len(lines)
                and lines[index + 1].strip()
                and not lines[index + 1].startswith(("#", "|", "!["))
            ):
                index += 1
                paragraph.append(lines[index].strip())
            story.append(Paragraph(paragraph_text(" ".join(paragraph)), styles["ManuscriptBody"]))
        index += 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(destination),
        pagesize=(8.5 * inch, 11 * inch),
        rightMargin=inch,
        leftMargin=inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="antropy: dimension-agnostic entropy methods",
        author="Daniel Ari Friedman",
        invariant=1,
    )

    def footer(canvas: Canvas, doc: BaseDocTemplate) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#516174"))
        canvas.drawString(inch, 0.35 * inch, "antropy-hd | computational methods report")
        canvas.drawRightString(7.5 * inch, 0.35 * inch, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
