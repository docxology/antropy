# Inference for independent replicate estimates

Entropy estimates describe an input. Statistical inference requires a declared
observational unit, an estimand, and assumptions about replication. The APIs in
`antropy_hd.inference` therefore return `PermutationResult` or `IntervalResult`,
separately from the entropy registry. The mean-difference effect always means
**mean(second) − mean(first)**, in the units of the supplied replicate values.
For entropy in bits, the effect and bootstrap bounds are also in bits; p-values,
binomial proportions and Holm-adjusted p-values are dimensionless.

Inputs must be finite, real, one-dimensional groups with at least two observations
each. Spatial arrays are rejected rather than flattened. Boolean, object, string,
complex and nonfinite observations are rejected. Integer and floating inputs are
converted to binary64; exact arithmetic below refers to those converted values,
not to arbitrary precision integers or an unobserved continuous measurement.
Paired groups must have the same length, with corresponding observations aligned.

Overlapping spatial templates, adjacent time samples, and multiple entropy
measures from the same specimen are not automatically independent replicates.
The caller must supply experimental units whose sampling or randomization design
supports the chosen inference. These functions do not implement cluster,
block, spatial or time-series resampling. A failure to reject does not establish
equivalence, and a p-value does not measure effect size.

## Permutation tests

```python
from antropy_hd.inference import permutation_test
from antropy_hd.inference_models import Alternative, Mode, Pairing, PermutationConfig

config = PermutationConfig(
    seed=2026,
    pairing=Pairing.INDEPENDENT,
    alternative=Alternative.TWO_SIDED,
    mode=Mode.AUTO,
    resamples=9999,
    max_exact_allocations=100000,
    max_resampling_work=100000000,
)
result = permutation_test([0.1, 0.2, 0.4], [0.3, 0.5, 0.8], config=config)
print(result.model_dump_json())
```

