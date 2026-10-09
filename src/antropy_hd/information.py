# Copyright (c) 2026 Daniel Ari Friedman
"""Discrete information measures with explicit probability-tensor semantics."""

import math
from typing import assert_never

import numpy as np
from numpy.typing import ArrayLike, NDArray

from antropy_hd._information import (
    HistogramLimits,
    LogOptions,
    MixtureOptions,
    OrderOptions,
    jensen_shannon_value,
    normalize_value,
    parse_probabilities,
    partition_axes,
    probability_result,
    shannon_value,
)
from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.models import EntropyResult
from antropy_hd.validation import as_real_array


def shannon_entropy(
    probabilities: ArrayLike, *, base: float = 2.0, normalize: bool = False
) -> EntropyResult:
    """Return discrete Shannon entropy; tensor cells form one joint alphabet."""
    options = LogOptions(base=base, normalize=normalize)
    array = parse_probabilities(probabilities)
    value = normalize_value(
        shannon_value(array, options.base),
        array.size,
        options.normalize,
        math.log(array.size) / math.log(options.base),
    )
    return probability_result(
        "shannon", value, array, {"base": options.base, "normalize": options.normalize}
    )


def renyi_entropy(
    probabilities: ArrayLike, *, order: float = 2.0, base: float = 2.0, normalize: bool = False
) -> EntropyResult:
    """Return Rényi entropy, including order zero, one and positive infinity."""
    options = LogOptions(base=base, normalize=normalize)
    _ = OrderOptions(order=order)
    array = parse_probabilities(probabilities)
    positive = array[array > 0]
    logs = np.log(positive)
    if order == 0:
        natural = math.log(positive.size)
    elif order == 1:
        natural = shannon_value(array, math.e)
    elif math.isinf(order):
        natural = -float(np.max(logs))
    elif abs(order - 1.0) < 1e-4:
        natural = math.log1p(float(np.sum(positive * np.expm1((order - 1) * logs)))) / (1 - order)
    else:
        maximum = float(np.max(logs))
        with np.errstate(over="ignore"):
            shifted = np.exp(order * (logs - maximum))
        natural = (order / (1 - order)) * maximum + math.log(float(np.sum(shifted))) / (1 - order)
    value = normalize_value(
        max(0.0, natural) / math.log(options.base),
        array.size,
        options.normalize,
        math.log(array.size) / math.log(options.base),
    )
    return probability_result(
        "renyi",
        value,
        array,
        {
            "base": options.base,
            "normalize": options.normalize,
            "order": "infinity" if math.isinf(order) else order,
        },
    )


def tsallis_entropy(
    probabilities: ArrayLike, *, order: float = 2.0, normalize: bool = False
) -> EntropyResult:
    """Return Tsallis entropy with k=1 and the natural-log Shannon limit at q=1."""
    options = LogOptions(base=math.e, normalize=normalize)
    _ = OrderOptions(order=order)
    if not math.isfinite(order) or order < 0:
        raise ParameterError("order", "requires a finite nonnegative order")
    array = parse_probabilities(probabilities)
    positive = array[array > 0]
    if order == 1:
        natural = shannon_value(array, math.e)
        maximum = math.log(array.size)
    elif order == 0:
        natural = float(positive.size - 1)
        maximum = float(array.size - 1)
    elif order < 1:
        natural = float(np.sum(positive**order * -np.expm1((1 - order) * np.log(positive)))) / (
            1 - order
        )
        maximum = -math.expm1((1 - order) * math.log(array.size)) / (order - 1)
    else:
        with np.errstate(over="ignore"):
            natural = -float(np.sum(positive * np.expm1((order - 1) * np.log(positive)))) / (
                order - 1
            )
        maximum = -math.expm1((1 - order) * math.log(array.size)) / (order - 1)
    value = normalize_value(max(0.0, natural), array.size, options.normalize, maximum)
    return probability_result(
        "tsallis", value, array, {"order": order, "normalize": options.normalize, "k": 1.0}
    )


