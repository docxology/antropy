# Inference and prospective operating characteristics {#sec:power}

## Scientific unit and declared design

Power depends on a specified generating mechanism, estimand, comparison rule and
decision threshold; it is not an intrinsic property of an entropy value. This
simulation evaluates the complete configured procedure using independently
generated whole fields [@morris2019simulation]. Pixels and overlapping template
pairs contribute to an estimator but do not become independent experimental
subjects. A same-probability stochastic scenario provides the null control;
alternative scenarios change the generating replacement probability.

The consumed design uses shapes 32, 8x10, 5x6x7, group sizes 4, 8, 16 and 64 independent outer repetitions per cell, with root seed 20261010. The comparison is independent and two_sided; the configured allocation mode is auto. The significance threshold is 0.05, interval confidence level 0.95 and configured planning target 0.8. Multiplicity policy: holm. The declared estimators are Native HDSE (r=2.5), Native HDSE (r=1.5), Normalized Shannon entropy, Statistical complexity.

| Scenario | Role | First $p$ | Second $p$ |
|---|---|---|---|
| Identical distributions | null | 0.25 | 0.25 |
| Moderate replacement contrast | alternative | 0.25 | 0.5 |
| Large replacement contrast | alternative | 0.25 | 0.75 |

| Control | Configured value |
|---|---|
| schema version | 1 |
| seed | 20261010 |
| shapes | [[32], [8, 10], [5, 6, 7]] |
| sample sizes | [4, 8, 16] |
| repetitions | 64 |
| alpha | 0.05 |
| confidence level | 0.95 |
| target power | 0.8 |
| multiplicity | "holm" |
| period | 12.0 |
| phase origin | 1 |
| symbol range | [-4.0, 4.0] |
| symbol bins | 16 |
| max input elements | 10000 |
| max fields | 20000 |
| max distance component visits | 5000000000 |
| max inference work | 100000000 |
| max pool bytes | 1048576 |
| max report bytes | 95000000 |

| Inference control | Configured value |
|---|---|
| seed | 20261011 |
| pairing | "independent" |
| resamples | 499 |
| max samples | 100 |
| max resampling work | 1000000 |
| alternative | "two_sided" |
| mode | "auto" |
| max exact allocations | 1000 |

### Native HDSE (r=2.5)

Geometry: native; registered measure: `hdse`. Explicit invocation parameters:

```json
{
  "embedding": {
    "max_memory_bytes": 134217728,
    "max_pairs": 500000,
    "max_templates": 1000,
    "shape": 2
  },
  "match": {
    "block_size": 64,
    "tolerance": 2.5
  }
}
```

### Native HDSE (r=1.5)

Geometry: native; registered measure: `hdse`. Explicit invocation parameters:

```json
{
  "embedding": {
    "max_memory_bytes": 134217728,
    "max_pairs": 500000,
    "max_templates": 1000,
    "shape": 2
  },
  "match": {
    "block_size": 64,
    "tolerance": 1.5
  }
}
```

### Normalized Shannon entropy

Geometry: symbols; registered measure: `shannon_entropy`. Explicit invocation parameters:

```json
{
  "normalize": true
}
```

### Statistical complexity

Geometry: symbols; registered measure: `statistical_complexity`. Explicit invocation parameters:

```json
{
  "config": {
    "alphabet_size": 16
  }
}
```

The report retains 1152 stored pools, 18432 whole-field estimator records and 6912 inference decisions: 6336 available and 576 unavailable. It emits 108 operating-characteristic cells. The preflight worst-case binomial Monte Carlo standard-error bound is 0.0625; it is a simulation-precision bound, not a statement of scientific effect precision.

| $n$ | Allocations | Evaluated | Mode | Work | Grid increment |
|---|---|---|---|---|---|
| 4 | 70 | 70 | exact | 560 | 0.0142857 |
| 8 | 12870 | 499 | monte_carlo | 7984 | 0.002 |
| 16 | 601080390 | 499 | monte_carlo | 15968 | 0.002 |

For equal-sized groups with exact two-sided enumeration, every allocation has a distinct complementary allocation with the same absolute contrast. The minimum attainable p-value is at least twice the exact grid increment. Ties can increase it. The first Holm threshold is alpha divided by the declared family size; if even this lower bound exceeds that threshold, no family member can reject. This necessary-condition calculation does not guarantee rejection at other group sizes.

| $n$ | Two-sided p floor | First threshold | Rejection by floor |
|---|---|---|---|
| 4 | 0.0285714 | 0.0125 | precluded |

| Scheduled resource | Count |
|---|---|
| Fields | 18432 |
| Decisions | 6912 |
| Distance component visits | 1971634176 |
| Inference scalar work | 56475648 |
| Peak live pool arrays (bytes) | 53760 |

\begingroup\small

