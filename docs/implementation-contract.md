# Implementation contract

Repository: `docxology/antropy`; distribution: `antropy-hd`; import: `antropy_hd`.
The name avoids shadowing the unrelated AntroPy time-series library.

## Shared API

`EntropyResult` is a frozen Pydantic model with `measure: str`, `value: float | None`,
`status: Status` (`finite`, `undefined`, `infinite`), `n_observations: int`,
`parameters: dict[str, JsonValue]`, and `diagnostics: dict[str, JsonValue]`.
Finite results contain finite floats; undefined/infinite values are null in strict
JSON. `as_float()` converts explicit statuses to float/nan/inf for numeric workflows.
Every public entropy API returns this model.

`as_real_array(data: ArrayLike) -> NDArray[np.float64]` rejects empty, scalar,
complex, boolean, string/object, nonfinite input and conversion overflow.
Typed `AntropyError(ValueError)` subclasses expose parameter/domain/resource failures.

`EmbeddingConfig` fields: `shape: int | tuple[int,...] = 2`,
`delay: int | tuple[int,...] = 1`, `stride: int | tuple[int,...] = 1`,
`extend_axes: tuple[int,...] | None = None`, `max_templates=10000`,
`max_pairs=50000000`, `max_memory_bytes=134217728`.
`MatchConfig`: `tolerance=0.2`, `relative=True`, `ddof=0`,
`closed=False`, `metric` in chebyshev/euclidean/cityblock,
`exclusion` in self/coordinate, `theiler=0`, `block_size=128`.
`paired_templates(array, embedding)` returns base/extended templates, origin tuples,
and geometry on common origins defined by the extended block. Flattening occurs
within each extracted block only. Guard resources before materialization.

## Measures

The numerical core separates spatial embedding, blocked pair distances,
template entropy, information measures, ordinal measures, spectral measures,
and multiscale coarse-graining. All APIs have validated keyword configuration,
explicit units, deterministic tie conventions, and common results. Orchestration
dispatches registered methods; the CLI owns file boundaries; scripts generate
research artifacts and verify provenance. Numerical modules have no plotting,
manuscript, network or repository-infrastructure dependencies.

## Scientific boundaries

HDSE means shape=m on all axes, delay/stride=1, extension on all axes, strict
Chebyshev threshold r*global SD, tuple self-exclusion. Population SD is explicit
because the paper leaves ddof unspecified. Coordinate exclusion is sensitivity
only: the paper's prose and equations disagree. Rectangular windows, selected axes,
other distances, Theiler exclusions and ND variants of other measures are extensions.
Approximate entropy uses full separate origin populations and includes self matches.
Fuzzy entropy specifies exp(-(distance/tolerance)**power), centering option and
log-domain accumulation. Multiscale specifies trimmed block means and original SD
tolerance by default. No paper experiment/classification replication claim is made.

## HDSE mathematics and equation mapping

For a finite real tensor $X$ of shape $(I_1,\ldots,I_D)$ and scalar $m\geq1$,
let the common origin set be

$$O=\prod_{d=1}^{D}\{0,\ldots,I_d-m-1\},\qquad N=\prod_d(I_d-m).$$

At each origin $i$, extract $T_m(i)=X[i_1:i_1+m,\ldots,i_D:i_D+m]$
and $T_{m+1}(i)$ at the same origin. This implements Xia-Wang equations (1)
and (5), including the intentionally excluded final base-window endpoint.
The Chebyshev distance of equation (2) is

$$d(T(i),T(j))=\max_k |T(i)_k-T(j)_k|.$$

With $\epsilon=r\sigma(X)$ and strict matching $d<\epsilon$, count unordered
distinct-origin pairs $B$ at size $m$ and $A$ at size $m+1$. Equations (3)-(4)
use average ordered matching fractions, $2B/[N(N-1)]$ and $2A/[N(N-1)]$;
the common normalization cancels in equation (6):

$$\operatorname{HDSE}(X;m,r)=\log B-\log A.$$

The estimate is undefined if $B=0$, infinite if $B>0,A=0$, and zero if
$A=B>0$. These are mathematical states, not missing observations. Defaults use
population SD (`ddof=0`); the paper does not specify the SD denominator.
The default excludes only identical origin tuples, following its equations and
denominator. Its prose instead states that every coordinate must differ; setting
`exclusion="coordinate"` selects that sensitivity variant explicitly.

