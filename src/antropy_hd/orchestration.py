# Copyright (c) 2026 Daniel Ari Friedman
"""Validated method dispatch and reproducible analysis batches."""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass
from importlib.metadata import version
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar, Final, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from antropy_hd.distribution import distribution_entropy
from antropy_hd.errors import ParameterError
from antropy_hd.information import (
    conditional_entropy,
    histogram_entropy,
    jensen_shannon_divergence,
    joint_entropy,
    mutual_information,
    renyi_entropy,
    shannon_entropy,
    tsallis_entropy,
)
from antropy_hd.models import EmbeddingConfig, EntropyResult, MatchConfig
from antropy_hd.multiscale import multiscale_entropy
from antropy_hd.ordinal import permutation_entropy, weighted_permutation_entropy
from antropy_hd.spectral import spectral_entropy, svd_entropy
from antropy_hd.statistical import StatisticalComplexityConfig, statistical_complexity
from antropy_hd.template_entropy import approximate_entropy, fuzzy_entropy, hdse, sample_entropy
from antropy_hd.validation import as_real_array

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from numpy.typing import ArrayLike, NDArray

type AnalysisResult = EntropyResult | tuple[EntropyResult, ...]
type ParameterValue = JsonValue | EmbeddingConfig | MatchConfig | StatisticalComplexityConfig


@dataclass(frozen=True, slots=True)
class Method:
    """Public function and the interpretation of its input array."""

    runner: Callable[..., AnalysisResult]
    input_kind: str

    def resolve(self) -> Callable[..., AnalysisResult]:
        """Resolve a fixed, allowlisted implementation."""
        return self.runner


METHODS: Final[Mapping[str, Method]] = MappingProxyType(
    {
        "hdse": Method(hdse, "observations"),
        "sample_entropy": Method(sample_entropy, "observations"),
        "approximate_entropy": Method(approximate_entropy, "observations"),
        "fuzzy_entropy": Method(fuzzy_entropy, "observations"),
        "distribution_entropy": Method(distribution_entropy, "observations"),
        "multiscale_entropy": Method(multiscale_entropy, "observations"),
        "shannon_entropy": Method(shannon_entropy, "probabilities"),
        "renyi_entropy": Method(renyi_entropy, "probabilities"),
        "tsallis_entropy": Method(tsallis_entropy, "probabilities"),
        "histogram_entropy": Method(histogram_entropy, "observations"),
        "joint_entropy": Method(joint_entropy, "joint probabilities"),
        "conditional_entropy": Method(conditional_entropy, "joint probabilities"),
        "mutual_information": Method(mutual_information, "joint probabilities"),
        "jensen_shannon_divergence": Method(
            jensen_shannon_divergence, "probabilities; q supplied as parameter"
        ),
        "permutation_entropy": Method(permutation_entropy, "observations"),
        "weighted_permutation_entropy": Method(weighted_permutation_entropy, "observations"),
        "spectral_entropy": Method(spectral_entropy, "observations"),
        "svd_entropy": Method(svd_entropy, "observations"),
        "statistical_complexity": Method(statistical_complexity, "fixed-alphabet probabilities"),
    }
)


class AnalysisSpec(BaseModel):
    """One explicit measure invocation; unknown fields fail validation."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    measure: str
    parameters: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_measure(self) -> AnalysisSpec:
        """Reject unknown measures before any numerical work."""
        if self.measure not in METHODS:
            raise ParameterError(
                "measure", f"Unknown measure {self.measure!r}; choose from {sorted(METHODS)}"
            )
        return self


class BatchConfig(BaseModel):
    """Versioned, deterministic batch configuration."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    analyses: tuple[AnalysisSpec, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self) -> BatchConfig:
        """Require unambiguous result identities."""
        ids = [spec.id for spec in self.analyses]
        if len(set(ids)) != len(ids):
            raise ParameterError("analyses", "Analysis ids must be unique")
        return self


class BatchResult(BaseModel):
    """Strict JSON result with input and consumed configuration provenance."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    package_version: str
    input_shape: tuple[int, ...]
    input_sha256: str
    config_sha256: str
    config: BatchConfig
    results: dict[str, AnalysisResult]


def canonical_json(value: JsonValue) -> str:
    """Serialize deterministically and reject nonfinite JSON numbers."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def array_sha256(data: NDArray[np.float64]) -> str:
    """Bind shape, dtype and C-order array bytes, independent of file encoding."""
    digest = hashlib.sha256()
    digest.update(canonical_json({"shape": list(data.shape), "dtype": "<f8"}).encode())
    digest.update(np.asarray(data, dtype="<f8", order="C").tobytes())
    return digest.hexdigest()


def prepared_parameters(spec: AnalysisSpec) -> dict[str, ParameterValue]:
    """Validate the entire call signature and nested configuration models."""
    parameters: dict[str, ParameterValue] = dict(spec.parameters)
    if "embedding" in parameters:
        parameters["embedding"] = EmbeddingConfig.model_validate(parameters["embedding"])
    if "match" in parameters:
        parameters["match"] = MatchConfig.model_validate(parameters["match"])
    if "config" in parameters and spec.measure == "statistical_complexity":
        parameters["config"] = StatisticalComplexityConfig.model_validate(parameters["config"])
    runner = METHODS[spec.measure].resolve()
    try:
        _ = inspect.signature(runner).bind(np.array([0.0]), **parameters)
    except TypeError as error:
        raise ParameterError("parameters", str(error)) from error
    return parameters


def analyze(data: ArrayLike, spec: AnalysisSpec) -> AnalysisResult:
    """Run one registered measure with fully validated parameters."""
    array = as_real_array(data)
    parameters = prepared_parameters(spec)
    return METHODS[spec.measure].resolve()(array, **parameters)


def run_batch(data: ArrayLike, config: BatchConfig) -> BatchResult:
    """Validate every call before running, preserving explicit estimate statuses."""
    array = as_real_array(data)
    prepared = [(spec, prepared_parameters(spec)) for spec in config.analyses]
    results = {
        spec.id: METHODS[spec.measure].resolve()(array, **parameters)
        for spec, parameters in prepared
    }
    return BatchResult(
        package_version=version("antropy-hd"),
        input_shape=array.shape,
        input_sha256=array_sha256(array),
        config_sha256=hashlib.sha256(
            canonical_json(config.model_dump(mode="json")).encode()
        ).hexdigest(),
        config=config,
        results=results,
    )