```text
Power plan:   de602e182e541b4a64956b1dc30b661c29ac4f2f4b742a9695de245c80fb2914
Power report: 1e4ff2f8b8a38d3c29916d3d6f905ffb3ebbf240c2f0adfaa6526f2b1b1fb301
```

\endgroup

Sample-size comparisons reuse prefixes of each maximum-size subject pool.
Within a given cell, outer repetitions use separate streams; estimates across
sample sizes and estimators need not be independent. Reported
intervals are pointwise rather than simultaneous confidence bands. The
configured target is a planning input, not a certified sample-size recommendation
or an estimate of post hoc observed power.

## Permutation decisions and multiplicity

For independent field groups, the statistic is the second-group mean minus the
first-group mean. The null assumption is exchangeability of the whole-field
observations under identical generating distributions. The separate paired API
uses within-pair contrasts and exchangeable sign flips; the current field
generator supplies independent groups instead.

With exact enumeration, $p=e/A$ for $e$ inclusive-tail allocations among all $A$
allocations, including the observed allocation. With $B$ sampled allocations,
the Monte Carlo correction is $p=(b+1)/(B+1)$ [@phipson2010permutation]. Inclusive
tails are compared using exact rational contrasts of the stored binary64 inputs;
reporting a floating-point effect does not change the tail decision. The recorded
p-value grid increment need not equal the smallest attainable two-sided p-value,
because complementary allocations can have the same absolute statistic.

When Holm adjustment is selected, ordered p-values use the running maximum
of $(K-i+1)p_{(i)}$, clipped at one and returned to the original order
[@holm1979]. The declared family includes every configured estimator. Unavailable
comparisons keep null observed p-values and cannot reject; a value of one is used
only internally for conservative family bookkeeping. Raw and adjusted rejection
counts remain separate in the producer report.

## Availability, rejection rates and uncertainty

Let $R$ be attempted outer repetitions, $C$ available comparisons, $U=R-C$
unavailable comparisons and $J$ selected rejections. The report distinguishes

