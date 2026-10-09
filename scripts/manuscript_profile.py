# Copyright (c) 2026 Daniel Ari Friedman
"""Validated publication configuration and project metadata sources."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import ClassVar, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from antropy_hd.errors import ParameterError


class Author(BaseModel):
    """Authorship sourced from the project manifest, with configured affiliations."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    name: str
    email: str | None = None


class ProjectMetadata(BaseModel):
    """The publication-relevant projection of pyproject.toml."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    name: str
    version: str
    description: str
    license: str
    authors: tuple[Author, ...] = Field(min_length=1)
    repository: str
    coverage_floor: float


class ManuscriptFigure(BaseModel):
    """One required producer-owned figure and its manuscript citation."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    token: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    source: str
    label: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    caption: str
    dependency: Literal["baseline", "study", "benchmark"]
    float_page: bool = False


class ManuscriptProfile(BaseModel):
    """Every publication option is configured rather than embedded in prose."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    title: str
    subtitle: str
    document_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    affiliations: dict[str, str]
    orcids: dict[str, str]
    sections: tuple[str, ...] = Field(min_length=1)
    figures: tuple[ManuscriptFigure, ...]
    measure_labels: dict[str, str]
    template_repository: str
    template_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    template_exemplar: str
    study_required: bool
    complexity_required: bool
    benchmark_required: bool
    verification_prefix: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    infrastructure_coverage_floor: float = Field(ge=0, le=100)
    numeric_digits: int = Field(ge=3, le=12)
    language: str
    paper_size: Literal["a4paper", "letterpaper"]
    margin_mm: float = Field(gt=0, allow_inf_nan=False)
    font_size_pt: Literal[10, 11, 12]
    section_breaks: bool
    figure_height_fraction: float = Field(gt=0, le=1)
    compiler: Literal["xelatex", "lualatex"]


class ManuscriptContext(BaseModel):
    """Publication metadata and explicitly selected producer requirements."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    project: ProjectMetadata
    profile: ManuscriptProfile


def load_context(root: Path) -> ManuscriptContext:
    """Parse exact project/profile inputs and reject unknown or escaping options."""
    manifest = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = manifest["project"]
    metadata = ProjectMetadata.model_validate(
        {
            **{
                key: project[key]
                for key in ("name", "version", "description", "license", "authors")
            },
            "repository": project["urls"]["Repository"],
            "coverage_floor": manifest["tool"]["coverage"]["report"]["fail_under"],
        }
    )
    path = root / "docs/manuscript/project.yaml"
    profile = ManuscriptProfile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    names = {author.name for author in metadata.authors}
    if not set(profile.affiliations) <= names or not set(profile.orcids) <= names:
        raise ParameterError("manuscript", "Author configuration contains an undeclared author")
    for section in profile.sections:
        if Path(section).is_absolute() or ".." in Path(section).parts:
            raise ParameterError("manuscript", "Section path must be repository-relative")
        section_path = (path.parent / section).resolve()
        if not section_path.is_relative_to(path.parent.resolve()) or not section_path.is_file():
            raise ParameterError("manuscript", f"Missing or escaping section: {section}")
    tokens = [figure.token for figure in profile.figures]
    labels = [figure.label for figure in profile.figures]
    if (
        len(set(labels)) != len(labels)
        or len(set(tokens)) != len(tokens)
        or len(set(profile.sections)) != len(profile.sections)
    ):
        raise ParameterError("manuscript", "Figure tokens and sections must be unique")
    for figure in profile.figures:
        relative = Path(figure.source)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not (root / relative).resolve().is_relative_to(root.resolve())
        ):
            raise ParameterError(
                "manuscript", "Figure source path must remain inside the repository"
            )
    return ManuscriptContext(project=metadata, profile=profile)
