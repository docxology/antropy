# Copyright (c) 2026 Daniel Ari Friedman
"""Independent whole-field MIX groups with stable scenario, subject and inference streams."""

from __future__ import annotations

import hashlib
import math
from typing import Literal, assert_never

import numpy as np
from numpy.typing import NDArray

from antropy_hd.errors import ParameterError
from antropy_hd.symbolization import SymbolizationConfig, fixed_alphabet
from scripts.power_plan import PowerPlan, PowerScenario


def identity_words(identity: str) -> tuple[int, ...]:
    """Use specified SHA-256 words rather than Python's process-randomized hash function."""
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    return tuple(
        int.from_bytes(digest[offset : offset + 4], "little") for offset in range(0, len(digest), 4)
    )


def stream_seed(
    plan: PowerPlan, identity: str, shape: tuple[int, ...], replicate: int, subject: int
) -> int:
    """Derive separate deterministic streams, including each semantic namespace in the identity."""
    sequence = np.random.SeedSequence(
        [plan.seed, *identity_words(identity), *shape, replicate, subject]
    )
    return int(sequence.generate_state(1, dtype=np.uint64)[0])


def pool_identity(
    scenario: PowerScenario,
    shape: tuple[int, ...],
    replicate: int,
    group: Literal["first", "second"],
) -> str:
    """Keep the complete unit identity in paths and records."""
    return f"{scenario.id}-{'x'.join(map(str, shape))}-replicate{replicate}-{group}"


def replacement_field(
    plan: PowerPlan,
    scenario: PowerScenario,
    shape: tuple[int, ...],
    replicate: int,
    group: Literal["first", "second"],
    subject: int,
) -> NDArray[np.float64]:
    """Draw separate field streams even under the same-probability null hypothesis."""
    match group:
        case "first":
            probability = scenario.first_probability
        case "second":
            probability = scenario.second_probability
        case unreachable:
            assert_never(unreachable)
    coordinates = np.indices(shape, dtype=np.float64)
    periodic = np.sin(2 * math.pi * (coordinates + plan.phase_origin) / plan.period).sum(axis=0)
    rng = np.random.default_rng(
        stream_seed(plan, f"field/{scenario.id}/{group}", shape, replicate, subject)
    )
    uniform = rng.random(shape)
    replacement = rng.uniform(-math.sqrt(3), math.sqrt(3), shape)
    field = np.where(uniform < probability, replacement, periodic)
    if not np.isfinite(field).all():
        raise ParameterError("power", "Synthetic field overflowed; no observation was replaced")
    return field


def fixed_probabilities(array: NDArray[np.float64], plan: PowerPlan) -> NDArray[np.float64]:
    """Use the same fixed full alphabet for both independent groups and all scenarios."""
    config = SymbolizationConfig(
        cuts=tuple(float(value) for value in np.linspace(*plan.symbol_range, plan.symbol_bins - 1))
    )
    return np.asarray(fixed_alphabet(array, config=config).probabilities, dtype=np.float64)