$$
\widehat q_{\mathrm{conditional}}=J/C\quad(C>0),\qquad
\widehat q_{\mathrm{procedure}}=J/R,\qquad
\widehat a=C/R.
$$ {#eq:power-denominators}

Conditional rejection is undefined when no comparison is available. The
unconditional rate describes the implemented procedure that declines to reject
on unavailable comparisons. Under a null scenario it is a false-positive
operating characteristic; under a declared alternative it is a prospective
detection rate. Neither quantity is a biological classification accuracy.

Wilson score intervals quantify binomial Monte Carlo uncertainty at the
configured confidence level [@brown2001interval]. If $\widehat q=J/R$ and $z$ is
the configured normal quantile, their center and half-width are

$$
c=\frac{\widehat q+z^2/(2R)}{1+z^2/R},\qquad
h=\frac{z\sqrt{\widehat q(1-\widehat q)/R+z^2/(4R^2)}}{1+z^2/R}.
$$ {#eq:wilson}

The separate interval conditional on availability uses denominator $C$.
Missing-decision identification bounds $[J/R,(J+U)/R]$ are sensitivity bounds,
not confidence intervals. They show the range obtained by leaving unknown
decisions unresolved rather than imputing zero entropy or deleting a field.

For a true cell rejection probability $q$, the outer simulation standard error
is $\sqrt{q(1-q)/R}$, bounded above by $1/(2\sqrt R)$. This bound concerns
simulation precision. It does not quantify an entropy estimator's bias or
guarantee the configured power target is attained.

### Identical distributions

| Shape | $n$ | Method | Available/R | Rejects/R | Unconditional [CI] |
|---|---|---|---|---|---|
| 5x6x7 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 8 | Native HDSE (r=2.5) | 64/64 | 4/64 | 0.0625 [0.0245712, 0.149975] |
| 5x6x7 | 8 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 8 | Normalized Shannon entropy | 64/64 | 2/64 | 0.03125 [0.00861214, 0.106973] |
| 5x6x7 | 8 | Statistical complexity | 64/64 | 2/64 | 0.03125 [0.00861214, 0.106973] |
| 5x6x7 | 16 | Native HDSE (r=2.5) | 64/64 | 4/64 | 0.0625 [0.0245712, 0.149975] |
| 5x6x7 | 16 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 16 | Normalized Shannon entropy | 64/64 | 1/64 | 0.015625 [0.00276354, 0.083341] |
| 5x6x7 | 16 | Statistical complexity | 64/64 | 1/64 | 0.015625 [0.00276354, 0.083341] |
| 8x10 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 8 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 8 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 8 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 8 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 16 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 16 | Native HDSE (r=1.5) | 64/64 | 2/64 | 0.03125 [0.00861214, 0.106973] |
| 8x10 | 16 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 16 | Statistical complexity | 64/64 | 2/64 | 0.03125 [0.00861214, 0.106973] |
| 32 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 8 | Native HDSE (r=2.5) | 64/64 | 2/64 | 0.03125 [0.00861214, 0.106973] |
| 32 | 8 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 8 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 8 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 16 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 16 | Native HDSE (r=1.5) | 64/64 | 1/64 | 0.015625 [0.00276354, 0.083341] |
| 32 | 16 | Normalized Shannon entropy | 64/64 | 1/64 | 0.015625 [0.00276354, 0.083341] |
| 32 | 16 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |

### Moderate replacement contrast

| Shape | $n$ | Method | Available/R | Rejects/R | Unconditional [CI] |
|---|---|---|---|---|---|
| 5x6x7 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 8 | Native HDSE (r=2.5) | 64/64 | 18/64 | 0.28125 [0.185934, 0.401339] |
| 5x6x7 | 8 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 8 | Normalized Shannon entropy | 64/64 | 64/64 | 1 [0.943376, 1] |
| 5x6x7 | 8 | Statistical complexity | 64/64 | 63/64 | 0.984375 [0.916659, 0.997236] |
| 5x6x7 | 16 | Native HDSE (r=2.5) | 64/64 | 33/64 | 0.515625 [0.395816, 0.633664] |
| 5x6x7 | 16 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 16 | Normalized Shannon entropy | 64/64 | 64/64 | 1 [0.943376, 1] |
| 5x6x7 | 16 | Statistical complexity | 64/64 | 64/64 | 1 [0.943376, 1] |
| 8x10 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 8 | Native HDSE (r=2.5) | 64/64 | 47/64 | 0.734375 [0.615171, 0.827036] |
| 8x10 | 8 | Native HDSE (r=1.5) | 64/64 | 58/64 | 0.90625 [0.810171, 0.956322] |
| 8x10 | 8 | Normalized Shannon entropy | 64/64 | 3/64 | 0.046875 [0.016069, 0.128997] |
| 8x10 | 8 | Statistical complexity | 64/64 | 12/64 | 0.1875 [0.110646, 0.299744] |
| 8x10 | 16 | Native HDSE (r=2.5) | 64/64 | 62/64 | 0.96875 [0.893027, 0.991388] |
| 8x10 | 16 | Native HDSE (r=1.5) | 64/64 | 63/64 | 0.984375 [0.916659, 0.997236] |
| 8x10 | 16 | Normalized Shannon entropy | 64/64 | 3/64 | 0.046875 [0.016069, 0.128997] |
| 8x10 | 16 | Statistical complexity | 64/64 | 31/64 | 0.484375 [0.366336, 0.604184] |
| 32 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 8 | Native HDSE (r=2.5) | 64/64 | 2/64 | 0.03125 [0.00861214, 0.106973] |
| 32 | 8 | Native HDSE (r=1.5) | 64/64 | 13/64 | 0.203125 [0.122734, 0.317136] |
| 32 | 8 | Normalized Shannon entropy | 64/64 | 17/64 | 0.265625 [0.172964, 0.384829] |
| 32 | 8 | Statistical complexity | 64/64 | 3/64 | 0.046875 [0.016069, 0.128997] |
| 32 | 16 | Native HDSE (r=2.5) | 64/64 | 6/64 | 0.09375 [0.0436783, 0.189829] |
| 32 | 16 | Native HDSE (r=1.5) | 64/64 | 42/64 | 0.65625 [0.534036, 0.760769] |
| 32 | 16 | Normalized Shannon entropy | 64/64 | 41/64 | 0.640625 [0.518209, 0.747116] |
| 32 | 16 | Statistical complexity | 64/64 | 7/64 | 0.109375 [0.0540011, 0.208986] |

### Large replacement contrast

| Shape | $n$ | Method | Available/R | Rejects/R | Unconditional [CI] |
|---|---|---|---|---|---|
| 5x6x7 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 8 | Native HDSE (r=2.5) | 64/64 | 37/64 | 0.578125 [0.4561, 0.691302] |
| 5x6x7 | 8 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 8 | Normalized Shannon entropy | 64/64 | 64/64 | 1 [0.943376, 1] |
| 5x6x7 | 8 | Statistical complexity | 64/64 | 48/64 | 0.75 [0.631837, 0.839851] |
| 5x6x7 | 16 | Native HDSE (r=2.5) | 64/64 | 59/64 | 0.921875 [0.829805, 0.966169] |
| 5x6x7 | 16 | Native HDSE (r=1.5) | 0/64 | 0/64 | 0 [0, 0.0566241] |
| 5x6x7 | 16 | Normalized Shannon entropy | 64/64 | 64/64 | 1 [0.943376, 1] |
| 5x6x7 | 16 | Statistical complexity | 64/64 | 64/64 | 1 [0.943376, 1] |
| 8x10 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 8x10 | 8 | Native HDSE (r=2.5) | 64/64 | 64/64 | 1 [0.943376, 1] |
| 8x10 | 8 | Native HDSE (r=1.5) | 64/64 | 64/64 | 1 [0.943376, 1] |
| 8x10 | 8 | Normalized Shannon entropy | 64/64 | 25/64 | 0.390625 [0.280556, 0.513081] |
| 8x10 | 8 | Statistical complexity | 64/64 | 61/64 | 0.953125 [0.871003, 0.983931] |
| 8x10 | 16 | Native HDSE (r=2.5) | 64/64 | 64/64 | 1 [0.943376, 1] |
| 8x10 | 16 | Native HDSE (r=1.5) | 64/64 | 64/64 | 1 [0.943376, 1] |
| 8x10 | 16 | Normalized Shannon entropy | 64/64 | 46/64 | 0.71875 [0.598661, 0.814066] |
| 8x10 | 16 | Statistical complexity | 64/64 | 64/64 | 1 [0.943376, 1] |
| 32 | 4 | Native HDSE (r=2.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Native HDSE (r=1.5) | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Normalized Shannon entropy | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 4 | Statistical complexity | 64/64 | 0/64 | 0 [0, 0.0566241] |
| 32 | 8 | Native HDSE (r=2.5) | 64/64 | 11/64 | 0.171875 [0.0987774, 0.282132] |
| 32 | 8 | Native HDSE (r=1.5) | 64/64 | 29/64 | 0.453125 [0.337294, 0.574264] |
| 32 | 8 | Normalized Shannon entropy | 64/64 | 48/64 | 0.75 [0.631837, 0.839851] |
| 32 | 8 | Statistical complexity | 64/64 | 8/64 | 0.125 [0.0647224, 0.227746] |
| 32 | 16 | Native HDSE (r=2.5) | 64/64 | 20/64 | 0.3125 [0.212311, 0.433923] |
| 32 | 16 | Native HDSE (r=1.5) | 64/64 | 51/64 | 0.796875 [0.682864, 0.877266] |
| 32 | 16 | Normalized Shannon entropy | 64/64 | 63/64 | 0.984375 [0.916659, 0.997236] |
| 32 | 16 | Statistical complexity | 64/64 | 22/64 | 0.34375 [0.239231, 0.465964] |

\clearpage

![Prospective whole-field rejection rates at alpha 0.05, with holm adjustment over 4 declared estimators. Each cell uses 64 outer repetitions and group sizes 4, 8, 16. Solid curves count all attempts; dotted curves condition on availability, with gaps where no comparison is available. Shading shows pointwise Wilson intervals at confidence level 0.95. Horizontal references show the configured target 0.8 and alpha. Unavailable decisions remain unrejected in unconditional rates.](../../output/power/figures/rejection-rates.png){#fig:power-rejection width=100% fig-pos=p}

\clearpage

### Identical distributions

| Shape | $n$ | Method | Availability [CI] | Conditional [CI] | Missing bounds |
|---|---|---|---|---|---|
| 5x6x7 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 4 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.0625 [0.0245712, 0.149975] | [0.0625, 0.0625] |
| 5x6x7 | 8 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.03125 [0.00861214, 0.106973] | [0.03125, 0.03125] |
| 5x6x7 | 8 | Statistical complexity | 1 [0.943376, 1] | 0.03125 [0.00861214, 0.106973] | [0.03125, 0.03125] |
| 5x6x7 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.0625 [0.0245712, 0.149975] | [0.0625, 0.0625] |
| 5x6x7 | 16 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.015625 [0.00276354, 0.083341] | [0.015625, 0.015625] |
| 5x6x7 | 16 | Statistical complexity | 1 [0.943376, 1] | 0.015625 [0.00276354, 0.083341] | [0.015625, 0.015625] |
| 8x10 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 8 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 8 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 16 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.03125 [0.00861214, 0.106973] | [0.03125, 0.03125] |
| 8x10 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 16 | Statistical complexity | 1 [0.943376, 1] | 0.03125 [0.00861214, 0.106973] | [0.03125, 0.03125] |
| 32 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.03125 [0.00861214, 0.106973] | [0.03125, 0.03125] |
| 32 | 8 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 8 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 16 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.015625 [0.00276354, 0.083341] | [0.015625, 0.015625] |
| 32 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.015625 [0.00276354, 0.083341] | [0.015625, 0.015625] |
| 32 | 16 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |

### Moderate replacement contrast

| Shape | $n$ | Method | Availability [CI] | Conditional [CI] | Missing bounds |
|---|---|---|---|---|---|
| 5x6x7 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 4 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.28125 [0.185934, 0.401339] | [0.28125, 0.28125] |
| 5x6x7 | 8 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 5x6x7 | 8 | Statistical complexity | 1 [0.943376, 1] | 0.984375 [0.916659, 0.997236] | [0.984375, 0.984375] |
| 5x6x7 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.515625 [0.395816, 0.633664] | [0.515625, 0.515625] |
| 5x6x7 | 16 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 5x6x7 | 16 | Statistical complexity | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 8x10 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.734375 [0.615171, 0.827036] | [0.734375, 0.734375] |
| 8x10 | 8 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.90625 [0.810171, 0.956322] | [0.90625, 0.90625] |
| 8x10 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.046875 [0.016069, 0.128997] | [0.046875, 0.046875] |
| 8x10 | 8 | Statistical complexity | 1 [0.943376, 1] | 0.1875 [0.110646, 0.299744] | [0.1875, 0.1875] |
| 8x10 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.96875 [0.893027, 0.991388] | [0.96875, 0.96875] |
| 8x10 | 16 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.984375 [0.916659, 0.997236] | [0.984375, 0.984375] |
| 8x10 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.046875 [0.016069, 0.128997] | [0.046875, 0.046875] |
| 8x10 | 16 | Statistical complexity | 1 [0.943376, 1] | 0.484375 [0.366336, 0.604184] | [0.484375, 0.484375] |
| 32 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.03125 [0.00861214, 0.106973] | [0.03125, 0.03125] |
| 32 | 8 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.203125 [0.122734, 0.317136] | [0.203125, 0.203125] |
| 32 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.265625 [0.172964, 0.384829] | [0.265625, 0.265625] |
| 32 | 8 | Statistical complexity | 1 [0.943376, 1] | 0.046875 [0.016069, 0.128997] | [0.046875, 0.046875] |
| 32 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.09375 [0.0436783, 0.189829] | [0.09375, 0.09375] |
| 32 | 16 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.65625 [0.534036, 0.760769] | [0.65625, 0.65625] |
| 32 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.640625 [0.518209, 0.747116] | [0.640625, 0.640625] |
| 32 | 16 | Statistical complexity | 1 [0.943376, 1] | 0.109375 [0.0540011, 0.208986] | [0.109375, 0.109375] |

### Large replacement contrast

| Shape | $n$ | Method | Availability [CI] | Conditional [CI] | Missing bounds |
|---|---|---|---|---|---|
| 5x6x7 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 4 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 5x6x7 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.578125 [0.4561, 0.691302] | [0.578125, 0.578125] |
| 5x6x7 | 8 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 5x6x7 | 8 | Statistical complexity | 1 [0.943376, 1] | 0.75 [0.631837, 0.839851] | [0.75, 0.75] |
| 5x6x7 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.921875 [0.829805, 0.966169] | [0.921875, 0.921875] |
| 5x6x7 | 16 | Native HDSE (r=1.5) | 0 [0, 0.0566241] | undefined | [0, 1] |
| 5x6x7 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 5x6x7 | 16 | Statistical complexity | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 8x10 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 8x10 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 8x10 | 8 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 8x10 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.390625 [0.280556, 0.513081] | [0.390625, 0.390625] |
| 8x10 | 8 | Statistical complexity | 1 [0.943376, 1] | 0.953125 [0.871003, 0.983931] | [0.953125, 0.953125] |
| 8x10 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 8x10 | 16 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 8x10 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.71875 [0.598661, 0.814066] | [0.71875, 0.71875] |
| 8x10 | 16 | Statistical complexity | 1 [0.943376, 1] | 1 [0.943376, 1] | [1, 1] |
| 32 | 4 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Normalized Shannon entropy | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 4 | Statistical complexity | 1 [0.943376, 1] | 0 [0, 0.0566241] | [0, 0] |
| 32 | 8 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.171875 [0.0987774, 0.282132] | [0.171875, 0.171875] |
| 32 | 8 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.453125 [0.337294, 0.574264] | [0.453125, 0.453125] |
| 32 | 8 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.75 [0.631837, 0.839851] | [0.75, 0.75] |
| 32 | 8 | Statistical complexity | 1 [0.943376, 1] | 0.125 [0.0647224, 0.227746] | [0.125, 0.125] |
| 32 | 16 | Native HDSE (r=2.5) | 1 [0.943376, 1] | 0.3125 [0.212311, 0.433923] | [0.3125, 0.3125] |
| 32 | 16 | Native HDSE (r=1.5) | 1 [0.943376, 1] | 0.796875 [0.682864, 0.877266] | [0.796875, 0.796875] |
| 32 | 16 | Normalized Shannon entropy | 1 [0.943376, 1] | 0.984375 [0.916659, 0.997236] | [0.984375, 0.984375] |
| 32 | 16 | Statistical complexity | 1 [0.943376, 1] | 0.34375 [0.239231, 0.465964] | [0.34375, 0.34375] |

\clearpage

![Availability and unconditional null calibration for Identical distributions (p=0.25 in both groups). Raw rejection is compared with holm adjustment over 4 declared estimators at alpha 0.05. Whole fields are the independent units; 64 repetitions estimate each cell. Intervals are pointwise at confidence level 0.95.](../../output/power/figures/availability-calibration.png){#fig:power-availability width=100% fig-pos=p}

\clearpage

## Effect summaries and bootstrap interface

Mean differences retain each estimator's configured units. Their reported means
and sample standard deviations condition on available comparisons; unavailable
effects remain null. Empirical variation among outer repetitions and the
Monte Carlo uncertainty of a rejection proportion are different quantities.

### Identical distributions

\begingroup\small\setlength{\tabcolsep}{8pt}

| Shape | $n$ | Method | Mean $\Delta$ | SD | Raw | Adj. |
|----------|-----:|-------------------------|--------------------:|--------------------:|----------:|----------:|
| 5x6x7 | 4 | Native HDSE (r=2.5) | 0.0079771 | 0.499975 | 6 | 0 |
| 5x6x7 | 4 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 4 | Normalized Shannon entropy | 0.000465629 | 0.00874333 | 0 | 0 |
| 5x6x7 | 4 | Statistical complexity | 8.73969e-05 | 0.00293578 | 1 | 0 |
| 5x6x7 | 8 | Native HDSE (r=2.5) | 0.0110846 | 0.3332 | 5 | 4 |
| 5x6x7 | 8 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 8 | Normalized Shannon entropy | -0.000363409 | 0.00665451 | 4 | 2 |
| 5x6x7 | 8 | Statistical complexity | 0.000327146 | 0.00232198 | 4 | 2 |
| 5x6x7 | 16 | Native HDSE (r=2.5) | 0.00720238 | 0.233063 | 6 | 4 |
| 5x6x7 | 16 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 16 | Normalized Shannon entropy | -0.000233572 | 0.00485811 | 2 | 1 |
| 5x6x7 | 16 | Statistical complexity | 0.000267878 | 0.00160841 | 2 | 1 |
| 8x10 | 4 | Native HDSE (r=2.5) | 0.000128229 | 0.0319748 | 1 | 0 |
| 8x10 | 4 | Native HDSE (r=1.5) | 0.0128598 | 0.162703 | 2 | 0 |
| 8x10 | 4 | Normalized Shannon entropy | -0.00027704 | 0.0113081 | 3 | 0 |
| 8x10 | 4 | Statistical complexity | -0.000342759 | 0.00218425 | 0 | 0 |
| 8x10 | 8 | Native HDSE (r=2.5) | 0.000280026 | 0.0233939 | 2 | 0 |
| 8x10 | 8 | Native HDSE (r=1.5) | 0.00905552 | 0.106368 | 1 | 0 |
| 8x10 | 8 | Normalized Shannon entropy | 0.000518915 | 0.00762356 | 4 | 0 |
| 8x10 | 8 | Statistical complexity | -0.000204289 | 0.00151584 | 2 | 0 |
| 8x10 | 16 | Native HDSE (r=2.5) | 0.00341973 | 0.0179267 | 2 | 0 |
| 8x10 | 16 | Native HDSE (r=1.5) | 0.013453 | 0.0848148 | 2 | 2 |
| 8x10 | 16 | Normalized Shannon entropy | 0.000831496 | 0.00487999 | 4 | 0 |
| 8x10 | 16 | Statistical complexity | -0.000162677 | 0.00112663 | 3 | 2 |
| 32 | 4 | Native HDSE (r=2.5) | 0.00119658 | 0.011672 | 1 | 0 |
| 32 | 4 | Native HDSE (r=1.5) | 0.00980362 | 0.0355917 | 2 | 0 |
| 32 | 4 | Normalized Shannon entropy | -0.00112075 | 0.0209735 | 2 | 0 |
| 32 | 4 | Statistical complexity | 0.000143083 | 0.00264442 | 1 | 0 |
| 32 | 8 | Native HDSE (r=2.5) | 0.00123023 | 0.00742757 | 2 | 2 |
| 32 | 8 | Native HDSE (r=1.5) | 0.00533874 | 0.0222971 | 0 | 0 |
| 32 | 8 | Normalized Shannon entropy | 0.00014562 | 0.013859 | 2 | 0 |
| 32 | 8 | Statistical complexity | 0.000185304 | 0.00164353 | 2 | 0 |
| 32 | 16 | Native HDSE (r=2.5) | 0.000501501 | 0.0053336 | 2 | 0 |
| 32 | 16 | Native HDSE (r=1.5) | 0.00437018 | 0.0208222 | 1 | 1 |
| 32 | 16 | Normalized Shannon entropy | 0.000254737 | 0.0108428 | 1 | 1 |
| 32 | 16 | Statistical complexity | -5.40386e-05 | 0.00141895 | 3 | 0 |

\endgroup

### Moderate replacement contrast

\begingroup\small\setlength{\tabcolsep}{8pt}

| Shape | $n$ | Method | Mean $\Delta$ | SD | Raw | Adj. |
|----------|-----:|-------------------------|--------------------:|--------------------:|----------:|----------:|
| 5x6x7 | 4 | Native HDSE (r=2.5) | -0.401807 | 0.313747 | 7 | 0 |
| 5x6x7 | 4 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 4 | Normalized Shannon entropy | 0.0566313 | 0.0104234 | 63 | 0 |
| 5x6x7 | 4 | Statistical complexity | -0.0137403 | 0.00409393 | 45 | 0 |
| 5x6x7 | 8 | Native HDSE (r=2.5) | -0.480408 | 0.254119 | 28 | 18 |
| 5x6x7 | 8 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 8 | Normalized Shannon entropy | 0.055641 | 0.00661119 | 64 | 64 |
| 5x6x7 | 8 | Statistical complexity | -0.0133952 | 0.00265866 | 63 | 63 |
| 5x6x7 | 16 | Native HDSE (r=2.5) | -0.452019 | 0.177469 | 42 | 33 |
| 5x6x7 | 16 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 16 | Normalized Shannon entropy | 0.0555227 | 0.00448515 | 64 | 64 |
| 5x6x7 | 16 | Statistical complexity | -0.0134184 | 0.00210074 | 64 | 64 |
| 8x10 | 4 | Native HDSE (r=2.5) | 0.100478 | 0.0396488 | 23 | 0 |
| 8x10 | 4 | Native HDSE (r=1.5) | 0.501634 | 0.184456 | 26 | 0 |
| 8x10 | 4 | Normalized Shannon entropy | -0.00193156 | 0.00912914 | 1 | 0 |
| 8x10 | 4 | Statistical complexity | 0.00386839 | 0.00275411 | 3 | 0 |
| 8x10 | 8 | Native HDSE (r=2.5) | 0.102142 | 0.0226454 | 58 | 47 |
| 8x10 | 8 | Native HDSE (r=1.5) | 0.525782 | 0.103121 | 63 | 58 |
| 8x10 | 8 | Normalized Shannon entropy | -0.00040937 | 0.00729443 | 4 | 3 |
| 8x10 | 8 | Statistical complexity | 0.00341839 | 0.00211569 | 19 | 12 |
| 8x10 | 16 | Native HDSE (r=2.5) | 0.100598 | 0.0193475 | 64 | 62 |
| 8x10 | 16 | Native HDSE (r=1.5) | 0.535309 | 0.0839673 | 64 | 63 |
| 8x10 | 16 | Normalized Shannon entropy | -0.00125023 | 0.00489409 | 4 | 3 |
| 8x10 | 16 | Statistical complexity | 0.00337688 | 0.00143883 | 35 | 31 |
| 32 | 4 | Native HDSE (r=2.5) | 0.00746029 | 0.0114391 | 4 | 0 |
| 32 | 4 | Native HDSE (r=1.5) | 0.0608876 | 0.0433475 | 6 | 0 |
| 32 | 4 | Normalized Shannon entropy | 0.0337575 | 0.0201683 | 9 | 0 |
| 32 | 4 | Statistical complexity | -0.00217528 | 0.00308082 | 2 | 0 |
| 32 | 8 | Native HDSE (r=2.5) | 0.00611197 | 0.00785284 | 4 | 2 |
| 32 | 8 | Native HDSE (r=1.5) | 0.0624163 | 0.0280534 | 28 | 13 |
| 32 | 8 | Normalized Shannon entropy | 0.0343612 | 0.0163264 | 37 | 17 |
| 32 | 8 | Statistical complexity | -0.0019657 | 0.00218381 | 9 | 3 |
| 32 | 16 | Native HDSE (r=2.5) | 0.00728931 | 0.00582401 | 13 | 6 |
| 32 | 16 | Native HDSE (r=1.5) | 0.0620799 | 0.0228046 | 48 | 42 |
| 32 | 16 | Normalized Shannon entropy | 0.0364256 | 0.0124558 | 53 | 41 |
| 32 | 16 | Statistical complexity | -0.00236393 | 0.00155549 | 10 | 7 |

\endgroup

### Large replacement contrast

\begingroup\small\setlength{\tabcolsep}{8pt}

| Shape | $n$ | Method | Mean $\Delta$ | SD | Raw | Adj. |
|----------|-----:|-------------------------|--------------------:|--------------------:|----------:|----------:|
| 5x6x7 | 4 | Native HDSE (r=2.5) | -0.621122 | 0.344539 | 18 | 0 |
| 5x6x7 | 4 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 4 | Normalized Shannon entropy | 0.0551501 | 0.00700463 | 64 | 0 |
| 5x6x7 | 4 | Statistical complexity | -0.010481 | 0.00384784 | 29 | 0 |
| 5x6x7 | 8 | Native HDSE (r=2.5) | -0.643889 | 0.233606 | 44 | 37 |
| 5x6x7 | 8 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 8 | Normalized Shannon entropy | 0.0558269 | 0.00543524 | 64 | 64 |
| 5x6x7 | 8 | Statistical complexity | -0.0107382 | 0.00278446 | 56 | 48 |
| 5x6x7 | 16 | Native HDSE (r=2.5) | -0.642828 | 0.166691 | 62 | 59 |
| 5x6x7 | 16 | Native HDSE (r=1.5) | - | - | 0 | 0 |
| 5x6x7 | 16 | Normalized Shannon entropy | 0.0548904 | 0.00426106 | 64 | 64 |
| 5x6x7 | 16 | Statistical complexity | -0.0101608 | 0.00206099 | 64 | 64 |
| 8x10 | 4 | Native HDSE (r=2.5) | 0.174859 | 0.0510583 | 48 | 0 |
| 8x10 | 4 | Native HDSE (r=1.5) | 0.982899 | 0.199453 | 61 | 0 |
| 8x10 | 4 | Normalized Shannon entropy | -0.0136454 | 0.0107619 | 9 | 0 |
| 8x10 | 4 | Statistical complexity | 0.0105099 | 0.00384207 | 37 | 0 |
| 8x10 | 8 | Native HDSE (r=2.5) | 0.177121 | 0.031014 | 64 | 64 |
| 8x10 | 8 | Native HDSE (r=1.5) | 0.984111 | 0.143202 | 64 | 64 |
| 8x10 | 8 | Normalized Shannon entropy | -0.0145816 | 0.00796583 | 25 | 25 |
| 8x10 | 8 | Statistical complexity | 0.0111532 | 0.00294683 | 63 | 61 |
| 8x10 | 16 | Native HDSE (r=2.5) | 0.178323 | 0.0236021 | 64 | 64 |
| 8x10 | 16 | Native HDSE (r=1.5) | 0.989584 | 0.104276 | 64 | 64 |
| 8x10 | 16 | Normalized Shannon entropy | -0.0141923 | 0.00524524 | 46 | 46 |
| 8x10 | 16 | Statistical complexity | 0.0109956 | 0.00187163 | 64 | 64 |
| 32 | 4 | Native HDSE (r=2.5) | 0.00989782 | 0.0128064 | 5 | 0 |
| 32 | 4 | Native HDSE (r=1.5) | 0.0777537 | 0.0403601 | 15 | 0 |
| 32 | 4 | Normalized Shannon entropy | 0.0537122 | 0.0211495 | 25 | 0 |
| 32 | 4 | Statistical complexity | -0.00268643 | 0.00338277 | 5 | 0 |
| 32 | 8 | Native HDSE (r=2.5) | 0.0106385 | 0.00956086 | 15 | 11 |
| 32 | 8 | Native HDSE (r=1.5) | 0.0783142 | 0.0275142 | 43 | 29 |
| 32 | 8 | Normalized Shannon entropy | 0.0527435 | 0.0153472 | 58 | 48 |
| 32 | 8 | Statistical complexity | -0.00310831 | 0.00249848 | 10 | 8 |
| 32 | 16 | Native HDSE (r=2.5) | 0.0107698 | 0.00652311 | 27 | 20 |
| 32 | 16 | Native HDSE (r=1.5) | 0.0767366 | 0.0215585 | 59 | 51 |
| 32 | 16 | Normalized Shannon entropy | 0.0543095 | 0.0120494 | 64 | 63 |
| 32 | 16 | Statistical complexity | -0.00335883 | 0.00178672 | 27 | 22 |

\endgroup

The public percentile-bootstrap interface resamples whole observations within
independent groups, or paired observations jointly, and returns configured
empirical-quantile bounds [@efron1979bootstrap]. It is a separate inference tool;
the operating-characteristic simulation uses permutation decisions and Wilson
intervals. For bootstrap contrasts $D^*=\overline Y^*-\overline X^*$ and configured
confidence level $c$, the percentile limits are
$[Q_{(1-c)/2}(D^*),Q_{(1+c)/2}(D^*)]$, using linear interpolation of empirical
quantiles. The paired variant resamples subject pairs together and retains their
within-pair dependence. Small, discrete, sparse and degenerate samples can limit percentile
coverage. Application-specific dependence, effect size, generating assumptions
and external validation remain necessary before choosing a scientific sample
size or transferring the synthetic results to ant behavior.
