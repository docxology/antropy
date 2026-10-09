# Computational work and memory planning

Use `estimate_complexity(input_shape, ComplexityConfig(...))` before allocating
large fields or scheduling sweeps. The planner operates on integer geometry;
it constructs no input array, template matrix or origin grid. It reports the
current implementation's populations, scheduled distance work and conservative
resource guards for HDSE, 1D sample entropy, approximate entropy, fuzzy entropy,
distance-distribution entropy, permutation/weighted permutation, full FFT
spectral entropy and local SVD entropy. Unmodeled measures fail explicitly.

`feasible` means that the modeled resource guards fit their declared limits.
It does not imply finite entropy or valid numeric input values. Shape-dependent
parameter failures, including invalid embedding spans and SD degrees of freedom,
raise errors. Fuzzy kernel work is conditional on a positive resolved radius;
constant input with relative tolerance can skip its kernels. A known zero
configured fuzzy tolerance is planned as template extraction without distance
work. Later numerical errors can terminate a planned path early.

## Geometry determines the population

For input axis lengths `n_j`, window widths `m_j`, delays `d_j` and origin strides
`s_j`, a full local population has

$$
q_j=\left\lfloor\frac{n_j-(m_j-1)d_j-1}{s_j}\right\rfloor+1,
\qquad K=\prod_jq_j,\qquad k=\prod_jm_j.
$$

HDSE/SampEn/FuzzyEn resolve `q_j` from the extended shape and reuse those origins
for both template widths. ApEn constructs separate full populations for the two
shapes and releases the first before allocating the second. Ordinal, SVD and
distribution entropy use a single full local population; distribution entropy
reuses it for its maximum-distance and histogram passes.

