# Prospective synthetic operating characteristics

`power_plan.yaml` declares the entire design before the runner generates outcomes.
This is a reproducible prespecified simulation, not a preregistration. Parameters,
budgets, labels, methods, scenarios, sample sizes and uncertainty levels are read
from that file. `scripts/run_power.py` only composes field generation, registered
estimators, inference, summaries and plotting. It never reimplements an entropy
kernel or changes a threshold based on the resulting curves.

Each independent observation is one complete native field. Its coordinates are
not additional independent subjects. The periodic baseline and Bernoulli
replacement law follow the bounded MIX adaptation described in
`docs/study-design.md`; independent groups receive separate random streams even
when their generating probabilities coincide. Replacement amplitudes are uniform
with unit variance. The RNG namespaces include the design seed, scenario, shape,
group, outer repetition and subject. Inner permutation streams also consume the
declared test seed and the analysis/sample-size identities. Python's randomized
process hash is never used.

For each scenario, geometry and independent outer repetition, a maximum-size
pool is generated per group. Smaller sample-size comparisons use its prefixes.
This saves kernel work and correlates points on a curve; repetitions remain
independent. Pointwise intervals do not imply simultaneous coverage of a curve
or confirm the smallest sample size attaining a target. The target-power line is
a configured descriptive reference. Monte Carlo standard error is reported from
the configured outer repetition count, including the worst-case binomial bound.
Sampling error from the inner permutation algorithm is a separate source of
variation included in these operating characteristics.

The null is equality of the complete generating distributions. The test statistic
is the second-group minus first-group mean of whole-field estimates. A label
permutation test relies on exchangeability under that null; equal means with
unequal distributions do not establish this condition. Exact tests retain all
allocations and inclusive tails. Monte Carlo tests sample uniformly with
replacement and use the nonzero corrected tail proportion documented in
`docs/inference.md`. The recorded resolution is a grid increment, not necessarily
the smallest attainable two-sided p-value. Complementary allocations can make
the latter larger, and fixed-family multiplicity can preclude rejection entirely
at small sample sizes.

The analysis family is fixed in the plan. Holm adjustment retains every declared
member. A comparison is unavailable when either group contains any undefined or
infinite estimate; no entropy is set to zero, imputed, omitted or silently
replaced. An unavailable member contributes a conservative bookkeeping p-value
of one for the fixed-family adjustment, but its own reported p-value, effect and
test remain null and it never rejects. Thus removing a failed method cannot
shrink the multiplicity family after seeing results.

For each prespecified cell, let R be attempted outer repetitions, V available
comparisons, F unavailable comparisons and K rejected comparisons. The report
retains all four counts and distinguishes:

- K/V: rejection conditional on availability, undefined when V is zero;
- K/R: implemented unconditional rejection probability, counting failures as
  nonrejections;
- V/R: availability probability;
- [K/R, (K+F)/R]: an identification range for hypothetical decisions on missing
  comparisons. This is **not** a confidence interval.

Wilson score intervals accompany the first three binomial proportions. They have
nonzero width at observed zero or complete rejection. They are pointwise Monte
Carlo uncertainty intervals, not bootstrap intervals over correlated grid cells.
Conditional rejection can be selected by estimator availability and is not a
general power claim for all inputs. The unadjusted rejection counts are retained
separately; figure comparisons do not select the best method after simulation.
Power curves describe only the declared generator, geometry, estimator,
threshold, test, multiplicity policy and budgets, not biological performance or
the paper's empirical classification results.

All native pools, per-subject hashes, complete entropy results, actual permutation
results, decisions, denominators, summaries and CSV projections are retained.
`scripts/validate_power.py` regenerates fields, replays kernels and independently
reconstructs tests and adjustment before accepting these artifacts. Negative
controls deliberately corrupt real files and coherent records. Preflight bounds
field counts, template distance component visits, live pool-array bytes and inner
resampling work. The serialized report also has a byte limit checked before its
publication; a failure retains already generated pools. These are numerical/array bounds,
not process RSS or runtime predictions.

The simulation structure and uncertainty reporting follow
[Morris, White and Crowther (2019)](https://doi.org/10.1002/sim.8086).
Corrected random permutation probabilities follow
[Phipson and Smyth (2010)](https://doi.org/10.2202/1544-6115.1585).
The inference documentation cites the primary sources for exact/random
permutation validity, Wilson intervals, Holm adjustment and bootstrap inference.
