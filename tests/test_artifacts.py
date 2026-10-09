# Copyright (c) 2026 Daniel Ari Friedman
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from scripts.artifact_io import bounded_path
from scripts.build_manuscript import build
from scripts.render_manuscript import render_pdf
from scripts.run_experiments import ExperimentPlan, execute_experiments, synthesize
from scripts.validate_artifacts import validate

# Imported fixture exports are pytest's collection surface.
from tests.artifact_fixtures import artifacts as artifacts  # noqa: PLC0414
from tests.artifact_fixtures import baseline as baseline  # noqa: PLC0414
from tests.artifact_fixtures import mutate_json, prepare_project, rehash_record


def test_complete_pipeline_deterministic_and_bound(baseline: Path, tmp_path: Path) -> None:
    report = validate(baseline)
    assert report["authenticated_files"] >= 20
    assert report["pdf_pages"] >= 3
    root = tmp_path / "second"
    plan = prepare_project(root)
    rows = execute_experiments(root, plan)
    assert rows
    _ = build(root)
    for relative in ("output/data/results.csv", "output/pdf/antropy-methods.pdf"):
        assert (root / relative).read_bytes() == (baseline / relative).read_bytes()


@pytest.mark.parametrize(
    "relative",
    [
        "output/data/results.csv",
        "output/figures/hdse-tolerance.png",
        "output/reports/experiments.json",
        "output/pdf/antropy-methods.pdf",
        "docs/manuscript/manuscript.md",
        "output/data/noise-12.npy",
    ],
)
def test_missing_artifacts_fail_closed(artifacts: Path, relative: str) -> None:
    (artifacts / relative).unlink()
    with pytest.raises(ValueError, match="missing"):
        validate(artifacts)


def test_modified_bytes_rejected(artifacts: Path) -> None:
    path = artifacts / "output/data/results.csv"
    path.write_text(path.read_text() + "corruption")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate(artifacts)


@pytest.mark.parametrize(
    "operation", ["empty", "floor", "missing", "duplicate", "traversal", "absolute"]
)
def test_adversarial_manifests_rejected(artifacts: Path, operation: str) -> None:
    path = artifacts / "output/provenance/manifest.json"
    payload = json.loads(path.read_text())
    if operation == "empty":
        payload["artifacts"] = []
    elif operation == "floor":
        payload["required_artifacts"] = []
    elif operation == "missing":
        payload["artifacts"] = [
            record for record in payload["artifacts"] if record["path"] != "output/data/results.csv"
        ]
    elif operation == "duplicate":
        payload["artifacts"].append(payload["artifacts"][0])
    elif operation == "traversal":
        payload["artifacts"][0]["path"] = "../escape"
    else:
        payload["artifacts"][0]["path"] = str(artifacts / "uv.lock")
    path.write_text(json.dumps(payload))
    with pytest.raises((ValueError, ValidationError)):
        validate(artifacts)


@pytest.mark.parametrize(
    "operation",
    [
        "input_hash",
        "array_hash",
        "config_hash",
        "missing_result",
        "duplicate_field",
        "unmanifested",
    ],
)
def test_rehashed_json_still_fails_semantic_checks(artifacts: Path, operation: str) -> None:
    relative = "output/reports/experiments.json"
    payload = json.loads((artifacts / relative).read_text())
    first = payload["batches"][0]
    if operation == "input_hash":
        first["input_file_sha256"] = "0" * 64
    elif operation == "array_hash":
        first["batch"]["input_sha256"] = "0" * 64
    elif operation == "config_hash":
        first["batch"]["config_sha256"] = "0" * 64
    elif operation == "missing_result":
        first["batch"]["results"].pop(next(iter(first["batch"]["results"])))
    elif operation == "duplicate_field":
        payload["batches"].append(first)
    else:
        copied = artifacts / "output/data/unmanifested.npy"
        shutil.copyfile(artifacts / first["input_file"], copied)
        first["input_file"] = "output/data/unmanifested.npy"
    mutate_json(artifacts, relative, payload)
    with pytest.raises(
        ValueError,
        match=r"hash|identity|configuration|cover|Duplicate|duplicated|matrix|Unmanifested",
    ):
        validate(artifacts)


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("status", "infinite"),
        ("measure", "wrong"),
        ("value", "123"),
        ("input_sha256", "0" * 64),
        ("ndim", "99"),
        ("n_observations", "99"),
        ("parameters_json", "{}"),
        ("diagnostics_json", "{}"),
        ("structure", "wrong"),
        ("tolerance", "99"),
    ],
)
def test_rehashed_csv_cannot_change_estimates(
    artifacts: Path, column: str, replacement: str
) -> None:
    import csv

    relative = "output/data/results.csv"
    path = artifacts / relative
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    selected = next(row for row in rows if row["status"] == "finite")
    selected[column] = replacement
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    rehash_record(artifacts, relative)
    with pytest.raises(ValueError, match=r"CSV|Nonfinite"):
        validate(artifacts)


