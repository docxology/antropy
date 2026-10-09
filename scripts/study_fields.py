# Copyright (c) 2026 Daniel Ari Friedman
"""Paper MIX construction and explicitly described spatial controls."""

from __future__ import annotations

import itertools
import math
from typing import assert_never

import numpy as np
from numpy.typing import NDArray

from antropy_hd.errors import ParameterError
from scripts.study_models import Family, StudyCase, StudyPlan


def study_cases(plan: StudyPlan) -> tuple[StudyCase, ...]:
    """Derive every declared field independently of execution or result files."""
    cases: list[StudyCase] = []
    for shape, trial in itertools.product(sorted(plan.shapes), range(plan.replicates)):
        cases.extend(
            StudyCase(shape=shape, family="mix", mixing=p, trial=trial)
            for p in sorted(plan.mixing_probabilities)
        )
        cases.extend(
            StudyCase(shape=shape, family=family, mixing=None, trial=trial)
            for family in sorted(plan.controls)
        )
    return tuple(cases)


def family_code(family: Family) -> int:
    """Return a stable namespace independent of configuration ordering."""
    match family:
        case "mix":
            return 1
        case "constant":
            return 2
        case "checkerboard":
            return 3
        case "gaussian":
            return 4
        case "correlated":
            return 5
        case "shuffled":
            return 6
        case unreachable:
            assert_never(unreachable)


def study_field(plan: StudyPlan, case: StudyCase) -> NDArray[np.float64]:
    """Return a finite native field, without silently flattening spatial neighborhoods."""
    coordinates = np.indices(case.shape, dtype=np.float64)
    phase_coordinates = coordinates + plan.phase_origin
    periodic = np.sin(2 * np.pi * phase_coordinates / plan.period).sum(axis=0)
    seed = np.random.SeedSequence([plan.seed, family_code(case.family), *case.shape, case.trial])
    rng = np.random.default_rng(seed)
    match case.family:
        case "mix":
            if case.mixing is None:
                raise ParameterError("mixing", "MIX requires a declared replacement probability")
            mask = rng.random(case.shape) < case.mixing
            replacement = rng.uniform(-math.sqrt(3), math.sqrt(3), case.shape)
            field = np.where(mask, replacement, periodic)
        case "constant":
            field = np.zeros(case.shape)
        case "checkerboard":
            field = 2 * (coordinates.sum(axis=0) % 2) - 1
        case "gaussian":
            field = rng.normal(scale=plan.gaussian_sd, size=case.shape)
        case "correlated":
            field = rng.normal(scale=plan.gaussian_sd, size=case.shape)
            for _ in range(plan.correlation_steps):
                field = (
                    field
                    + sum(
                        np.roll(field, shift, axis)
                        for axis in range(field.ndim)
                        for shift in (-1, 1)
                    )
                ) / (1 + 2 * field.ndim)
        case "shuffled":
            field = rng.permutation(periodic.ravel(order="C")).reshape(case.shape)
        case unreachable:
            assert_never(unreachable)
    if not np.isfinite(field).all():
        raise ParameterError("study", "Synthetic field overflowed; no data was substituted")
    return field


def symbol_probabilities(array: NDArray[np.float64], plan: StudyPlan) -> NDArray[np.float64]:
    """Quantize on fixed cuts, retaining zero categories and both overflow categories."""
    cuts = np.linspace(*plan.symbol_range, plan.symbol_bins - 1)
    counts = np.bincount(
        np.searchsorted(cuts, array.ravel(), side="right"), minlength=plan.symbol_bins
    )
    return counts.astype(np.float64) / array.size
