# Copyright (c) 2026 Daniel Ari Friedman
"""Explicit source bindings for baseline and configured publication claims."""

from __future__ import annotations

from pathlib import Path

from pydantic import JsonValue

from antropy_hd.orchestration import canonical_json
from scripts.manuscript_data import PublicationData, file_sha256


def write_claims(root: Path, data: PublicationData) -> None:
    """Keep baseline identities and add producer-specific bindings when present."""
    claims: list[JsonValue] = [
        {"id": "hdse-contract", "kind": "method", "sources": ["docs/implementation-contract.md"]},
        {"id": "related-contracts", "kind": "method", "sources": ["docs/sources-related.md"]},
        {
            "id": "synthetic-estimates",
            "kind": "measured",
            "sources": ["output/data/results.csv", "output/reports/experiments.json"],
        },
        {
            "id": "synthetic-design",
            "kind": "configuration",
            "sources": ["experiment_plan.yaml", "output/provenance/experiment-config.json"],
        },
    ]
    if data.study is not None:
        claims.extend(
            [
                {
                    "id": "study-estimates",
                    "kind": "measured",
                    "sources": [
                        "output/study/results.csv",
                        "output/study/report.json",
                        "output/study/summary.json",
                    ],
                },
                {
                    "id": "study-design",
                    "kind": "configuration",
                    "sources": ["study_plan.yaml", "output/study/report.json"],
                },
            ]
        )
    if data.complexity is not None:
        claims.append(
            {
                "id": "complexity-plan",
                "kind": "method",
                "sources": [
                    "output/study/complexity.json",
                    "src/antropy_hd/complexity.py",
                    "src/antropy_hd/_complexity.py",
                ],
            }
        )
    if data.benchmark is not None:
        claims.append(
            {
                "id": "measured-runtime",
                "kind": "measured",
                "sources": ["benchmark_plan.yaml", "output/study/benchmark.json"],
            }
        )
    if data.power is not None:
        claims.extend(
            [
                {
                    "id": "power-design",
                    "kind": "configuration",
                    "sources": ["power_plan.yaml", "output/power/report.json"],
                },
                {
                    "id": "power-estimates",
                    "kind": "measured",
                    "sources": [
                        "output/power/report.json",
                        "output/power/decisions.csv",
                        "output/power/summary.csv",
                    ],
                },
                {
                    "id": "inference-method",
                    "kind": "method",
                    "sources": [
                        "docs/manuscript/11_inference_and_power.md",
                        "src/antropy_hd/inference.py",
                        "docs/manuscript/references.bib",
                    ],
                },
            ]
        )
    if (
        data.study is not None
        or data.benchmark is not None
        or data.complexity is not None
        or data.power is not None
    ):
        claims.append(
            {
                "id": "template-renderer",
                "kind": "configuration",
                "sources": [
                    "docs/manuscript/project.yaml",
                    "uv.lock",
                    "output/provenance/manuscript-template.json",
                ],
            }
        )
    payload: JsonValue = {
        "schema_version": 1,
        "results_csv_sha256": file_sha256(root / "output/data/results.csv"),
        "claims": claims,
    }
    _ = (root / "docs/manuscript/claims.json").write_text(
        canonical_json(payload) + "\n", encoding="utf-8"
    )
