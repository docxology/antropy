# Copyright (c) 2026 Daniel Ari Friedman
"""Retain independent field pools and complete per-subject numerical evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from antropy_hd.orchestration import array_sha256
from scripts.artifact_io import digest
from scripts.power_analysis import evaluate_field
from scripts.power_fields import pool_identity, replacement_field
from scripts.power_models import FieldEstimate, PowerPool
from scripts.power_plan import PowerPlan, PowerScenario


@dataclass(frozen=True, slots=True)
class RetainedPool:
    """Disk-bound pool identity and the field estimates consumed by all n-prefix tests."""

    record: PowerPool
    estimates: tuple[FieldEstimate, ...]


def retain_pool(
    root: Path,
    plan: PowerPlan,
    scenario: PowerScenario,
    shape: tuple[int, ...],
    replicate: int,
    group: Literal["first", "second"],
) -> RetainedPool:
    """Compute each field once and save a numeric-only, explicitly shaped tensor."""
    identity = pool_identity(scenario, shape, replicate, group)
    array = np.empty((max(plan.sample_sizes), *shape), dtype=np.float64)
    estimates: list[FieldEstimate] = []
    for subject in range(max(plan.sample_sizes)):
        field = replacement_field(plan, scenario, shape, replicate, group, subject)
        array[subject] = field
        estimates.append(
            FieldEstimate(
                field_id=f"{identity}-subject{subject}",
                pool_id=identity,
                pool_index=subject,
                input_sha256=array_sha256(field),
                results=evaluate_field(field, plan),
            )
        )
    path = root / "output/power/pools" / f"{identity}.npy"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, array, allow_pickle=False)
    return RetainedPool(
        record=PowerPool(
            id=identity,
            scenario_id=scenario.id,
            shape=shape,
            replicate=replicate,
            group=group,
            input_file=path.relative_to(root).as_posix(),
            file_sha256=digest(path),
            array_sha256=array_sha256(array),
            subjects=max(plan.sample_sizes),
        ),
        estimates=tuple(estimates),
    )
