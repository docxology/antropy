# Copyright (c) 2026 Daniel Ari Friedman
"""Real, bounded prospective simulation fixtures shared by model and artifact controls."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from scripts.power_plan import PowerPlan
from scripts.run_power import run_power


@pytest.fixture(scope="module")
def small_power(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("prospective-power")
    plan = PowerPlan.model_validate(
        {
            "seed": 27,
            "shapes": [[12], [4, 5]],
            "sample_sizes": [2, 4],
            "repetitions": 2,
            "scenarios": [
                {
                    "id": "null",
                    "label": "Null",
                    "role": "null",
                    "first_probability": 0.25,
                    "second_probability": 0.25,
                },
                {
                    "id": "contrast",
                    "label": "Contrast",
                    "role": "alternative",
                    "first_probability": 0.25,
                    "second_probability": 1.0,
                },
            ],
            "analyses": [
                {
                    "label": "HDSE",
                    "geometry": "native",
                    "spec": {
                        "id": "hdse",
                        "measure": "hdse",
                        "parameters": {"embedding": {"shape": 2}, "match": {"tolerance": 2.5}},
                    },
                },
                {
                    "label": "Sparse HDSE",
                    "geometry": "native",
                    "spec": {
                        "id": "sparse",
                        "measure": "hdse",
                        "parameters": {"embedding": {"shape": 2}, "match": {"tolerance": 0.0}},
                    },
                },
                {
                    "label": "Partially sparse HDSE",
                    "geometry": "native",
                    "spec": {
                        "id": "partial",
                        "measure": "hdse",
                        "parameters": {"embedding": {"shape": 2}, "match": {"tolerance": 0.5}},
                    },
                },
                {
                    "label": "Flattened HDSE",
                    "geometry": "flattened",
                    "spec": {
                        "id": "flat",
                        "measure": "hdse",
                        "parameters": {"embedding": {"shape": 2}, "match": {"tolerance": 2.5}},
                    },
                },
                {
                    "label": "Shannon",
                    "geometry": "symbols",
                    "spec": {
                        "id": "shannon",
                        "measure": "shannon_entropy",
                        "parameters": {"normalize": True},
                    },
                },
            ],
            "alpha": 0.05,
            "confidence_level": 0.95,
            "target_power": 0.8,
            "multiplicity": "holm",
            "test": {
                "seed": 29,
                "resamples": 19,
                "max_exact_allocations": 20,
                "max_samples": 8,
                "max_resampling_work": 10000,
            },
            "period": 6.0,
            "phase_origin": 1,
            "symbol_range": [-3.0, 3.0],
            "symbol_bins": 8,
            "max_input_elements": 100,
            "max_fields": 100,
            "max_distance_component_visits": 1000000,
            "max_inference_work": 100000,
            "max_pool_bytes": 10000,
            "max_report_bytes": 2000000,
        }
    )
    path = root / "power_plan.yaml"
    _ = path.write_text(yaml.safe_dump(plan.model_dump(mode="json"), sort_keys=False))
    _ = run_power(root, path)
    return root


@pytest.fixture
def power_files(tmp_path: Path, small_power: Path) -> Path:
    target = tmp_path / "project"
    _ = shutil.copytree(small_power, target)
    return target
