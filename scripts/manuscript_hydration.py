# Copyright (c) 2026 Daniel Ari Friedman
"""Hydrate ordered sections through the template's real substitution boundary."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from infrastructure.rendering.manuscript_injection import substitute_manuscript_text
from pydantic import JsonValue

from antropy_hd.errors import ParameterError
from scripts.manuscript_profile import ManuscriptContext
from scripts.manuscript_tables import Variables


def section_texts(root: Path, context: ManuscriptContext, variables: Variables) -> list[str]:
    """Fail before writing when any declared source token has no producer/configuration value."""
    texts: list[str] = []
    for name in context.profile.sections:
        source = root / "docs/manuscript" / name
        resolved, unresolved = substitute_manuscript_text(
            source.read_text(encoding="utf-8"), variables
        )
        if unresolved:
            raise ParameterError("manuscript", f"Unresolved variables in {name}: {unresolved}")
        texts.append(resolved)
    return texts


def renderer_config(context: ManuscriptContext) -> Variables:
    """Expose a stable inspectable serialized rendering configuration."""
    profile, project = context.profile, context.project
    authors: list[JsonValue] = []
    for author in project.authors:
        record: dict[str, JsonValue] = {"name": author.name}
        if author.email is not None:
            record["email"] = author.email
        if author.name in profile.affiliations:
            record["affiliation"] = profile.affiliations[author.name]
        if author.name in profile.orcids:
            record["orcid"] = profile.orcids[author.name]
        authors.append(record)
    config: dict[str, JsonValue] = {
        "paper": {
            "title": profile.title,
            "subtitle": profile.subtitle,
            "version": project.version,
            "date": profile.date,
        },
        "authors": authors,
        "publication": {
            "repository_url": project.repository,
            "repository_label": "Source repository",
            "transmission_bookends": {"enabled": False},
        },
        "metadata": {
            "language": profile.language,
            "license": project.license,
            "documentclass": "article",
            "fontsize": f"{profile.font_size_pt}pt",
            "geometry": f"{profile.paper_size},margin={profile.margin_mm:g}mm",
        },
        "rendering": {
            "section_breaks": profile.section_breaks,
            "include_date": False,
            "figure_height_fraction": profile.figure_height_fraction,
            "front_matter_figure_height_fraction": profile.figure_height_fraction,
        },
    }
    return {"yaml": yaml.safe_dump(config, sort_keys=False)}


def hydrate(root: Path, context: ManuscriptContext, variables: Variables) -> list[Path]:
    """Write fully resolved source copies and exact auxiliary sources inside this project."""
    texts = section_texts(root, context, variables)
    directory = root / "output/manuscript"
    directory.mkdir(parents=True, exist_ok=True)
    sources: list[Path] = []
    for name, text in zip(context.profile.sections, texts, strict=True):
        path = directory / name
        _ = path.write_text(text, encoding="utf-8")
        sources.append(path)
    for name in ("preamble.md", "references.bib"):
        source = root / "docs/manuscript" / name
        if not source.is_file():
            raise ParameterError("manuscript", f"Required auxiliary source missing: {name}")
        _ = shutil.copyfile(source, directory / name)
    _ = (directory / "config.yaml").write_text(renderer_config(context)["yaml"], encoding="utf-8")
    data_path = root / "output/data/manuscript_variables.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    _ = data_path.write_text(
        json.dumps(variables, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return sources
