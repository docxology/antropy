# Copyright (c) 2026 Daniel Ari Friedman
"""Real Pandoc controls for exact cost values and separate numeric columns."""

from __future__ import annotations

import json
import subprocess
from shutil import which

from antropy_hd.complexity import ComplexityConfig, estimate_complexity
from antropy_hd.models import EmbeddingConfig, MatchConfig
from scripts.manuscript_data import ComplexityReport
from scripts.manuscript_tables import cost_tables
from scripts.study_models import StudyComplexityRecord


def test_cost_table_numeric_columns_and_exact_counts_survive_pandoc() -> None:
    estimate = estimate_complexity(
        (336,),
        ComplexityConfig(
            measure="sample_entropy",
            embedding=EmbeddingConfig(shape=2, max_templates=1000, max_pairs=500000),
            match=MatchConfig(block_size=64),
        ),
    )
    report = ComplexityReport(
        schema_version=1,
        plan_sha256="0" * 64,
        records=(
            StudyComplexityRecord(
                original_shape=(6, 7, 8),
                geometry="flattened",
                analysis_id="sample-r2",
                estimate=estimate,
                guard_peak_bytes=estimate.guard_peak_bytes,
                distance_component_visits=estimate.distance_component_visits,
            ),
        ),
    )
    source = cost_tables(report)
    row = next(line for line in source.splitlines() if "| 334 | 3 |" in line)
    fields = [field.strip() for field in row.split("|")[1:-1]]
    assert fields[5:] == ["198348", "675488"]
    executable = which("pandoc")
    assert executable is not None
    process = subprocess.run(  # noqa: S603 - fixed argument vector, actual tool execution.
        [executable, "--from=markdown", "--to=json"],
        input=source,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    payload = json.loads(process.stdout)
    table = next(block for block in payload["blocks"] if block["t"] == "Table")
    alignments = [column[0]["t"] for column in table["c"][2]]
    assert alignments == ["AlignDefault", "AlignDefault", *["AlignRight"] * 5]


def test_disabled_cost_output_has_no_table() -> None:
    assert "|" not in cost_tables(None)
