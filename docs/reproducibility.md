# Reproducibility and acceptance

`experiment_plan.yaml` specifies the seed, input shapes, structures, tolerances,
local embedding shape, signal period, mixture amplitude, histogram bins and
resource budgets. The validated plan rejects extra fields, duplicate designs,
infeasible shapes and nonfinite parameters. Each generated field uses a
SeedSequence derived from the plan seed, shape and structure position; tolerance
sweeps reuse the same field. Every plan field contributes to execution or a
resource bound.

Run the three commands in the README in order. Missing results prevent manuscript
generation; missing or changed artifacts prevent acceptance. The manuscript
source is generated from the actual CSV, and the PDF is rendered from that
inspectable Markdown. The SHA-256 inventory includes source/configuration inputs,
generated NPY arrays, JSON batches, CSV rows, the figure, source manuscript and PDF.
The manifest is written last. It does not authenticate itself; a reviewed commit
or release records the manifest's identity externally.

The validator independently checks the required artifact floor, nonempty files,
relative path confinement, byte counts and hashes, input-file and canonical-array
hashes, consumed configuration hashes, exact batch/CSV analysis coverage, estimate
values and statuses, effective parameter/diagnostic details, CSV binding in the
manuscript, PNG geometry and PDF text/provenance. Adversarial tests remove files,
change results and weaken manifests to confirm rejection. Hash consistency is a
custody control; numerical oracle tests provide separate algorithm evidence.

Synthetic design replay uses a separate, bounded floating-point equivalence rule.
The stored NPY shape must match exactly, and both stored and replayed arrays must
contain only finite values before any tolerance comparison. A finite plan can
still overflow during synthesis; that replay fails closed. For each stored value x and replayed
reference y in a d-dimensional field, the replay comparison accepts only
`abs(x-y) <= 2*gamma_k*max(1,abs(y))`, where `epsilon = 2^-52`,
`k = 16 + 8*d`, and `gamma_k = k*epsilon/(1-k*epsilon)`. Relative tolerance is
zero; the displayed expression is the complete per-element absolute envelope.
The factor two budgets two platform implementations, the dimension term budgets
axiswise phase/trigonometric/sum work, and the fixed term conservatively budgets
scaling, Gaussian transformation and mixture operations. The unit-scale floor
allows cancellation near zero. This is an explicit float64 replay acceptance
policy, not a universal proof of every platform's transcendental-library error.
Differences outside the envelope fail closed, including genuinely reseeded data
with coherently recomputed provenance. Extreme numerical designs whose replay
error exceeds this budget require investigation rather than a larger hidden
tolerance.

This equivalence applies only when checking a synthetic field against the live
plan's regenerated reference. SHA-256 and byte counts for manifest files, the
actual NPY file hash, canonical stored-array identity, configuration hashes, CSV
values/statuses and report/manuscript bindings remain exact. A one-ULP alteration
without re-authenticated file and report hashes still fails. Accepted replay
roundoff does not change stored arrays or estimates, smooth entropy thresholds,
or imply that regenerated entropy estimates are bit-identical across platforms.

The initial hosted run
[37978727833](https://github.com/docxology/antropy/actions/runs/37978727833)
passed its numerical/tooling gates but failed the former bit-identical synthetic
replay check on Linux. That failure remains part of the project record. Regression
controls reproduce it with a one-ULP real NPY difference, require strict custody
checks to pass after legitimate recomputation, and reject the first binary64 step
outside an independently derived exact-rational envelope.

Synthetic fields are implementation demonstrations. No experiment in the source
paper, biological finding, classification accuracy or application-specific
validation is claimed. Undefined and infinite estimates are preserved in CSV,
JSON, tables and figure annotations. The published source PDF is never an artifact
input or output in this repository.

Development checks run with the frozen uv lock. Source branch-inclusive coverage
must exceed 90 percent; research infrastructure coverage must exceed 60 percent.
The installed-wheel check creates a real isolated environment, installs the wheel
and executes CLI analysis from a temporary directory outside the checkout.
Rendering inspection is a separate visual acceptance step: text extraction and
file hashes alone cannot prove page layout. Independent review is required before
the initial public push.
