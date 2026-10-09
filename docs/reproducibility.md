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
