# Copyright (c) 2026 Daniel Ari Friedman
from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest
from pydantic import JsonValue, ValidationError

from antropy_hd.models import EntropyResult, Status
from antropy_hd.orchestration import (
    METHODS,
    AnalysisSpec,
    BatchConfig,
    analyze,
    array_sha256,
    canonical_json,
    run_batch,
)


@pytest.mark.parametrize("measure", METHODS)
def test_every_registered_measure_runs(measure: str) -> None:
    data = np.tile([0.0, 1.0, 0.5, 1.5], 8)
    parameters = {}
    if "probabilities" in METHODS[measure].input_kind:
        data = np.array([0.25, 0.75])
    if measure in {"joint_entropy", "conditional_entropy", "mutual_information"}:
        data = np.array([[0.25, 0.25], [0.25, 0.25]])
    if measure == "jensen_shannon_divergence":
        parameters = {"q": [0.75, 0.25]}
    if measure == "multiscale_entropy":
        parameters = {"scales": [1, 2]}
    result = analyze(data, AnalysisSpec(id="real", measure=measure, parameters=parameters))
    estimates = result if isinstance(result, tuple) else (result,)
    assert estimates
    assert all(isinstance(estimate, EntropyResult) for estimate in estimates)
    assert all(
        json.loads(estimate.model_dump_json())["status"] in {"finite", "undefined", "infinite"}
        for estimate in estimates
    )


def test_batch_hashes_statuses_and_determinism() -> None:
    config = BatchConfig(
        analyses=(
            AnalysisSpec(
                id="constant",
                measure="hdse",
                parameters={"embedding": {"shape": [2, 2]}, "match": {"tolerance": 0.5}},
            ),
        )
    )
    data = np.ones((4, 4))
    result = run_batch(data, config)
    estimate = result.results["constant"]
    assert isinstance(estimate, EntropyResult)
    assert estimate.status is Status.UNDEFINED
    assert estimate.value is None
    assert result == run_batch(data.copy(order="F"), config)
    assert (
        result.config_sha256
        == hashlib.sha256(canonical_json(config.model_dump(mode="json")).encode()).hexdigest()
    )
    assert result.input_sha256 == array_sha256(data)
    assert result.input_sha256 != array_sha256(data.reshape(16))
    assert result.input_sha256 != array_sha256(data + 1)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_json_cannot_silently_emit_nonfinite(value: float) -> None:
    with pytest.raises(ValueError, match="Out of range"):
        canonical_json({"value": value})


@pytest.mark.parametrize(
    "payload",
    [
        {"analyses": []},
        {"analyses": [{"id": "x", "measure": "missing"}]},
        {"analyses": [{"id": "x", "measure": "hdse", "surprise": 1}]},
        {"analyses": [{"id": "x", "measure": "hdse"}], "unconsumed": 1},
        {"schema_version": 2, "analyses": [{"id": "x", "measure": "hdse"}]},
        {"analyses": [{"id": "x", "measure": "hdse"}, {"id": "x", "measure": "histogram_entropy"}]},
        {"analyses": [{"id": "../escape", "measure": "hdse"}]},
    ],
)
def test_batch_rejects_invalid_configs(payload: JsonValue) -> None:
    with pytest.raises(ValidationError):
        BatchConfig.model_validate(payload)


@pytest.mark.parametrize(
    "parameters",
    [
        {"wrong": 3},
        {"embedding": {"shape": 2, "wrong": 1}},
        {"match": {"tolerance": 0.5, "wrong": 1}},
        {"embedding": {"max_templates": 2}},
        {"match": {"metric": "missing"}},
    ],
)
def test_parameter_and_resource_failures_remain_real(parameters: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        analyze(np.arange(20.0), AnalysisSpec(id="x", measure="hdse", parameters=parameters))


def test_probability_interpretation_and_required_secondary_input() -> None:
    with pytest.raises(ValueError, match="sum"):
        analyze([0.25, 0.25], AnalysisSpec(id="p", measure="shannon_entropy"))
    with pytest.raises(ValueError, match="q"):
        analyze([0.5, 0.5], AnalysisSpec(id="p", measure="jensen_shannon_divergence"))


def test_json_roundtrip_and_nonfinite_config_failure() -> None:
    config = BatchConfig.model_validate_json(
        '{"analyses":[{"id":"x","measure":"histogram_entropy","parameters":{"bins":4}}]}'
    )
    result = run_batch(np.arange(10.0), config)
    assert json.loads(result.model_dump_json())["config"]["analyses"][0]["parameters"]["bins"] == 4
    invalid = AnalysisSpec(id="x", measure="histogram_entropy", parameters={"base": float("nan")})
    with pytest.raises(ValueError, match="finite"):
        run_batch([0.0, 1.0], BatchConfig(analyses=(invalid,)))
