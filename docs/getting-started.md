# Getting started from source

This guide follows the current `main` checkout. For the frozen v0.3.0 wheel,
source distribution and manuscript, use the
[v0.3.0 release](https://github.com/docxology/antropy/releases/tag/v0.3.0) and
[download verification instructions](releases.md#download-verify-and-install).
Current documentation changes do not replace that archive.

## Install the locked environment

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git,
then clone into a new directory:

```sh
git clone https://github.com/docxology/antropy.git
cd antropy
uv sync --locked --python 3.14
uv run --locked python --version
uv run --locked antropy-hd version
uv run --locked antropy-hd methods
```

Use CPython 3.14 for the project environment. `uv sync` installs the checkout and
its locked development dependencies; the distribution is `antropy-hd` and the
Python import is `antropy_hd`. The methods command emits JSON listing method
names and whether each expects observations or probabilities. Numerical analysis
and the examples below need no TeX installation. Manuscript rendering has
[additional system requirements](releases.md#interpret-results-and-reproduce-the-manuscript).

Run all remaining commands from the repository root.

## Analyze the existing demo

The checked-in [demo grid](../data/demo-grid.csv) is a synthetic amplitude field;
see [data notes](../data/README.md). These commands read existing inputs and emit
strict JSON on stdout:

```sh
uv run --locked antropy-hd analyze data/demo-grid.csv --measure hdse \
  --parameters '{"embedding":{"shape":2},"match":{"tolerance":0.5}}'
uv run --locked antropy-hd batch data/demo-grid.csv --config data/example-batch.json
```

The [batch configuration](../data/example-batch.json) runs HDSE, spatial ordinal
and spectral analysis. To save a separate result, choose a new path:

```sh
uv run --locked antropy-hd batch data/demo-grid.csv --config data/example-batch.json \
  --output work/quickstart/demo.json
```

An existing output causes an error. `--overwrite` explicitly permits replacement;
the default does not replace it. Keep exploratory results under a separate path
such as `work/quickstart/` so the accepted research outputs retain their identity.

CSV means a headerless, comma-separated two-dimensional numeric grid, including
one-row or one-column files. NPY preserves dimension and loads with pickle
disabled; use a vector NPY for a one-dimensional signal. The source checkout
also includes an existing synthetic NPY signal that can be read directly:

```sh
uv run --locked antropy-hd analyze output/data/periodic-64.npy --measure spectral_entropy
```

Scalar, empty, boolean, string, object, complex and nonfinite inputs are rejected.
Probability methods require normalized probability arrays; selecting one does
not turn amplitudes into probabilities. See [configuration and input rules](configuration.md).

## Read the result state

Analysis and batch JSON contain `results`, keyed by analysis ID, along with input
shape, package version, consumed configuration and hashes. Read each result's
`status` before using `value`:

| Status | Value | Interpretation |
| --- | --- | --- |
| `finite` | Finite number | Interpret with the method's units, parameters and diagnostics. |
| `undefined` | `null` | The estimate is unavailable under the recorded conditions; for HDSE, no base matches is one cause. |
| `infinite` | `null` | A distinct infinite estimate; for HDSE, positive base matches and no extended matches. |

Preserve statuses and counts when summarizing; a `null` is not zero entropy.
The [methods guide](methods-guide.md#multiscale-boundaries-and-result-states)
explains degeneracy, units and multiscale boundaries.

## Plan work before computation

This command takes only a shape and configuration. It does not load or allocate
the requested data array, run an entropy estimate or write an output file:

```sh
uv run --locked antropy-hd plan --shape '[64,80]' \
  --config '{"measure":"hdse","embedding":{"shape":[2,3],"stride":[2,2]},"match":{"block_size":32}}'
```

Inspect `feasible` and the `resources` entries in the returned JSON; each entry
records its `parameter`, `stage`, `required` amount and `limit`. A well-formed request
that exceeds a resource limit still exits successfully while reporting
`feasible: false`; that does not authorize running an infeasible calculation.
Scheduled work and guarded template/pair workspace are not runtime predictions
or whole-process memory bounds. See [work and memory planning](computational-complexity.md).

## Run the four configurable examples

Each command consumes its existing strict YAML plan and emits one JSON object:

```sh
uv run --locked python examples/spatial_embeddings.py --plan examples/configs/spatial.yaml
uv run --locked python examples/fixed_alphabet.py --plan examples/configs/alphabet.yaml
uv run --locked python examples/planning_and_counts.py --plan examples/configs/planning.yaml
uv run --locked python examples/replicate_inference.py --plan examples/configs/inference.yaml
```

| Plan | Inspect in the example |
| --- | --- |
| [spatial.yaml](../examples/configs/spatial.yaml) | Native 2D/3D windows, per-axis geometry, extension axes and exclusions. |
| [alphabet.yaml](../examples/configs/alphabet.yaml) | Fixed amplitude cuts, both tail categories, retained empty categories and statistical complexity. |
| [planning.yaml](../examples/configs/planning.yaml) | Planned versus replayed distance work, observed counts and an actual memory-budget rejection. |
| [inference.yaml](../examples/configs/inference.yaml) | Paired permutation and bootstrap, allocation counts, Wilson intervals and Holm adjustment. |

Seeds, geometry, field generation, thresholds, inference controls and budgets live
in those plans. Unknown or duplicate YAML keys fail; use `--plan` to select a
separate design rather than adding constants to the entry points. The
[example guide](../examples/README.md) explains outputs and standalone script
execution. These are synthetic demonstrations, not empirical findings.

## Continue by task

Use the [methods guide](methods-guide.md) and [implementation contract](implementation-contract.md)
to choose a measure and its conventions. Read the [inference contract](inference.md)
before comparing replicates: overlapping templates are not independent subjects.
The [power protocol](power-design.md) describes prospective synthetic operating
characteristics and unavailable decisions. For full research reproduction, follow
the [study design](study-design.md), [reproduction commands](../README.md#reproduce-the-research-artifacts)
and [acceptance requirements](reproducibility.md).

Return to the [documentation index](README.md) for release, manuscript and
contribution links.
