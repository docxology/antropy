# Copyright (c) 2026 Daniel Ari Friedman
"""Real-file synthetic replay controls independent of strict artifact byte custody."""

from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from numpy.typing import NDArray

from antropy_hd.errors import ParameterError
from antropy_hd.models import EntropyResult
from antropy_hd.orchestration import BatchConfig, canonical_json, run_batch
from scripts.artifact_models import Experiments
from scripts.build_manuscript import build
from scripts.run_experiments import ExperimentPlan, synthesize
from scripts.validate_artifacts import expected_results, replay_equivalent, validate

# Pytest discovers explicitly imported real-file fixtures.
from tests.artifact_fixtures import artifacts as artifacts  # noqa: PLC0414
from tests.artifact_fixtures import baseline as baseline  # noqa: PLC0414
from tests.artifact_fixtures import rehash_record


def reseal_field(root: Path, field_id: str, array: NDArray[np.float64]) -> None:
    """Recompute one actual analysis, CSV, manuscript and all legitimate byte hashes."""
    report_path = root / "output/reports/experiments.json"
    payload = json.loads(report_path.read_text())
    record = next(record for record in payload["batches"] if record["field_id"] == field_id)
    input_path = root / record["input_file"]
    np.save(input_path, array, allow_pickle=False)
    config = BatchConfig.model_validate(record["batch"]["config"])
    batch = run_batch(array, config)
    record["input_file_sha256"] = hashlib.sha256(input_path.read_bytes()).hexdigest()
    record["batch"] = batch.model_dump(mode="json")
    report_path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    csv_path = root / "output/data/results.csv"
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        if row["field_id"] == field_id:
            result = batch.results[row["analysis_id"]]
            assert isinstance(result, EntropyResult)
            row.update(
                value="" if result.value is None else str(result.value),
                status=str(result.status),
                n_observations=str(result.n_observations),
                input_sha256=batch.input_sha256,
                config_sha256=batch.config_sha256,
                parameters_json=canonical_json(result.parameters),
                diagnostics_json=canonical_json(result.diagnostics),
            )
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    _ = build(root)


def prove_strict_report_bindings(root: Path) -> None:
    """Check actual file/array/config hashes and result coverage before replay checks."""
    manifest = json.loads((root / "output/provenance/manifest.json").read_text())
    paths = {artifact["path"] for artifact in manifest["artifacts"]}
    experiments = Experiments.model_validate_json(
        (root / "output/reports/experiments.json").read_text()
    )
    assert len(expected_results(root, paths, experiments)) == 30


def test_one_ulp_replay_difference_retains_strict_byte_identity(artifacts: Path) -> None:
    path = artifacts / "output/data/periodic-12.npy"
    original = np.load(path, allow_pickle=False)
    perturbed = original.copy()
    perturbed[1] = np.nextafter(original[1], np.inf)
    assert perturbed[1] - original[1] == np.finfo(np.float64).eps
    assert not np.array_equal(original, perturbed)
    reseal_field(artifacts, "periodic-12", perturbed)
    prove_strict_report_bindings(artifacts)
    assert validate(artifacts)["result_rows"] == 30


def test_unresealed_one_ulp_still_fails_exact_manifest(artifacts: Path) -> None:
    path = artifacts / "output/data/periodic-12.npy"
    array = np.load(path, allow_pickle=False)
    array[1] = np.nextafter(array[1], np.inf)
    np.save(path, array, allow_pickle=False)
    with pytest.raises(ParameterError) as failure:
        validate(artifacts)
    assert failure.value.parameter == "artifacts"


def test_independently_derived_roundoff_envelope_rejects_next_ulp(artifacts: Path) -> None:
    path = artifacts / "output/data/periodic-12.npy"
    array = np.load(path, allow_pickle=False)
    # For d=1 and |reference|=1, compare the exact rational envelope to binary64 steps.
    epsilon = Fraction(1, 2**52)
    operations = 16 + 8
    envelope = 2 * operations * epsilon / (1 - operations * epsilon)
    rejected_steps = envelope // epsilon + 1
    assert rejected_steps == 49
    array[1] += float(rejected_steps * epsilon)
    assert Fraction(float(array[1] - 1.0)) > envelope
    reseal_field(artifacts, "periodic-12", array)
    prove_strict_report_bindings(artifacts)
    with pytest.raises(ParameterError) as failure:
        validate(artifacts)
    assert failure.value.parameter == "seed"