def histogram_entropy(
    data: ArrayLike, *, bins: int | ArrayLike = 10, base: float = 2.0, max_bins: int = 100000
) -> EntropyResult:
    """Estimate amplitude Shannon entropy by pooling all scalar array entries."""
    options = LogOptions(base=base)
    limits = HistogramLimits(max_bins=max_bins)
    array = as_real_array(data)
    parsed: int | NDArray[np.float64] = (
        bins if isinstance(bins, int) and not isinstance(bins, bool) else as_real_array(bins)
    )
    match parsed:
        case int():
            if parsed < 1:
                raise ParameterError("bins", "requires a positive integer")
            count = parsed
            edges: int | NDArray[np.float64] = parsed
        case np.ndarray():
            explicit = parsed
            if (
                explicit.ndim != 1
                or explicit.size < 2
                or bool(np.any(explicit[1:] <= explicit[:-1]))
            ):
                raise ParameterError("bins", "requires strictly increasing one-dimensional edges")
            if float(explicit[0]) > float(np.min(array)) or float(explicit[-1]) < float(
                np.max(array)
            ):
                raise ParameterError("bins", "edges must contain every observation")
            count, edges = explicit.size - 1, explicit
        case unreachable:
            assert_never(unreachable)
    if count > limits.max_bins:
        raise ResourceError("max_bins", f"{count} bins exceed the declared limit")
    try:
        counts, actual_edges = np.histogram(array, bins=edges)
    except (ValueError, OverflowError, IndexError) as error:
        raise ParameterError("bins", "histogram edges are not numerically representable") from error
    if int(np.sum(counts)) != array.size or not bool(np.all(np.isfinite(actual_edges))):
        raise ParameterError("bins", "histogram must contain all observations with finite edges")
    return EntropyResult(
        measure="histogram",
        value=shannon_value(counts / array.size, options.base),
        n_observations=array.size,
        parameters={"base": options.base, "bins": count},
        diagnostics={
            "bin_edges": [float(edge) for edge in actual_edges],
            "counts": [int(value) for value in counts],
            "pooling": "amplitudes",
        },
    )


def joint_entropy(joint_probabilities: ArrayLike, *, base: float = 2.0) -> EntropyResult:
    """Return joint Shannon entropy over every axis of a probability tensor."""
    result = shannon_entropy(joint_probabilities, base=base)
    return result.model_copy(update={"measure": "joint"})


def conditional_entropy(
    joint_probabilities: ArrayLike, *, conditioned_axes: tuple[int, ...] = (1,), base: float = 2.0
) -> EntropyResult:
    """Return H(remaining variables | conditioned axes) from a joint tensor."""
    options = LogOptions(base=base)
    array = parse_probabilities(joint_probabilities)
    remaining = partition_axes(conditioned_axes, array.ndim)
    marginal = np.sum(array, axis=remaining, keepdims=True)
    positive = array > 0
    conditional = array / np.where(marginal > 0, marginal, 1)
    value = max(
        0.0,
        -float(np.sum(array[positive] * np.log(conditional[positive]))) / math.log(options.base),
    )
    return probability_result(
        "conditional",
        value,
        array,
        {"base": options.base, "conditioned_axes": list(conditioned_axes)},
    )


def mutual_information(
    joint_probabilities: ArrayLike, *, x_axes: tuple[int, ...] = (0,), base: float = 2.0
) -> EntropyResult:
    """Return I(X;Y), with X selected by axes and Y their complement."""
    options = LogOptions(base=base)
    array = parse_probabilities(joint_probabilities)
    y_axes = partition_axes(x_axes, array.ndim)
    x_marginal = np.sum(array, axis=y_axes)
    y_marginal = np.sum(array, axis=x_axes)
    value = max(
        0.0,
        shannon_value(x_marginal, options.base)
        + shannon_value(y_marginal, options.base)
        - shannon_value(array, options.base),
    )
    return probability_result(
        "mutual_information", value, array, {"base": options.base, "x_axes": list(x_axes)}
    )


def jensen_shannon_divergence(
    p: ArrayLike, q: ArrayLike, *, weight: float = 0.5, base: float = 2.0
) -> EntropyResult:
    """Return weighted Jensen-Shannon divergence on the same discrete alphabet."""
    options = LogOptions(base=base)
    _ = MixtureOptions(weight=weight)
    left, right = parse_probabilities(p), parse_probabilities(q)
    if left.shape != right.shape:
        raise ParameterError("probabilities", "both distributions must have the same shape")
    mixture = weight * left + (1 - weight) * right
    value = jensen_shannon_value(left, right, weight) / math.log(options.base)
    return probability_result(
        "jensen_shannon", value, mixture, {"base": options.base, "weight": weight}
    )