def test_rehashed_manuscript_and_png_controls(artifacts: Path) -> None:
    relative = "docs/manuscript/manuscript.md"
    path = artifacts / relative
    path.write_text(path.read_text().replace("Results CSV SHA-256:", "Removed binding:"))
    rehash_record(artifacts, relative)
    with pytest.raises(ValueError, match="bound"):
        validate(artifacts)


def test_rehashed_invalid_figure(artifacts: Path) -> None:
    relative = "output/figures/hdse-tolerance.png"
    (artifacts / relative).write_bytes(b"not a PNG image at all")
    rehash_record(artifacts, relative)
    with pytest.raises(ValueError, match="PNG"):
        validate(artifacts)


def test_symlink_path_escape_and_strict_nonfinite_json(artifacts: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    link = artifacts / "outside-link"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        bounded_path(artifacts, "outside-link")
    manifest = artifacts / "output/provenance/manifest.json"
    manifest.write_text('{"nonfinite":NaN}')
    with pytest.raises(ValueError, match="Out of range"):
        validate(artifacts)


@pytest.mark.parametrize(
    "change",
    [
        {"unused": 1},
        {"shapes": [[2]]},
        {"shapes": [[4], [4]]},
        {"shapes": [[100001]]},
        {"structures": ["noise", "noise"]},
        {"tolerances": [0.2, 0.2]},
        {"tolerances": [0]},
        {"noise_amplitude": float("nan")},
    ],
)
def test_plan_rejects_unconsumed_or_infeasible_controls(change: dict) -> None:
    payload = {"seed": 17, "shapes": [[8]], "structures": ["noise"], "tolerances": [0.2]}
    payload.update(change)
    with pytest.raises(ValidationError):
        ExperimentPlan.model_validate(payload)


def test_synthetic_controls_are_consumed() -> None:
    payload = {
        "seed": 17,
        "shapes": [[8]],
        "structures": ["periodic", "noise", "mixed"],
        "tolerances": [0.2],
    }
    plan = ExperimentPlan.model_validate(payload)
    for structure in plan.structures:
        first = synthesize(plan, (8,), structure)
        assert np.array_equal(first, synthesize(plan, (8,), structure))
        altered = ExperimentPlan.model_validate({**payload, "seed": 18})
        if structure != "periodic":
            assert not np.array_equal(first, synthesize(altered, (8,), structure))
    with pytest.raises(ValueError, match="not in tuple"):
        synthesize(plan, (8,), "unknown")
    assert not np.array_equal(
        synthesize(plan, (8,), "periodic"),
        synthesize(ExperimentPlan.model_validate({**payload, "period": 3}), (8,), "periodic"),
    )
    assert not np.array_equal(
        synthesize(plan, (8,), "mixed"),
        synthesize(
            ExperimentPlan.model_validate({**payload, "noise_amplitude": 0.8}), (8,), "mixed"
        ),
    )


def test_renderer_rejects_escape_and_malformed_images(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError, match="Invalid"):
        render_pdf(root, "![broken", root / "broken.pdf")
    with pytest.raises(ValueError, match="escapes"):
        render_pdf(root, "![escape](../../../../escape.png)", root / "broken.pdf")


def test_coherently_dropped_field_cannot_weaken_coverage(artifacts: Path) -> None:
    import csv

    relative = "output/reports/experiments.json"
    payload = json.loads((artifacts / relative).read_text())
    omitted = payload["batches"].pop()["field_id"]
    mutate_json(artifacts, relative, payload)
    csv_path = artifacts / "output/data/results.csv"
    with csv_path.open(newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["field_id"] != omitted]
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    rehash_record(artifacts, "output/data/results.csv")
    with pytest.raises(ValueError, match="matrix"):
        validate(artifacts)


@pytest.mark.parametrize("operation", ["seed", "config", "claim_hash", "claim_source"])
def test_live_plan_and_claim_bindings_cannot_be_rehashed_away(
    artifacts: Path, operation: str
) -> None:
    if operation in {"seed", "config"}:
        relative = "output/provenance/experiment-config.json"
        payload = json.loads((artifacts / relative).read_text())
        if operation == "seed":
            payload["plan"]["seed"] += 1
        else:
            payload["plan_sha256"] = "0" * 64
    else:
        relative = "docs/manuscript/claims.json"
        payload = json.loads((artifacts / relative).read_text())
        if operation == "claim_hash":
            payload["results_csv_sha256"] = "0" * 64
        else:
            payload["claims"][0]["sources"] = ["missing.md"]
    mutate_json(artifacts, relative, payload)
    with pytest.raises(ValueError, match=r"snapshot|ledger|Claim source"):
        validate(artifacts)
