# Copyright (c) 2026 Daniel Ari Friedman
"""Authenticate complete independent field pools and replay every configured scalar kernel."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Literal, assert_never

import numpy as np
from numpy.typing import NDArray

from antropy_hd.errors import ParameterError
from antropy_hd.orchestration import analyze, array_sha256
from scripts.artifact_io import bounded_path, digest, replay_equivalent
from scripts.power_fields import fixed_probabilities, pool_identity, replacement_field
from scripts.power_models import FieldEstimate, PowerPool, PowerReport
from scripts.power_plan import PowerPlan
from scripts.result_replay import result_equivalent, scalar_result

type Group = Literal["first", "second"]
type PoolKey = tuple[str, tuple[int, ...], int, Group]


@dataclass(frozen=True, slots=True)
class FieldIndex:
    """Authenticated subject records organized by the experimental unit, never array cells."""

    groups: dict[PoolKey, tuple[FieldEstimate, ...]]


@dataclass(frozen=True, slots=True)
class PoolDesign:
    """The exact prospective pool and subject matrix, prior to tensor reads."""

    identities: dict[str, PoolKey]
    estimates: dict[tuple[str, int], FieldEstimate]


def _design(report: PowerReport) -> PoolDesign:
    plan = report.plan
    groups: tuple[Group, ...] = ("first", "second")
    identities: dict[str, PoolKey] = {}
    for scenario, shape, replicate, group in product(
        plan.scenarios, plan.shapes, range(plan.repetitions), groups
    ):
        identity = pool_identity(scenario, shape, replicate, group)
        identities[identity] = (scenario.id, shape, replicate, group)
    actual_ids = [pool.id for pool in report.pools]
    if len(set(actual_ids)) != len(actual_ids) or set(actual_ids) != identities.keys():
        raise ParameterError("power", "Pool design matrix is incomplete or duplicated")
    expected_fields = {
        (identity, index) for identity in identities for index in range(max(plan.sample_sizes))
    }
    actual_fields = [(field.pool_id, field.pool_index) for field in report.estimates]
    if len(set(actual_fields)) != len(actual_fields) or set(actual_fields) != expected_fields:
        raise ParameterError("power", "Field design matrix is incomplete or duplicated")
    field_ids = [field.field_id for field in report.estimates]
    if len(set(field_ids)) != len(field_ids):
        raise ParameterError("power", "Field identities are duplicated")
    return PoolDesign(
        identities=identities,
        estimates={(field.pool_id, field.pool_index): field for field in report.estimates},
    )


def _pool_array(root: Path, pool: PowerPool, plan: PowerPlan) -> NDArray[np.float64]:
    path = bounded_path(root, pool.input_file)
    if digest(path) != pool.file_sha256:
        raise ParameterError("power", "Pool file hash differs from stored bytes")
    array = np.load(path, allow_pickle=False, mmap_mode="r")
    if (
        array.dtype != np.dtype(np.float64)
        or array.shape != (pool.subjects, *pool.shape)
        or array.nbytes > plan.max_pool_bytes
        or not np.isfinite(array).all()
        or array_sha256(array) != pool.array_sha256
    ):
        raise ParameterError("power", "Pool tensor shape, dtype, finiteness or hash differs")
    return array


def _replay_field(stored: NDArray[np.float64], field: FieldEstimate, plan: PowerPlan) -> None:
    if (
        field.field_id != f"{field.pool_id}-subject{field.pool_index}"
        or field.input_sha256 != array_sha256(stored)
        or set(field.results) != {analysis.spec.id for analysis in plan.analyses}
    ):
        raise ParameterError("power", "Subject identity, input hash or analysis coverage differs")
    probabilities = fixed_probabilities(stored, plan)
    for analysis in plan.analyses:
        match analysis.geometry:
            case "native":
                transformed = stored
            case "flattened":
                transformed = stored.ravel(order="C")
            case "symbols":
                transformed = probabilities
            case unreachable:
                assert_never(unreachable)
        replayed = scalar_result(analyze(transformed, analysis.spec))
        if not result_equivalent(field.results[analysis.spec.id], replayed):
            raise ParameterError("power", "Field estimate fails actual scalar kernel replay")


def validate_fields(root: Path, report: PowerReport) -> FieldIndex:
    """Require the whole declared matrix before loading or replaying any reported pool."""
    plan = report.plan
    design = _design(report)
    verified: dict[PoolKey, tuple[FieldEstimate, ...]] = {}
    scenarios = {scenario.id: scenario for scenario in plan.scenarios}
    for pool in report.pools:
        key = design.identities[pool.id]
        scenario_id, shape, replicate, group = key
        if (
            pool.scenario_id != scenario_id
            or pool.shape != shape
            or pool.replicate != replicate
            or pool.group != group
            or pool.subjects != max(plan.sample_sizes)
            or pool.input_file != f"output/power/pools/{pool.id}.npy"
        ):
            raise ParameterError("power", "Pool identity differs from the declared design")
        array = _pool_array(root, pool, plan)
        records: list[FieldEstimate] = []
        for index in range(pool.subjects):
            field = design.estimates[(pool.id, index)]
            stored = np.asarray(array[index], dtype=np.float64)
            reference = replacement_field(
                plan, scenarios[scenario_id], shape, replicate, group, index
            )
            if not replay_equivalent(stored, reference):
                raise ParameterError("power", "Pool field fails independent seeded design replay")
            _replay_field(stored, field, plan)
            records.append(field)
        verified[key] = tuple(records)
    files = {path.name for path in (root / "output/power/pools").glob("*.npy")}
    if files != {f"{identity}.npy" for identity in design.identities}:
        raise ParameterError("power", "Pool directory contains undeclared or missing tensor files")
    return FieldIndex(groups=verified)