Independent tests pool the groups and allocate `n_first` labeled observations to
the first group. Every one of the `comb(n_first + n_second, n_first)` allocations
has equal weight. Equal data values remain distinct labeled observations, so
ties retain their multiplicity. Validity requires exchangeability across labels
under the null, typically independent observations with the same null
distribution; equality of means alone does not imply that assumption.
[Phipson and Smyth (2010)](https://gksmyth.github.io/pubs/PermPValuesPreprint.pdf)
describe the label-randomization framework and sampling conventions.

Paired tests exchange labels independently within each of `n` independent pairs,
equivalently enumerate `2**n` signs of the paired differences. Validity requires
exchangeable within-pair labels under the null, as supported by a randomization
design or a sign-symmetric difference distribution. A zero average difference
alone does not justify sign flips. Pairing retains the dependence within each
pair; different pairs must be valid independent units.

The alternative specifies an inclusive tail:

| Alternative | Count a null contrast `t` when |
| --- | --- |
| `two_sided` | `abs(t) >= abs(observed)` |
| `greater` | `t >= observed` |
| `less` | `t <= observed` |

This two-sided convention uses absolute contrasts, including when unequal group
sizes make the allocation distribution asymmetric. It is not defined by doubling
one directional tail.

All tail comparisons use exact integer contrasts over a common power-of-two
denominator. This preserves exact ties, summation-order invariance, subnormal
values and representable differences near large offsets, without an epsilon.
The returned `effect` rounds the rational contrast once to binary64;
`effect_numerator` and `effect_denominator` retain the exact contrast. An effect
outside the finite binary64 range raises `ParameterError`. The exact tail ordering
can still distinguish a nonzero rational effect that rounds to zero.

`EXACT` includes the observed allocation and reports `p_value = extreme/evaluated`
with resolution `1/evaluated`. It checks the allocation ceiling and work budget
before encoding contrasts or enumerating null allocations. `AUTO` uses exact
enumeration only if both limits permit it; otherwise it checks and runs Monte
Carlo. Explicit `MONTE_CARLO` always draws the configured number of resamples.
Monte Carlo uses independent uniform allocations or sign patterns **with
replacement across draws**, including possible repeated or identity allocations.
It reports `(extreme + 1)/(resamples + 1)` and resolution `1/(resamples + 1)`, so
the p-value cannot be zero. This correction is conservative for sampling finite
permutation populations with replacement; it is not presented as exhaustive
enumeration of that population. See Phipson and Smyth, sections 4 and 6,
[DOI: 10.2202/1544-6115.1585](https://doi.org/10.2202/1544-6115.1585).

Every resampling configuration requires a nonnegative integer seed. Exact tests
retain that configuration but report `effective_seed=null` because enumeration
does not consume randomness. Monte Carlo records the actual seed. The generator
is NumPy's `default_rng`; reproducibility claims apply within the recorded NumPy
environment and configuration, rather than promising identical streams across
arbitrary future generator versions.

## Percentile bootstrap intervals

`bootstrap_interval(first, second, config=BootstrapConfig(...))` resamples each
independent group separately with replacement, retaining its original size.
With `pairing="paired"`, it resamples pair indices jointly. It computes the same
second-minus-first effect for each draw and takes empirical quantiles at
`(1-confidence_level)/2` and `1-(1-confidence_level)/2`. Linear quantiles interpolate
between order statistics at position `(resamples-1)*probability`. Convex rational
interpolation avoids overflow when two finite endpoints have an unrepresentable
binary64 difference; the final bounds are rounded once.

This is an ordinary empirical percentile bootstrap, following the resampling
principle introduced by [Efron (1979), *Bootstrap Methods: Another Look at the
Jackknife*](https://doi.org/10.1214/aos/1176344552), *The Annals of Statistics*
7(1), 1–26. The [original article scan](https://blogs.helsinki.fi/bk-club/files/2012/05/Efron_Bootstrap_AS1979.pdf)
provides the empirical-distribution construction. This implementation does not
claim bias correction, studentization, or guaranteed nominal coverage for small,
discrete, skewed or degenerate samples. A constant empirical distribution can
produce a zero-width interval; that describes the supplied empirical resamples
and does not establish population certainty. Any unrepresentable resample effect
fails explicitly; draws are never silently dropped.

## Wilson intervals and declared hypothesis families

`binomial_interval(successes, total, confidence_level=0.95)` inverts the normal
binomial score test to give a Wilson interval. Counts must be integers satisfying
`0 <= successes <= total`, excluding booleans. For `total=0`, the result is
`status="undefined"` with null estimate and bounds. With positive total, zero
successes give lower bound 0 and all successes give upper bound 1. The underlying
assumption is independent Bernoulli trials with a common success probability;
this interval is approximate rather than a guarantee of exact nominal coverage
for every binomial parameter. The original source is [Wilson (1927), *Probable
Inference, the Law of Succession, and Statistical Inference*](https://www.jstor.org/stable/2276774),
*Journal of the American Statistical Association* 22(158), 209–212,
[DOI: 10.2307/2276774](https://doi.org/10.2307/2276774).

`holm_adjust(p_values)` accepts a finite declared family of valid p-values in
`[0, 1]`. It sorts the family, multiplies the ordered p-values by descending family
sizes, takes the running maximum, caps at 1, and returns a tuple in the original
order. Equal values are retained; zero p-values are allowed as input although this
module's permutation tests never generate them. An empty declared family returns
an empty tuple. Familywise error control depends on each input p-value being valid
and on the family being declared appropriately; arbitrary selection after seeing
results is not repaired by adjustment. The source is [Holm (1979), *A Simple
Sequentially Rejective Multiple Test Procedure*](https://www.jstor.org/stable/4615733),
*Scandinavian Journal of Statistics* 6(2), 65–70; the
[original article scan](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf), section 2,
states the sequential procedure and familywise guarantee.

## Work and memory bounds

`max_samples` counts observations across both input groups, including both members
of each pair. It can be lowered from the implementation ceiling of 10,000.
`resamples` is a positive integer capped at 1,000,000. These ceilings bound
integer-encoding and bootstrap-statistic storage; they are not recommended sample
sizes. `max_resampling_work` limits the declared number of observational units
visited across draws: `evaluated*(n_first+n_second)` for independent groups and
`evaluated*n_pairs` for paired groups. Independent permutations visit at most
`n_first` selected values after the pooled sum is precomputed; their full pooled
size is a conservative resampling-unit budget. Paired calculations visit one
paired difference per unit. This count omits setup, integer bit-operation costs,
RNG internals and bootstrap sorting, and predicts neither wall time nor process
RSS. The actual count appears as `resampling_work` in each result.

Permutation null statistics are streamed; there is no array proportional to the
number of enumerated or sampled allocations. Bootstrap retains `resamples`
binary64 effects (8 bytes each), sorts that buffer in place, and generates only
one draw's indices at a time. NumPy and Python can allocate additional temporary
workspace. Integer contrasts have bounded width for finite binary64 input and the
sample ceiling. Configure budgets for the available resources and validate the
experimental design independently of computational feasibility.

The focused tests use Fraction-based independent enumeration, analytic score
intervals, manually interpolated bootstrap quantiles, real seeded allocation
streams, exact budget boundaries, and invalid-domain controls:

```sh
uv run pytest tests/test_inference.py tests/test_inference_intervals.py tests/test_inference_validation.py
```
