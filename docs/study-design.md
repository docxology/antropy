# Replicated synthetic study protocol

The consumed controls are in [study_plan.yaml](../study_plan.yaml). Results,
stored arrays, complete configurations, diagnostics and aggregates are under
`output/study/`. This is a bounded adaptation of the MIX construction in
[Xia and Wang (2026)](https://doi.org/10.1016/j.chaos.2026.118076), together with
explicit controls. It does not reproduce their full experimental grids,
classification results, noise-color nomenclature or unspecified fBm generator.

## Fields and pairing

For zero-based array coordinates u, the periodic field is
`s(u) = sum_j sin(2*pi*(u_j + phase_origin)/period)`. The configured phase origin
selects the tensor-index convention; one follows the paper's usual one-based
indexing, and zero is a declared phase adaptation. There is no division by
`sqrt(d)` in this study. The earlier baseline remains a separate experiment with
its original additive-mixture and amplitude-normalization conventions.

MIX uses `x_p = where(U < p, Y, s)`, with independently drawn per-cell
`U ~ Uniform[0,1)` and `Y ~ Uniform[-sqrt(3),sqrt(3)]`. Within one shape and trial,
the same U and Y are reused across all probabilities. Replacement masks are
nested in p. These common random numbers support paired comparisons; conditions
within a trial are not independent experiments. Different trials have distinct
seed namespaces. The periodic endpoint is deterministic across trials.

The RNG receives a SeedSequence containing the plan seed, a fixed generator
identifier, all shape axes and the trial identifier. List position is not part
of the seed. Adding or reordering configured conditions does not change existing
fields. The complete case matrix is derived independently by the validator.

Controls have explicit meanings:

- Constant: all-zero field. Strict HDSE with zero SD is undefined, whereas its
  fixed-alphabet Shannon entropy and statistical complexity are zero.
- Checkerboard: `2*(sum_j u_j mod 2)-1`, giving a regular alternating field.
- Gaussian: independent zero-mean normal draws with the configured SD.
- Correlated: Gaussian draws in a separate seed namespace, repeatedly averaged
  with the center and both immediate neighbors on every axis. Each step divides
  by `1+2*d`; `roll` supplies periodic boundaries. There is no hidden variance
  renormalization. This is a smoothing control, not an asserted fBm or noise-color
  reproduction.
- Shuffled: a seeded global permutation of the periodic field, reshaped in C
  order. It preserves the amplitude multiset and any fixed-cut histogram while
  changing spatial neighborhoods.

## Input meaning and estimator populations

Native HDSE, distribution entropy, permutation entropy and spectral entropy
receive the native tensor. SampEn receives an explicitly C-order flattened
version of the same field. Their feature counts, origin populations and extension
geometry differ. Their contrast is a geometry demonstration and cannot establish
the effect of flattening with every other estimator property held fixed.

The Shannon/complexity analysis uses shared fixed amplitude cuts. The cuts span
the configured finite range. The two tails are categories, so observations beyond
that range are retained. Empty categories remain in the full declared alphabet;
the uniform reference and normalization are never rebuilt from occupied bins.
The entropy-complexity plane is distributional and is not a causal ordinal plane.

## Variation and undefined estimates

Every row retains its trial, geometry, full parameters, diagnostics and explicit
finite/undefined/infinite state. Summaries report total and all three outcome
counts. Means condition on finite results; sample SD is null with fewer than two
finite trials. Plots leave missing means as gaps and mark singleton means without
invented zero error bars. Error bars are trial sample SD, not confidence intervals
from overlapping template pairs. No universal monotonicity or classification
claim is imposed on the measured results.

## Resource and acceptance controls

Preflight checks every native and flattened invocation before creating outputs.
The plan bounds input cells, fields, templates, candidate pairs, controlled array
workspace and scheduled distance-component evaluations. Radius choices can change
matches without changing the distance work performed by this implementation.
The guards are distinct from whole-process resident memory.

Validation authenticates input files, seeded design replay, transformed input and
configuration identities, every declared case/method/radius, exact CSV bindings,
complete aggregates and cost plans. It also reruns the actual kernels on stored
inputs. Status, parameters, counts and identities remain exact. Floating numerical
replay uses an explicit absolute envelope of
`64*float64_epsilon*max(1,abs(reference))` for real-valued outputs and diagnostics;
this is a portability acceptance policy, not a universal numerical-error theorem.
Raw table/report custody remains exact. Negative controls reject coherently
altered estimates, missing or duplicate trials, false Boolean counts, duplicate
CSV columns, changed aggregates and fabricated cost plans.

## Timings

[benchmark_plan.yaml](../benchmark_plan.yaml) independently configures shapes,
block sizes, warmup, repetitions and limits. Actual Gaussian input arrays are
stored, each timed HDSE call uses a monotonic nanosecond clock, and all positive
durations are retained. Medians and sample SD are recomputed from those durations.
Source, input, configuration and exact work counts are authenticated. Timings
describe the recorded machine and execution; they are not portable predictions
or an empirical proof of an asymptotic theorem.
