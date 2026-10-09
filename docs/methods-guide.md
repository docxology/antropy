# Methods guide

Choose an input interpretation before choosing a measure. A numeric amplitude
field uses axes as spatial, temporal or channel coordinates. A probability tensor
uses axes as discrete random variables and cells as joint outcomes. Passing
amplitudes to a probability API does not estimate their distribution: probabilities
must already be finite, nonnegative and sum to one. Raw counts must be explicitly
converted to probabilities. The package rejects complex, boolean, scalar, empty
and nonfinite amplitude inputs.

## Spatial geometry and HDSE

HDSE constructs local templates in the input's original dimensionality. A
rectangular `shape`, `delay` and `stride` each accept one positive integer per
axis; a scalar repeats on all axes. `extend_axes` selects which local dimensions
grow by one sample. Only the values inside an extracted window are flattened,
in C order, for componentwise comparison.

Default HDSE uses equal width on every axis, unit delay/stride, extension on every
axis, strict Chebyshev amplitude distance, and a radius equal to `tolerance`
times the original array's global standard deviation. Population SD (`ddof=0`)
is explicit. Base and extended templates use exactly the same origins, determined
by where the extended window fits. HDSE returns the natural logarithm of base
matches divided by extended matches. These conventions follow the HDSE
construction in [Xia and Wang (2026)](https://doi.org/10.1016/j.chaos.2026.118076).

The paper's prose and equations give different self-exclusion interpretations.
The default `exclusion="self"` removes only an identical origin tuple.
`exclusion="coordinate"` requires the two origins to differ on every axis and
is a separately labeled sensitivity option. `theiler` additionally excludes
origins whose largest coordinate separation is at most the specified number of
index positions. Delays, strides and Theiler separation use array indices;
physical spacing and mixed measurement units require an explicit application
model. Amplitude metrics compare local values, not physical origin coordinates.

Rectangular windows, selected extension axes, nonunit delays/strides, alternate
amplitude metrics and Theiler exclusions are configured extensions. Changing an
image into a row-major sequence changes its origin neighborhood and estimator
population. The [spatial example](../examples/spatial_embeddings.py) retains 2D/3D
geometry and prints all effective configurations and observed counts.

## Estimator families

| Measure | Input/population and convention | Raw units and normalization |
|---|---|---|
| `hdse` | Nested templates on common extended-window origins; strict threshold by default. | Nats; no alphabet normalization. |
| `sample_entropy` | 1D common-origin construction; closed threshold when no `MatchConfig` is supplied. An explicit match config determines its boundary. | Nats. |
| `approximate_entropy` | Separate complete base/extended origin populations; self matches and ordered comparisons included. Coordinate/Theiler exclusions are rejected. | Nats; the spatial construction is an extension of [Pincus (1991)](https://doi.org/10.1073/pnas.88.6.2297). |
| `fuzzy_entropy` | Membership `exp(-(distance/radius)**power)`; independent local mean centering by default; log-domain accumulation. | Nats; centered extension distances can produce negative values. |
| `distribution_entropy` | Histogram of eligible local-template pair distances divided by their observed maximum; complete local origins and explicit bin count. | Nats, divided by `ln(bins)` when normalized (default). |
| `permutation_entropy` | Stable ordinal rankings of local C-order samples; ties preserve position. | Bits by default; normalize by `log_b(k!)` for `k` local samples. |
| `weighted_permutation_entropy` | Same ordinal alphabet with each local window weighted by population variance. | Same ordinal normalization; zero total variance is undefined. |
| `spectral_entropy` | Full N-D FFT periodogram; conjugate bins count separately; explicit demeaning/DC retention. | Bits by default; normalize by the retained Fourier-bin count's logarithm. |
| `svd_entropy` | Singular values of the local trajectory matrix, without squaring them; optional column centering. | Bits by default; normalize by `log_b(min(template_count, window_width))`. |

Permutation and variance-weighted permutation definitions come from
[Bandt and Pompe (2002)](https://doi.org/10.1103/PhysRevLett.88.174102) and
[Fadlallah et al. (2013)](https://doi.org/10.1103/PhysRevE.87.022911).
Their N-D windows here are explicit spatial extensions. The full FFT convention
and the local singular-value convention are recorded in the
[source/convention record](sources-related.md); one-sided spectra, Welch estimates
and squared singular-value weights yield different distributions.

## Probability measures and fixed alphabets

Shannon, Rényi, joint/conditional entropy, mutual information and Jensen–Shannon
divergence use a selectable logarithm base greater than one: base 2 gives bits
and base `e` gives nats. Shannon follows
[Shannon (1948)](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x).
Zero probabilities contribute zero while their categories remain part of the
declared alphabet. Normalized Shannon/Rényi divide by `log_b(N)` for all `N`
cells, including zero cells. Rényi supports order zero (occupied support), one
(Shannon) and positive infinity (min-entropy); its
[original definition](https://static.renyi.hu/renyi_cikkek/1961_on_measures_of_entropy_and_information.pdf)
also identifies the Shannon limit.

Tsallis entropy uses `k=1`, finite nonnegative order and its natural-log Shannon
limit at order one. It has no logarithm-base argument. Normalization divides by
the uniform-alphabet Tsallis maximum for all cells. See
[Tsallis (1988)](https://doi.org/10.1007/BF01016429). Joint entropy covers every
axis of a joint probability tensor. Conditional entropy conditions on explicitly
selected axes; mutual information partitions axes into an explicit X set and
its complement. Neither function reconstructs those probabilities from raw data.

Weighted Jensen–Shannon divergence compares same-shaped distributions over the
same cell identities, with an explicit mixing probability. The result is the
divergence, rather than its square-root distance. The implementation preserves
nearby-distribution information using a stable convex-remainder expression and
logarithmic mixture coordinates. The definition is due to
[Lin (1991)](https://doi.org/10.1109/18.61115).

For statistical complexity, declare `StatisticalComplexityConfig(alphabet_size=N)`
and pass exactly `N` probability cells. With uniform `U_N` and a point mass
`delta_N` on that same alphabet, the implementation computes

$$
C_{JS}(P)=\frac{H(P)}{\log_b N}\,
\frac{JS_{1/2}(P,U_N)}{JS_{1/2}(\delta_N,U_N)}.
$$

The dimensionless product vanishes for a uniform distribution and for a point
mass. Both factors use the complete declared alphabet. Removing empty categories
changes the uniform reference and can change the result. The formula is the
normalized Shannon–Jensen–Shannon construction in
[Rosso et al. (2007), equations 1–3](https://doi.org/10.1103/PhysRevLett.99.154102),
within the family discussed by
[Martín, Plastino and Rosso (2006)](https://doi.org/10.1016/j.physa.2005.11.053).
The [fixed-alphabet example](../examples/fixed_alphabet.py) demonstrates explicit
tail categories and retained zero counts. Its amplitude symbols do not imply
the temporal causality of an ordinal-pattern analysis or a validated
noise-versus-chaos classifier.

`histogram_entropy` separately pools amplitude values into bins. Automatic bins
can adapt to each field's amplitude range, so a histogram entropy comparison
does not automatically hold discretization fixed. To compare fixed symbols,
choose shared cuts, retain empty and tail categories, record the equality rule
at cuts, and normalize all observed category counts explicitly.

## Multiscale boundaries and result states

`coarse_grain(data, scale)` averages aligned blocks beginning at index zero.
A scalar scale applies to every axis; a tuple permits anisotropic factors.
Incomplete high-side blocks are trimmed. For axis length `n_j` and scale `s_j`,
the output length is `floor(n_j/s_j)` and the retained input length is
`s_j*floor(n_j/s_j)`. Padding, partial-block averaging and periodic wrapping are
not alternative policies in the current API. Record the original shape and
scale when interpreting boundary loss.

`multiscale_entropy` applies HDSE to each coarse field. By default it preserves
the original array's resolved tolerance; setting `preserve_tolerance=False`
recomputes relative SD at each scale. Increasing scale can leave too few valid
extended origins and fail the whole request. The multidimensional geometry and
trimmed-block convention are specified extensions of the multiscale approach
introduced by [Costa, Goldberger and Peng (2002)](https://doi.org/10.1103/PhysRevLett.89.068102).

Inspect `status`, counts, effective parameters and diagnostics together. HDSE
with no base matches is undefined; positive base matches with no extended
matches is infinite. Zero fuzzy width, zero retained Fourier power and zero
total variance weights are undefined. A singleton alphabet has zero raw Shannon
entropy but undefined normalization by its zero maximum. Numeric range failures
raise typed errors rather than changing these mathematical states. Strict JSON
uses null for undefined/infinite values, and `as_float()` exposes numeric sentinels
for workflows that deliberately handle them.

These measures quantify different distributions and populations. Matching units
does not calibrate their scales, and a larger number is not a general ordering
of biological organization. Overlapping windows and pairs are dependent
observations. Uncertainty, stationarity assumptions and application-specific
validation require a study design beyond the example scripts.