With equal width `m` on `D` axes, the base template contains `m^D` samples and the
all-axis extension contains `(m+1)^D`. Rectangular windows and selected extension
axes change both component width and valid origins. Dimension alone does not
specify cost. Delay, stride, actual axis lengths and extension selection all
contribute. This accounting models the local-block construction of
[Xia and Wang (2026)](https://doi.org/10.1016/j.chaos.2026.118076), with the
repository's documented geometry extensions.

## Eligible pairs differ from scheduled distance cells

The pre-exclusion unordered candidate population is `K(K-1)/2`. Tuple/coordinate
exclusion and Theiler separation reduce eligible pairs, but the current blocked
kernel computes distances before selecting eligible cells. Exclusions therefore
do not reduce the candidate-pair resource gate or automatically remove their
distance computation.

For actual block lengths `b_1,...,b_B` summing to `K`, one upper-block traversal
computes exactly

$$
\text{cells}=\frac{K^2+\sum_i b_i^2}{2},
\qquad \text{blocks}=\frac{B(B+1)}{2}.
$$

Every diagonal block is computed as a full square, including self cells and the
lower-triangle cells later masked out. HDSE/FuzzyEn traverse base and extended
components separately. Distribution entropy traverses the same width twice.
ApEn includes ordered/self comparisons and computes `K^2` cells per population
across `B^2` blocks. Each distance cell visits every template component; origin
mask construction separately visits every coordinate axis where applicable.
Chebyshev, cityblock and Euclidean kernels have the same component-visit count,
while their arithmetic and hardware costs differ.

Eligible pair counts are calculated exactly for the Cartesian origin lattice,
including coordinate exclusion and index-space Theiler bounds. The
[planning example](../examples/planning_and_counts.py) compares these counts with
real HDSE diagnostics and counts cells in a separate replay of the actual
pair-block engine. Changing block size can change scheduled cells and memory
while preserving selected pairs and numerical results.

## What the memory numbers mean

`resources` lists each guard's stage, parameter, required amount and limit.
`resource_violations` selects the exceeded guards. `guard_peak_bytes` is the
largest modeled memory guard, not a measured process resident-set size or a sum
of sequential populations. Input float64 storage is reported separately as
`8*prod(input_shape)`.

The extraction guard covers template values, origins, extraction indices,
offsets and its fixed allowance. A pair-kernel guard includes live template
values/origins, caller-retained arrays, consumer scratch and a conservative
`160*min(K,block_size)^2` allowance plus a fixed allowance. HDSE accounts for
simultaneous base/extended matrices; fuzzy kernels add shifted/scaled/centered
arrays; ApEn adds row counts. Distance-distribution planning reserves its
histogram workspace before testing extraction and kernel budgets. Ordinal and
SVD planning also model their separate working-array guards.

These quantities reproduce the estimator's controlled-array guards. Caller-owned
input, file loading, SD temporaries, Python/runtime allocations beyond allowances,
and vendor-specific FFT/SVD internals are outside their process-memory guarantee.
Use operating-system measurements when a deployment requires an RSS bound.
The numerical tests exercise each of the nine estimators with the modeled guard
budget and a budget one byte smaller, so a change in real guards can invalidate
the planning regression rather than silently changing the meaning of feasibility.

## FFT, SVD and ordinal size terms

`terms` separates `exact_scheduled_count` from `asymptotic_size_term`. The FFT term
uses all input axes in `N*sum(ceil(log2(n_j)))`. Local SVD records the dense size
term `K*k*min(K,k)`. Ordinal analysis records local ranking size
`K*k*ceil(log2(k))` and row-pattern deduplication size `K*k*ceil(log2(K))`.
The counts of supplied elements/components remain exact; these logarithmic and
dense-algebra terms are structural proxies, rather than calibrated operation
counts, FLOPs, time predictions or vendor workspace guarantees. The full FFT and
SVD routines follow the documented
[NumPy FFT](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html)
and [SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)
interfaces.

## Commands for planning and measured experiments

From the repository root, the public CLI produces strict JSON without creating
the requested input array:

```sh
uv sync --locked
uv run --locked antropy-hd plan --shape '[64,80]' --config '{"measure":"hdse","embedding":{"shape":[2,1],"delay":[2,1],"stride":[1,2],"extend_axes":[0]},"match":{"block_size":16,"theiler":1}}'
uv run --locked antropy-hd plan --shape '[128,128,128]'
uv run --locked python examples/planning_and_counts.py
```

The default `benchmark_plan.yaml` specifies bounded shape/block sweeps, seeds,
warmups, timed repetitions, geometry, matching and resource limits. Actual
`hdse` calls use a monotonic clock; every timed repetition and platform metadata
is retained. To create a separate measured receipt:

```sh
uv run --locked python scripts/benchmark_complexity.py --plan benchmark_plan.yaml --root work/benchmark-run
```

This writes `work/benchmark-run/output/study/benchmark.json` and its cost-scaling
figure. The receipt includes real input hashes, configurations, planned work,
observed counts, raw repetition times, median time, sample SD, Python/NumPy
versions and machine details. Timings depend on platform, concurrent load,
array shape and numerical libraries. They do not convert structural terms into
portable runtime promises.

`study_plan.yaml` separately specifies replicated synthetic fields, tolerance
sweeps, native/flattened analyses, fixed symbol cuts and an aggregate component-
visit budget. Each actual configured request is planned before field allocation.
An independent output directory can be produced and validated with:

```sh
mkdir -p work/study-run
cp -n study_plan.yaml work/study-run/study_plan.yaml
uv run --locked python scripts/run_study.py --plan study_plan.yaml --root work/study-run
uv run --locked python -c "from pathlib import Path; from scripts.validate_study import validate_study; print(validate_study(Path('work/study-run')))"
```

The study runner copies no acceptance state from the checked-in reports. Its
validator reads the declared root's `study_plan.yaml`; the copy command preserves
an existing plan, so choose an unused output root for a different design. The source plan,
all effective settings, statuses and generated field identities must remain
available to interpret or validate the measured outputs. See
[reproducibility](reproducibility.md) for custody and replay controls.
