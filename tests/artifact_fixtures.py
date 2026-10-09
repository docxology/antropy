# Copyright (c) 2026 Daniel Ari Friedman
"""Reusable real-file experiment fixtures and deliberate authenticated mutations."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import JsonValue

from scripts.build_manuscript import build
from scripts.run_experiments import execute_experiments
from scripts.validate_artifacts import validate

REPOSITORY = Path(__file__).resolve().parents[1]


def prepare_project(root: Path) -> Path:
    root.mkdir()
    for folder in ("src", "scripts"):
        shutil.copytree(
            REPOSITORY / folder, root / folder, ignore=shutil.ignore_patterns("__pycache__")
        )
    shutil.copytree(REPOSITORY / "typings", root / "typings")
    (root / "docs").mkdir()
    for name in ("implementation-contract.md", "sources-related.md"):
        shutil.copyfile(REPOSITORY / "docs" / name, root / "docs" / name)
    shutil.copytree(REPOSITORY / "docs/manuscript", root / "docs/manuscript")
    profile_path = root / "docs/manuscript/project.yaml"
    profile = yaml.safe_load(profile_path.read_text())
    profile.update(study_required=False, complexity_required=False, benchmark_required=False)
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False))
    for name in ("domain_profile.yaml", "pyproject.toml", "uv.lock"):
        shutil.copyfile(REPOSITORY / name, root / name)
    plan = root / "experiment_plan.yaml"
    plan.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "seed": 17,
                "shapes": [[12], [5, 5]],
                "structures": ["periodic", "noise", "mixed"],
                "tolerances": [0.2, 1.0],
                "embedding_shape": 2,
                "period": 4.0,
                "noise_amplitude": 0.35,
                "histogram_bins": 4,
                "max_templates": 100,
                "max_pairs": 10000,
            }
        )
    )
    return plan


@pytest.fixture(scope="module")
def baseline(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("pipeline") / "project"
    plan = prepare_project(root)
    rows = execute_experiments(root, plan)
    assert len(rows) == 30
    _ = build(root)
    assert validate(root)["result_rows"] == 30
    return root


@pytest.fixture
def artifacts(tmp_path: Path, baseline: Path) -> Path:
    target = tmp_path / "project"
    shutil.copytree(baseline, target)
    return target


def rehash_record(root: Path, relative: str) -> None:
    manifest_path = root / "output/provenance/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    path = root / relative
    for artifact in manifest["artifacts"]:
        if artifact["path"] == relative:
            artifact["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            artifact["bytes"] = path.stat().st_size
    manifest_path.write_text(json.dumps(manifest))


def mutate_json(root: Path, relative: str, payload: JsonValue) -> None:
    (root / relative).write_text(json.dumps(payload))
    rehash_record(root, relative)
