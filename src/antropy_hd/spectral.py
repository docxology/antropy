# Copyright (c) 2026 Daniel Ari Friedman
"""Full N-D Fourier and local-embedding singular-value entropy."""

from typing import ClassVar

import numpy as np
from numpy.typing import ArrayLike, NDArray
from pydantic import ConfigDict, Field, StrictBool, StrictInt

from antropy_hd._information import LogOptions
from antropy_hd.embedding import local_templates
from antropy_hd.errors import ParameterError, ResourceError
from antropy_hd.information import shannon_entropy
from antropy_hd.models import EmbeddingConfig, EntropyResult, Status
from antropy_hd.validation import as_real_array


class _SpectralOptions(LogOptions):
    """Define the periodogram convention and bound its working storage."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    demean: StrictBool = True
    include_dc: StrictBool = True
    max_memory_bytes: StrictInt = Field(default=134217728, ge=1024)


class _SVDOptions(LogOptions):
    """Select column centering of the trajectory matrix before decomposition."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)
    demean: StrictBool = False


def _scaled(
    data: NDArray[np.float64], *, translate: bool, axis: int | None = None
) -> NDArray[np.float64]:
    """Translate before scaling to preserve nearby floats on a large baseline."""
    if translate:
        low = np.min(data, axis=axis, keepdims=True)
        high = np.max(data, axis=axis, keepdims=True)
        shifted = data - (low / 2 + high / 2)
    else:
        shifted = data
    scale = float(np.max(np.abs(shifted)))
    return np.zeros_like(shifted) if scale == 0 else shifted / scale


def spectral_entropy(
    data: ArrayLike,
    *,
    demean: bool = True,
    include_dc: bool = True,
    base: float = 2.0,
    normalize: bool = False,
    max_memory_bytes: int = 134217728,
) -> EntropyResult:
    """Return Shannon entropy of normalized power over every full N-D FFT bin.

    Conjugate bins count separately. Removing DC reduces the normalization
    alphabet by one. A signal with zero retained power has undefined entropy.
    """
    options = _SpectralOptions(
        base=base,
        normalize=normalize,
        demean=demean,
        include_dc=include_dc,
        max_memory_bytes=max_memory_bytes,
    )
    array = as_real_array(data)
    estimated = array.size * 80
    if estimated > options.max_memory_bytes:
        raise ResourceError(
            "max_memory_bytes", f"FFT working storage needs at least {estimated} bytes"
        )
    scaled = _scaled(array, translate=options.demean)
    centered = scaled - float(np.mean(scaled)) if options.demean else scaled
    transform = np.fft.fftn(centered, norm="forward")
    power = np.abs(transform).ravel() ** 2
    retained = power if options.include_dc else power[1:]
    total = float(np.sum(retained))
    value: float | None = None
    if total > 0:
        value = shannon_entropy(
            retained / total, base=options.base, normalize=options.normalize
        ).value
    return EntropyResult(
        measure="spectral",
        value=value,
        status=Status.UNDEFINED if value is None else Status.FINITE,
        n_observations=array.size,
        parameters={
            "base": options.base,
            "normalize": options.normalize,
            "demean": options.demean,
            "include_dc": options.include_dc,
            "max_memory_bytes": options.max_memory_bytes,
        },
        diagnostics={
            "input_shape": list(array.shape),
            "frequency_bins": retained.size,
            "spectrum": "full_nd_fft_periodogram",
            "amplitude_scaling": "midrange_then_global_max_abs"
            if options.demean
            else "global_max_abs",
        },
    )


def svd_entropy(
    data: ArrayLike,
    *,
    embedding: EmbeddingConfig | None = None,
    demean: bool = False,
    base: float = 2.0,
    normalize: bool = False,
) -> EntropyResult:
    """Return Shannon entropy of normalized singular values of spatial templates.

    Singular values are not squared. Demeaning centers each template position
    across origins. The normalization alphabet is min(template count, width).
    """
    options = _SVDOptions(base=base, normalize=normalize, demean=demean)
    config = EmbeddingConfig() if embedding is None else embedding
    array = as_real_array(data)
    templates = local_templates(array, config)
    rank_size = min(templates.values.shape)
    estimated = templates.values.nbytes * 6 + templates.origins.nbytes + rank_size**2 * 8
    if estimated > config.max_memory_bytes:
        raise ResourceError(
            "max_memory_bytes", f"SVD working storage needs at least {estimated} bytes"
        )
    scaled = _scaled(templates.values, translate=options.demean, axis=0)
    centered = scaled - np.mean(scaled, axis=0) if options.demean else scaled
    try:
        singular = np.linalg.svd(centered, compute_uv=False)
    except np.linalg.LinAlgError as error:
        raise ParameterError("data", "singular-value decomposition did not converge") from error
    total = float(np.sum(singular))
    value: float | None = None
    if total > 0:
        value = shannon_entropy(
            singular / total, base=options.base, normalize=options.normalize
        ).value
    return EntropyResult(
        measure="svd",
        value=value,
        status=Status.UNDEFINED if value is None else Status.FINITE,
        n_observations=len(templates.values),
        parameters={
            "embedding": config.model_dump(mode="json"),
            "base": options.base,
            "normalize": options.normalize,
            "demean": options.demean,
        },
        diagnostics={
            "matrix_shape": list(templates.values.shape),
            "singular_values": [float(value) for value in singular],
            "weighting": "singular_values",
            "centering": "columns" if options.demean else "none",
            "amplitude_scaling": "column_midrange_then_global_max_abs"
            if options.demean
            else "global_max_abs",
        },
    )
