# antropy

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23306201.svg)](https://doi.org/10.5281/zenodo.23306201)
[![Main verification](https://github.com/docxology/antropy/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/docxology/antropy/actions/workflows/verify.yml)

**antropy** (entropy + ant) is a dimension-agnostic complexity methods project.
The distribution is `antropy-hd` and the Python import is `antropy_hd`, avoiding a
namespace collision with the separate AntroPy time-series project.

[Latest release: v0.3.1](https://github.com/docxology/antropy/releases/tag/v0.3.1)
collects the numerical wheel, source distribution, exact-commit source archive,
methods manuscript and verification receipts. Read the [manuscript PDF](antropy-methods.pdf),
follow the [release installation guide](docs/releases.md#download-verify-and-install),
or start with the [source quickstart](docs/getting-started.md).
The [documentation index](docs/README.md) gives a reading order; the
[changelog](CHANGELOG.md) records versioned changes. The v0.3.1 archive uses
[DOI 10.5281/zenodo.23306201](https://doi.org/10.5281/zenodo.23306201); see the
[release entry](docs/releases.md#v031) for publication and verification scope.

The project implements high-dimensional sample entropy (HDSE), related local
template measures, probability information measures, spatial ordinal measures,
and FFT/SVD entropy through a shared typed result and an explicit configuration
boundary. HDSE follows the algorithm of Xia and Wang (2026); scientific
conventions, ambiguity, extensions, and limitations are documented in
[the implementation contract](docs/implementation-contract.md).

The framework also provides fixed-alphabet Shannon-Jensen-Shannon statistical
complexity and an allocation-free planner for template populations, exact scheduled
distance work and conservative workspace guards. Native geometry, distributional
uncertainty, algorithm cost and numerical degeneracy are separate reported quantities.

Whole-observation inference includes exact and Monte Carlo permutation tests,
paired or independent percentile bootstrap intervals, Wilson score intervals and
fixed-family Holm adjustment. [The inference contracts](docs/inference.md) state
exchangeability assumptions, inclusive tails, finite-sample resolution, seed and
work limits. `fixed_alphabet` retains declared empty categories and both tails.

## Choose an analysis

The v0.3.1 registry contains 19 estimators. Input interpretation and geometry
determine what each estimate means; see the [method guide](docs/methods-guide.md)
for populations, units and normalization.

| Family | Registered estimators | Start here |
| --- | --- | --- |
| Local template matching | `hdse`, `sample_entropy`, `approximate_entropy`, `fuzzy_entropy`, `distribution_entropy` | [Geometry and HDSE](docs/methods-guide.md#spatial-geometry-and-hdse) |
| Probability and dependence | `shannon_entropy`, `renyi_entropy`, `tsallis_entropy`, `joint_entropy`, `conditional_entropy`, `mutual_information`, `jensen_shannon_divergence` | [Probability conventions](docs/methods-guide.md#probability-measures-and-fixed-alphabets) |
| Amplitude distributions and complexity | `histogram_entropy`, `statistical_complexity` | [Fixed alphabets](examples/README.md) |
| Local ordinal structure | `permutation_entropy`, `weighted_permutation_entropy` | [Estimator populations](docs/methods-guide.md#estimator-families) |
| Transform distributions | `spectral_entropy`, `svd_entropy` | [FFT and SVD conventions](docs/methods-guide.md#estimator-families) |
| Scale dependence | `multiscale_entropy` | [Multiscale boundaries](docs/methods-guide.md#multiscale-boundaries-and-result-states) |

Symbolization, resource planning and replicate inference are additional APIs.
Use `uv run --locked antropy-hd methods` to inspect the installed registry and
[configuration and API](docs/configuration.md) to construct validated requests.
HDSE retains native geometry; `sample_entropy` uses its documented 1D population.

## Install and run

The package requires Python 3.14 or newer. For release installation, use the
[downloaded-wheel instructions](docs/releases.md#download-verify-and-install).
Development uses CPython 3.14 and [uv](https://docs.astral.sh/uv/); run the following
from a source checkout:

```bash
uv sync --locked
uv run antropy-hd methods
uv run antropy-hd analyze data/demo-grid.csv --measure hdse \
  --parameters '{"embedding":{"shape":2},"match":{"tolerance":0.5}}'
uv run antropy-hd batch data/demo-grid.csv --config data/example-batch.json \
  --output output/reports/demo.json
```

NPY accepts finite numeric arrays of any positive dimension and disables pickle.
CSV represents a comma-separated two-dimensional grid with no header. Probability
methods require normalized probability arrays, and joint methods require joint
probability tables; choosing a method never silently converts amplitudes into
probabilities. Histogram entropy performs the explicitly configured discretization.
Unknown fields and method parameters fail; existing outputs require `--overwrite`.

```python
import numpy as np
from antropy_hd import EmbeddingConfig, MatchConfig, hdse

field = np.random.default_rng(17).normal(size=(12, 12))
result = hdse(field, embedding=EmbeddingConfig(shape=2), match=MatchConfig(tolerance=0.5))
print(result.model_dump_json())
```

Every measure returns `EntropyResult`. Finite estimates contain a finite value;
infinite and undefined estimates contain `null` plus an explicit status and
diagnostics. They remain distinguishable in strict JSON and analysis tables.

Inspect a request before allocating a data array:

```bash
uv run antropy-hd plan --shape '[64,80]' \
  --config '{"measure":"hdse","embedding":{"shape":[2,3],"stride":[2,2]},"match":{"block_size":32}}'
uv run python examples/spatial_embeddings.py
uv run python examples/fixed_alphabet.py
uv run python examples/planning_and_counts.py
uv run python examples/replicate_inference.py
```

The planner reports feasibility and violations rather than inventing runtime or
whole-process memory predictions. See the [runnable examples](examples/README.md)
for anisotropic geometry, exclusion sensitivity and fixed alphabet conventions.

For custom designs, select a checked-in plan explicitly:

```bash
uv run --locked python examples/spatial_embeddings.py --plan examples/configs/spatial.yaml
uv run --locked python examples/fixed_alphabet.py --plan examples/configs/alphabet.yaml
uv run --locked python examples/planning_and_counts.py --plan examples/configs/planning.yaml
uv run --locked python examples/replicate_inference.py --plan examples/configs/inference.yaml
```

The [quickstart](docs/getting-started.md) covers input files, safe output handling,
result interpretation and the next steps for each workflow.

## Inspect the example outputs

![Native HDSE and row-major flattened sample entropy across paired synthetic replacement fields](output/study/figures/native-v-flattened.png)

Native and row-major flattened analyses change template widths and origin
populations. Interpret this comparison with the [paired study design](docs/study-design.md)
and its [consumed plan](study_plan.yaml); the panels do not establish an ordering
of biological complexity across dimensions.

The [prospective rejection-rate figure](output/power/figures/rejection-rates.png)
and [availability/calibration figure](output/power/figures/availability-calibration.png)
show the configured whole-field operating characteristics. Read them with the
[power protocol](docs/power-design.md), including unavailable decisions,
pointwise uncertainty and dependence across sample-size prefixes.

## Reproduce the research artifacts

```bash
uv run python scripts/run_experiments.py --plan experiment_plan.yaml
uv run python scripts/run_study.py --plan study_plan.yaml
uv run python scripts/benchmark_complexity.py --plan benchmark_plan.yaml
uv run python scripts/run_power.py --plan power_plan.yaml
uv run python scripts/build_manuscript.py
uv run python scripts/validate_artifacts.py
```

The separate replicated study implements the paper's Bernoulli-replacement MIX
law on explicitly bounded fields, alongside constant, alternating, Gaussian,
smoothed and histogram-preserving shuffled controls. Common random numbers pair
mixing probabilities within trials. Summaries preserve every nonfinite outcome;
error bars represent trial variability. Native and flattened estimators retain
their different feature counts and origin populations. See the
[complete design and limitations](docs/study-design.md).

A separate [prospective power study](docs/power-design.md) compares independent
whole fields under stochastic same-distribution null controls and prespecified
replacement contrasts. It reports rejection conditional on availability,
unconditional rejection, failure rates, pointwise Monte Carlo uncertainty and
the exact/Monte Carlo inference schedules. Missing estimates remain explicit;
the analysis family and sample-size grid come from `power_plan.yaml`. Smaller
sample sizes reuse pool prefixes, so curve points are dependent. These curves
describe the declared synthetic design and do not certify biological sample sizes.

The example entry points read strict YAML plans in `examples/configs/` and call
shared numerical helpers. Their data-generation controls, geometry, thresholds,
resampling, and budgets are configurable; use `--plan` for a different design.

Manuscript building uses the actual **docxology/template** package, pinned by Git
revision in `uv.lock`, with Pandoc, pandoc-crossref, BibTeX and XeLaTeX. Install
those system tools before rendering. The numerical library and examples do not
require them. The workflow records the installed provider identity and verifies
its source against its package RECORD. There is no custom PDF fallback.

[The publication profile](docs/manuscript/project.yaml) configures metadata,
ordered sections, figures, typography and producer requirements. All displayed
measurements, counts, settings and tables derive from authenticated artifacts.
Unresolved variables, missing sections, references, glyphs or producer inputs are
fatal. The output includes native equations, bibliography, section bookmarks,
and a real table of contents, plus resolved Markdown, TeX and compiler receipts.

Read the [repository manuscript](antropy-methods.pdf) or the
[version-specific PDF](https://github.com/docxology/antropy/releases/download/v0.3.1/antropy-methods.pdf)
alongside its [scientific manifest](output/provenance/manifest.json) and
[renderer identity receipt](output/provenance/manuscript-template.json).
The release guide distinguishes retained scientific producer snapshots, refreshed
rendering, package checks and hosted CI; current `main` documentation may contain
later updates.

Generated arrays, CSV/JSON results, figures, variables, manuscript source and PDF
are SHA-256 bound in `output/provenance/manifest.json`. Validation also reruns the
actual study and benchmark kernels. These are methods demonstrations and a bounded
generator adaptation; the paper's full empirical and classification results are
not claimed as replicated.

## Verification

Verify downloaded release files against their accompanying checksums using the
[release guide](docs/releases.md#download-verify-and-install). In a source checkout,
run the development checks below; the [reproducibility contract](docs/reproducibility.md)
describes numerical replay, artifact custody and separate rendered-PDF inspection.

```bash
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
uv run pytest --cov=src/antropy_hd --cov-branch --cov-report=term-missing
uv build
uv run python scripts/check_installed_wheel.py
```

Tests use real arrays, files and subprocesses, including deliberate invalid input
and corrupted artifact controls. Template and pair workspace budgets bound the
controlled numerical work; caller inputs, file parsing, standard-deviation
temporaries and process RSS are outside that budget.
The numerical library does not depend on plotting, manuscript tooling or network
services. CI installs the built wheel in an isolated environment and runs its CLI.

## Scientific and project documentation

- [Documentation index](docs/README.md) and [source quickstart](docs/getting-started.md)
- [Method conventions](docs/implementation-contract.md) and [related primary sources](docs/sources-related.md)
- [Configuration and API](docs/configuration.md)
- [Method guide and interpretation](docs/methods-guide.md)
- [Release history, downloads and verification](docs/releases.md)
- [Replicate inference and assumptions](docs/inference.md)
- [Prospective power study](docs/power-design.md)
- [Computational work and memory](docs/computational-complexity.md)
- [Replicated study protocol](docs/study-design.md)
- [Reproducibility and artifact provenance](docs/reproducibility.md)
- [Manuscript source](docs/manuscript/manuscript.md)
- [Template adaptation](docs/template-adaptation.md)
- [Contribution guidance](CONTRIBUTING.md) and [security reporting](SECURITY.md)

The initial scaffold adapted [template_code_project](https://github.com/docxology/template_code_project).
The publication pipeline now consumes [docxology/template](https://github.com/docxology/template)
directly while preserving the standalone numerical package. Attribution and
exact revision records are in [the adaptation record](docs/template-adaptation.md).
The supplied published paper PDF is not redistributed. License: MIT.