Increasing every template axis adds $(m+1)^D-m^D$ constraints. Consequently,
dimension-agnostic geometry does not make raw entropy values comparable across
dimensions, nor remove exponential template-feature or quadratic pair growth.

## Resource and precision policy

`max_templates` and `max_pairs` bound exact populations; exceeding either raises
`ResourceError`. There is no sampling, silent truncation or automatic fallback.
`max_memory_bytes` bounds a conservative estimate of numerical template/pair
workspace, including extraction temporaries, both nested populations, retained
pair blocks, fuzzy buffers, and distribution-histogram buffers. It is not a
process RSS ceiling and excludes caller input, file parsing, SD preprocessing,
Python runtime, library allocator pools, and operating-system caches. Conservative
estimates can reject a request whose implementation-specific actual peak is lower.
Reducing `block_size` can reduce pair scratch while preserving exact counts.

SD is translated by the finite midrange before scaling, then its radius product
is combined by mantissa/exponent arithmetic. This preserves differences between
nearby very large finite values and avoids intermediate variance/product overflow.
Distance overflow represents a separation beyond every finite hard threshold;
distance-histogram requests reject unrepresentable distances. Fuzzy membership
uses radius-scaled coordinates and log-domain accumulation; unrepresentable kernel
coordinate ratios, eligible distances or log membership weights are rejected
explicitly as numerical range errors, rather than labeled mathematically undefined.
Input arrays are never modified.

## Primary sources for template methods

- Xia W, Wang F (2026). *High-dimensional sample entropy for uncovering rich
  complex structures in data*. Chaos, Solitons and Fractals 208, 118076.
  [DOI](https://doi.org/10.1016/j.chaos.2026.118076). Equations (1)-(6) define the
  default HDSE construction; the two explicitly identified ambiguities above
  are resolved by configuration and documented defaults.
- Pincus SM (1991). *Approximate entropy as a measure of system complexity*.
  Proceedings of the National Academy of Sciences 88, 2297-2301.
  [Primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC51218/),
  [DOI](https://doi.org/10.1073/pnas.88.6.2297).
  The implementation includes self matches and averages log matching fractions
  over separate full populations; spatial windows are a declared extension.
- Richman JS, Moorman JR (2000). *Physiological time-series analysis using
  approximate entropy and sample entropy*. American Journal of Physiology -
  Heart and Circulatory Physiology 278, H2039-H2049.
  [Publisher](https://journals.physiology.org/doi/10.1152/ajpheart.2000.278.6.h2039).
  The `sample_entropy` compatibility API uses one-dimensional common origins,
  excluded self matches, and an explicitly closed threshold by default.
- Chen W, Wang Z, Xie H, Yu W (2007). *Characterization of surface EMG signal
  based on fuzzy entropy*. IEEE Transactions on Neural Systems and
  Rehabilitation Engineering 15, 266-272.
  [Article record](https://pubmed.ncbi.nlm.nih.gov/17601197/),
  [DOI](https://doi.org/10.1109/TNSRE.2007.897025).
  This implementation chooses $\exp[-(d/\epsilon)^p]$ and optional local mean
  centering. Conventions using $\exp[-d^p/r]$ have a different scale parameter;
  the API does not equate them silently.
- Li P, Liu C, Li K, Zheng D, Liu C, Hou Y (2015). *Assessing the complexity
  of short-term heartbeat interval series by distribution entropy*. Medical
  and Biological Engineering and Computing 53, 77-87.
  [Article record](https://pubmed.ncbi.nlm.nih.gov/25351477/),
  [DOI](https://doi.org/10.1007/s11517-014-1216-0).
  Distance-distribution entropy here uses full valid spatial origins rather
  than omitting the final valid origin as in that 1D construction, normalizes
  distances by their observed maximum, and uses uniform bins on $[0,1]$.
- Costa M, Goldberger AL, Peng CK (2002). *Multiscale entropy analysis of
  complex physiologic time series*. Physical Review Letters 89, 068102.
  [Author-hosted paper](https://physionet.org/files/mse/1.0/papers/prl-2002.pdf),
  [DOI](https://doi.org/10.1103/PhysRevLett.89.068102).
  Trimmed block means and original-data tolerance follow the multiscale
  construction; ND geometry and strict HDSE matching are explicit extensions.

The remaining probability, ordinal, FFT and SVD primary sources and conventions
are recorded in [related sources](sources-related.md). Source papers establish
method provenance; their empirical claims are not adopted as antropy results.