def test_reseeded_noise_cannot_pass_coherently_resealed_custody(artifacts: Path) -> None:
    path = artifacts / "output/data/noise-12.npy"
    original = np.load(path, allow_pickle=False)
    payload = yaml.safe_load((artifacts / "experiment_plan.yaml").read_text())
    payload["seed"] += 1
    altered_plan = ExperimentPlan.model_validate(payload)
    replacement = synthesize(altered_plan, original.shape, "noise")
    assert np.max(np.abs(replacement - original)) > 0.1
    reseal_field(artifacts, "noise-12", replacement)
    prove_strict_report_bindings(artifacts)
    with pytest.raises(ParameterError) as failure:
        validate(artifacts)
    assert failure.value.parameter == "seed"


def test_rehashed_array_without_report_identity_still_fails(artifacts: Path) -> None:
    path = artifacts / "output/data/periodic-12.npy"
    array = np.load(path, allow_pickle=False)
    array[1] = np.nextafter(array[1], np.inf)
    np.save(path, array, allow_pickle=False)
    rehash_record(artifacts, "output/data/periodic-12.npy")
    with pytest.raises(ParameterError) as failure:
        validate(artifacts)
    assert failure.value.parameter == "artifacts"


@pytest.mark.parametrize("dimension", [1, 2, 3])
def test_last_binary64_step_inside_policy_is_accepted(dimension: int) -> None:
    epsilon = Fraction(1, 2**52)
    operations = 16 + 8 * dimension
    envelope = 2 * operations * epsilon / (1 - operations * epsilon)
    permitted_steps = envelope // epsilon
    reference = np.ones((2,) * dimension)
    inside = reference.copy()
    outside = reference.copy()
    inside.flat[0] += float(permitted_steps * epsilon)
    outside.flat[0] += float((permitted_steps + 1) * epsilon)
    assert Fraction(float(inside.flat[0] - 1.0)) <= envelope
    assert Fraction(float(outside.flat[0] - 1.0)) > envelope
    assert replay_equivalent(inside, reference)
    assert not replay_equivalent(outside, reference)


def test_replay_shape_cannot_broadcast_and_zero_uses_unit_floor() -> None:
    reference = np.zeros((2, 2))
    altered = np.nextafter(reference, np.inf)
    assert np.all(altered > 0)
    assert replay_equivalent(altered, reference)
    assert not replay_equivalent(np.zeros(4), reference)
    assert not replay_equivalent(np.zeros((1, 2)), reference)


@pytest.mark.parametrize("nonfinite", [np.inf, -np.inf, np.nan])
def test_nonfinite_replay_reference_fails_closed(nonfinite: float) -> None:
    assert not replay_equivalent(np.array([0.0]), np.array([nonfinite]))


@pytest.mark.parametrize("nonfinite", [np.inf, -np.inf, np.nan])
def test_nonfinite_stored_array_fails_closed(nonfinite: float) -> None:
    assert not replay_equivalent(np.array([nonfinite]), np.array([0.0]))


def test_finite_plan_can_produce_nonfinite_reference_without_acceptance() -> None:
    plan = ExperimentPlan.model_validate(
        {
            "seed": 17,
            "shapes": [[12]],
            "structures": ["mixed"],
            "tolerances": [0.2],
            "noise_amplitude": 1e308,
        }
    )
    with pytest.warns(RuntimeWarning, match="overflow"):
        reference = synthesize(plan, (12,), "mixed")
    assert not np.all(np.isfinite(reference))
    # Construct a finite adversarial stored input; only the overflow locations differ.
    stored = reference.copy()
    stored[~np.isfinite(stored)] = 0.0
    assert np.all(np.isfinite(stored))
    assert not replay_equivalent(stored, reference)
