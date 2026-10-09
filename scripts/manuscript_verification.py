# Copyright (c) 2026 Daniel Ari Friedman
"""Validate complete measured coverage receipts before quantifying verification claims."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from antropy_hd.errors import ParameterError
from scripts.manuscript_data import file_sha256
from scripts.manuscript_profile import ManuscriptContext
from scripts.manuscript_tables import Variables, number


class CoverageCounts(BaseModel):
    """The line/branch projection required to independently recompute coverage."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="ignore", frozen=True, allow_inf_nan=False
    )
    covered_lines: StrictInt = Field(ge=0)
    num_statements: StrictInt = Field(ge=0)
    covered_branches: StrictInt = Field(ge=0)
    num_branches: StrictInt = Field(ge=0)
    percent_covered: float = Field(ge=0, le=100)


class CoverageFile(BaseModel):
    """Consume file summaries; detailed line, context and function tables remain producer data."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)
    summary: CoverageCounts


class CoverageMetadata(BaseModel):
    """Require the branch-inclusive reporting mode used by the project gates."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)
    branch_coverage: Literal[True]


class CoverageReceipt(BaseModel):
    """Exact file inventory and independently checkable coverage totals."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)
    meta: CoverageMetadata
    totals: CoverageCounts
    files: dict[str, CoverageFile]


def coverage_percent(root: Path, receipt_path: Path, folder: str, floor: float) -> float:
    """Reject partial inventories, vacuous totals, inconsistent counts and missed floors."""
    receipt = CoverageReceipt.model_validate_json(receipt_path.read_text())
    expected = {path.relative_to(root).as_posix() for path in (root / folder).rglob("*.py")}
    if not expected or set(receipt.files) != expected:
        raise ParameterError(
            "manuscript", "Coverage receipt does not cover the complete source inventory"
        )
    fields = ("covered_lines", "num_statements", "covered_branches", "num_branches")
    for field in fields:
        if sum(getattr(item.summary, field) for item in receipt.files.values()) != getattr(
            receipt.totals, field
        ):
            raise ParameterError("manuscript", "Coverage totals differ from file summaries")
    total = receipt.totals
    denominator = total.num_statements + total.num_branches
    if (
        denominator <= 0
        or total.covered_lines > total.num_statements
        or total.covered_branches > total.num_branches
    ):
        raise ParameterError("manuscript", "Coverage receipt is vacuous or has impossible counts")
    percent = 100 * (total.covered_lines + total.covered_branches) / denominator
    if (
        not math.isclose(percent, total.percent_covered, rel_tol=1e-12, abs_tol=1e-12)
        or percent < floor
    ):
        raise ParameterError(
            "manuscript", "Recorded verification coverage is inconsistent or below its floor"
        )
    return percent


def verification_variables(root: Path, context: ManuscriptContext) -> Variables:
    """Describe only complete passing receipts; absent receipts assert no quantified result."""
    prefix = context.profile.verification_prefix
    directory = root / "output/reports/verification"
    source = directory / f"source-coverage-{prefix}.json"
    infrastructure = directory / f"infrastructure-coverage-{prefix}.json"
    tests = directory / f"source-tests-{prefix}.log"
    present = tuple(path.is_file() for path in (source, infrastructure, tests))
    if not any(present):
        return {
            "VERIFICATION_NARRATIVE": "Verification receipts for this configured build have not yet been generated; no pass count or measured coverage is asserted here."
        }
    if not all(present):
        raise ParameterError("manuscript", "Configured verification receipt set is incomplete")
    log = tests.read_text()
    matches = re.findall(r"(\d+) passed", log)
    if not matches or re.search(r"\b\d+ (?:failed|errors?)\b", log):
        raise ParameterError("manuscript", "Verification log does not represent a passing test run")
    source_percent = coverage_percent(
        root, source, "src/antropy_hd", context.project.coverage_floor
    )
    infra_percent = coverage_percent(
        root, infrastructure, "scripts", context.profile.infrastructure_coverage_floor
    )
    digits = context.profile.numeric_digits
    text = f"The configured verification receipts report {matches[-1]} passing tests, {number(source_percent, digits)} percent source coverage and {number(infra_percent, digits)} percent infrastructure coverage. These are recorded runs, not a substitute for independent release review."
    identities = (
        f"Source coverage: {file_sha256(source)}\n"
        f"Infra coverage:  {file_sha256(infrastructure)}\n"
        f"Test log:        {file_sha256(tests)}"
    )
    text += (
        "\n\nReceipt identities (SHA-256):\n\n\\begingroup\\small\n\n```text\n"
        + identities
        + "\n```\n\n\\endgroup"
    )
    return {"VERIFICATION_NARRATIVE": text}
