# Copyright (c) 2026 Daniel Ari Friedman
"""Adversarial report-structure controls; synthetic counts are never publication receipts."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from antropy_hd.errors import ParameterError
from scripts.manuscript_data import json_source
from scripts.manuscript_profile import load_context
from scripts.manuscript_verification import coverage_percent, verification_variables
from scripts.render_manuscript import build_epoch, validate_latex_output
from tests.artifact_fixtures import artifacts as artifacts  # noqa: PLC0414
from tests.artifact_fixtures import baseline as baseline  # noqa: PLC0414


def write_verification(root: Path) -> Path:
    """Create structurally consistent unit controls over the actual fixture file inventory."""
    prefix = load_context(root).profile.verification_prefix
    directory = root / "output/reports/verification"
    directory.mkdir(exist_ok=True)
    for name, folder in (("source", "src/antropy_hd"), ("infrastructure", "scripts")):
        files = [path.relative_to(root).as_posix() for path in (root / folder).rglob("*.py")]
        summary = {
            "covered_lines": 1,
            "num_statements": 1,
            "covered_branches": 1,
            "num_branches": 1,
            "percent_covered": 100.0,
        }
        totals = {
            **{key: len(files) for key in summary if key != "percent_covered"},
            "percent_covered": 100.0,
        }
        payload = {
            "meta": {"branch_coverage": True},
            "totals": totals,
            "files": {name: {"summary": summary} for name in files},
        }
        (directory / f"{name}-coverage-{prefix}.json").write_text(json.dumps(payload))
    (directory / f"source-tests-{prefix}.log").write_text("30 passed")
    return directory


@pytest.mark.parametrize("log", ["2 failed, 30 passed", "1 error, 30 passed", "no test summary"])
def test_passing_count_does_not_hide_failure(artifacts: Path, log: str) -> None:
    directory = write_verification(artifacts)
    context = load_context(artifacts)
    (directory / f"source-tests-{context.profile.verification_prefix}.log").write_text(log)
    with pytest.raises(ParameterError):
        verification_variables(artifacts, context)


@pytest.mark.parametrize(
    "change", ["empty", "missing", "extra", "totals", "percent", "floor", "no_branches"]
)
def test_partial_or_inconsistent_coverage_cannot_support_claim(
    artifacts: Path, change: str
) -> None:
    directory = write_verification(artifacts)
    prefix = load_context(artifacts).profile.verification_prefix
    path = directory / f"source-coverage-{prefix}.json"
    payload = json.loads(path.read_text())
    if change == "empty":
        payload["files"] = {}
    elif change == "missing":
        payload["files"].pop(next(iter(payload["files"])))
    elif change == "extra":
        payload["files"]["src/unrelated.py"] = next(iter(payload["files"].values()))
    elif change == "totals":
        payload["totals"]["covered_lines"] += 1
    elif change == "percent":
        payload["totals"]["percent_covered"] = 99.0
    elif change == "floor":
        for item in payload["files"].values():
            item["summary"]["covered_lines"] = 0
        payload["totals"].update(covered_lines=0, percent_covered=50.0)
    else:
        payload["meta"]["branch_coverage"] = False
    path.write_text(json.dumps(payload))
    with pytest.raises((ParameterError, ValidationError)):
        coverage_percent(artifacts, path, "src/antropy_hd", 90)


def test_partial_receipt_set_is_rejected(artifacts: Path) -> None:
    directory = write_verification(artifacts)
    context = load_context(artifacts)
    (directory / f"source-tests-{context.profile.verification_prefix}.log").unlink()
    with pytest.raises(ParameterError):
        verification_variables(artifacts, context)


def test_null_required_producer_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "null.json"
    _ = path.write_text("null")
    with pytest.raises(ParameterError):
        json_source(path, required=True)


def test_epoch_restores_environment_on_error() -> None:
    original = os.environ.get("SOURCE_DATE_EPOCH")

    def fail_with_epoch() -> None:
        with build_epoch("2026-10-09") as epoch:
            assert int(os.environ["SOURCE_DATE_EPOCH"]) == epoch
            raise ParameterError("test", "deliberate failure")

    with pytest.raises(ParameterError):
        fail_with_epoch()
    assert os.environ.get("SOURCE_DATE_EPOCH") == original


@pytest.mark.parametrize(
    "line",
    [
        r"Overfull \hbox (109.77373pt too wide) in paragraph at lines 1079--1087",
        r"Overfull \vbox (1.0pt too high) detected at line 20",
        r"Overfull \hbox (NaNpt too wide)",
    ],
)
def test_excessive_or_unparseable_overflow_is_rejected(tmp_path: Path, line: str) -> None:
    log = tmp_path / "native.log"
    log.write_text(line)
    with pytest.raises(ParameterError):
        validate_latex_output(log)


def test_subpoint_rounding_and_underfull_diagnostics_are_accepted(tmp_path: Path) -> None:
    log = tmp_path / "native.log"
    log.write_text(
        "Underfull \\hbox (badness 10000)\nOverfull \\hbox (0.11275pt too wide) in alignment\n"
    )
    validate_latex_output(log)


def test_hashes_use_separate_short_lines(artifacts: Path) -> None:
    directory = write_verification(artifacts)
    context = load_context(artifacts)
    text = verification_variables(artifacts, context)["VERIFICATION_NARRATIVE"]
    block = text.split("```text\n", 1)[1].split("\n```", 1)[0]
    paths = (
        directory / f"source-coverage-{context.profile.verification_prefix}.json",
        directory / f"infrastructure-coverage-{context.profile.verification_prefix}.json",
        directory / f"source-tests-{context.profile.verification_prefix}.log",
    )
    from scripts.manuscript_data import file_sha256

    assert [line.split()[-1] for line in block.splitlines()] == [
        file_sha256(path) for path in paths
    ]
    assert max(map(len, block.splitlines())) <= 84


def test_real_unbreakable_text_blocks_pdf_acceptance(artifacts: Path) -> None:
    from scripts.build_manuscript import build

    source = artifacts / "docs/manuscript/00_abstract.md"
    source.write_text(source.read_text() + "\n\n\\mbox{" + "A" * 200 + "}\n")
    with pytest.raises(ParameterError):
        build(artifacts)
    log = artifacts / "work/manuscript-build/pdf/_combined_manuscript.log"
    assert "Overfull \\hbox" in log.read_text()
