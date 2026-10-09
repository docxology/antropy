# Copyright (c) 2026 Daniel Ari Friedman
"""Native-dimensional local templates with explicit resource accounting."""

from dataclasses import dataclass
from math import prod
from typing import assert_never

import numpy as np
from numpy.typing import NDArray

from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.models import EmbeddingConfig


@dataclass(frozen=True, slots=True)
class Templates:
    """Read-only flattened local blocks plus their native-coordinate origins."""

    values: NDArray[np.float64]
    origins: NDArray[np.int64]
    shape: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PairedTemplates:
    """Nested base and extended blocks on exactly the same origin population."""

    base: Templates
    extended: Templates


def resolve_geometry(value: int | tuple[int, ...], ndim: int, name: str) -> tuple[int, ...]:
    """Resolve a scalar or an explicit per-axis geometry vector."""
    match value:
        case int():
            result = (value,) * ndim
        case tuple():
            result = value
        case unreachable:
            assert_never(unreachable)
    if len(result) != ndim or not result or min(result) < 1:
        raise ParameterError(name, "requires one positive integer per input axis")
    return result


def extended_shape(shape: tuple[int, ...], axes: tuple[int, ...] | None) -> tuple[int, ...]:
    """Increase the selected local-template axes by one element."""
    selected = tuple(range(len(shape))) if axes is None else axes
    if (
        not selected
        or len(set(selected)) != len(selected)
        or min(selected) < 0
        or max(selected) >= len(shape)
    ):
        raise ParameterError("extend_axes", "requires unique axes within input dimensionality")
    return tuple(size + int(axis in selected) for axis, size in enumerate(shape))


def _origins(
    data_shape: tuple[int, ...],
    shape: tuple[int, ...],
    delay: tuple[int, ...],
    stride: tuple[int, ...],
    config: EmbeddingConfig,
    features: int,
) -> NDArray[np.int64]:
    stops = tuple(
        size - (width - 1) * lag for size, width, lag in zip(data_shape, shape, delay, strict=True)
    )
    if min(stops) < 1:
        raise ParameterError("shape", "embedding span exceeds an input axis")
    counts = tuple((stop - 1) // step + 1 for stop, step in zip(stops, stride, strict=True))
    count = prod(counts)
    if count > config.max_templates:
        raise ResourceError(
            "max_templates", f"{count} templates requested; limit is {config.max_templates}"
        )
    # Covers live values, origins, extraction indices, offsets, and stride vector.
    estimated = count * (features * 8 + len(shape) * 32 + 16) + prod(shape) * len(shape) * 8 + 4096
    if estimated > config.max_memory_bytes:
        raise ResourceError(
            "max_memory_bytes", f"template storage needs at least {estimated} bytes"
        )
    grid: NDArray[np.int64] = np.indices(counts, dtype=np.int64).reshape(len(shape), -1).T
    grid *= np.asarray(stride, dtype=np.int64)
    grid.setflags(write=False)
    return grid


def _extract(
    data: NDArray[np.float64],
    shape: tuple[int, ...],
    delay: tuple[int, ...],
    origins: NDArray[np.int64],
) -> Templates:
    # WHY: explicit offsets preserve spatial adjacency without unsafe strided views.
    offsets: NDArray[np.int64] = np.indices(shape, dtype=np.int64).reshape(len(shape), -1).T
    offsets *= np.asarray(delay, dtype=np.int64)
    values = np.empty((len(origins), len(offsets)), dtype=np.float64)
    for column, offset in enumerate(offsets):
        indices = tuple(origins[:, axis] + offset[axis] for axis in range(data.ndim))
        values[:, column] = data[indices]
    values.setflags(write=False)
    return Templates(values, origins, shape)


def local_templates(data: NDArray[np.float64], config: EmbeddingConfig) -> Templates:
    """Extract the full valid origin population for one local-template geometry."""
    shape = resolve_geometry(config.shape, data.ndim, "shape")
    delay = resolve_geometry(config.delay, data.ndim, "delay")
    stride = resolve_geometry(config.stride, data.ndim, "stride")
    origins = _origins(data.shape, shape, delay, stride, config, prod(shape))
    return _extract(data, shape, delay, origins)


def paired_templates(data: NDArray[np.float64], config: EmbeddingConfig) -> PairedTemplates:
    """Extract nested geometries on the extended block's common valid origins."""
    shape = resolve_geometry(config.shape, data.ndim, "shape")
    larger = extended_shape(shape, config.extend_axes)
    delay = resolve_geometry(config.delay, data.ndim, "delay")
    stride = resolve_geometry(config.stride, data.ndim, "stride")
    origins = _origins(data.shape, larger, delay, stride, config, prod(shape) + prod(larger))
    count = len(origins)
    if count < 2:
        raise ParameterError("shape", "at least two common origins are required")
    pairs = count * (count - 1) // 2
    if pairs > config.max_pairs:
        raise ResourceError(
            "max_pairs", f"{pairs} candidate pairs requested; limit is {config.max_pairs}"
        )
    return PairedTemplates(
        _extract(data, shape, delay, origins), _extract(data, larger, delay, origins)
    )
