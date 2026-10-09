# Copyright (c) 2026 Daniel Ari Friedman
"""Authenticate the actual pinned template distribution and rendering tools."""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
from importlib.metadata import distribution
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field

from antropy_hd.errors import ParameterError
from scripts.manuscript_profile import ManuscriptContext


class VcsIdentity(BaseModel):
    """PEP 610 identity of the installed source package."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    vcs: Literal["git"]
    commit_id: str = Field(pattern=r"^[0-9a-f]{40}$")
    requested_revision: str


class DirectIdentity(BaseModel):
    """The installer's source receipt, independent of an environment path."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    url: str
    vcs_info: VcsIdentity


class TemplateIdentity(BaseModel):
    """Exact upstream identity and authenticated installed Python/Lua source bytes."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    distribution: str
    version: str
    repository: str
    revision: str
    exemplar: str
    installed_source_sha256: dict[str, str]
    tools: dict[str, str]


def template_identity(context: ManuscriptContext) -> TemplateIdentity:
    """Require pinned VCS metadata and verify source files against installed RECORD hashes."""
    package = distribution("research-project-template")
    raw = package.read_text("direct_url.json")
    if raw is None:
        raise ParameterError("renderer", "Template distribution lacks pinned VCS provenance")
    identity = DirectIdentity.model_validate(json.loads(raw))
    expected = context.profile
    if identity.vcs_info.commit_id != expected.template_revision or identity.url.removesuffix(
        ".git"
    ) != expected.template_repository.removesuffix(".git"):
        raise ParameterError(
            "renderer", "Installed template source differs from configured revision"
        )
    sources: dict[str, str] = {}
    for item in package.files or ():
        name = str(item)
        if name.startswith("infrastructure/") and item.suffix in {".py", ".lua"}:
            content = package.locate_file(item).read_bytes()
            digest = hashlib.sha256(content).digest()
            recorded = item.hash
            if (
                recorded is None
                or recorded.mode != "sha256"
                or base64.urlsafe_b64encode(digest).decode().rstrip("=") != recorded.value
            ):
                raise ParameterError(
                    "renderer", f"Template installed source authentication failed: {name}"
                )
            sources[name] = digest.hex()
    if not sources:
        raise ParameterError("renderer", "Template source inventory is empty")
    tools: dict[str, str] = {}
    for name in ("pandoc", "pandoc-crossref", expected.compiler, "bibtex"):
        executable = shutil.which(name)
        if executable is None:
            raise ParameterError("renderer", f"Required rendering tool missing: {name}")
        process = subprocess.run(  # noqa: S603 - resolved fixed tool names; no shell.
            [executable, "--version"], check=True, capture_output=True, text=True, timeout=30
        )
        tools[name] = process.stdout.splitlines()[0]
    return TemplateIdentity(
        distribution="research-project-template",
        version=package.version,
        repository=identity.url,
        revision=identity.vcs_info.commit_id,
        exemplar=expected.template_exemplar,
        installed_source_sha256=sources,
        tools=tools,
    )
