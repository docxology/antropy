# antropy

**antropy** (entropy + ant) is a dimension-agnostic complexity methods project.
The distribution is `antropy-hd` and the Python import is `antropy_hd`, avoiding a
namespace collision with the separate AntroPy time-series project.

The project implements high-dimensional sample entropy (HDSE), related local
template measures, probability information measures, spatial ordinal measures,
and FFT/SVD entropy through a shared typed result and an explicit configuration
boundary. HDSE follows the algorithm of Xia and Wang (2026); scientific
conventions, ambiguity, extensions, and limitations are documented in
[the implementation contract](docs/implementation-contract.md).

## Install and run

CPython 3.14 and [uv](https://docs.astral.sh/uv/) are required for development.

```bash
uv sync --frozen
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

## Reproduce the research artifacts

```bash
uv run python scripts/run_experiments.py --plan experiment_plan.yaml
uv run python scripts/build_manuscript.py
uv run python scripts/validate_artifacts.py
```

The seeded experiments compare specified synthetic periodic, independent-noise,
and mixed fields across dimensions and tolerances. These are implementation
demonstrations, not a reproduction of the paper's experiments or classification
results. Generated inputs, CSV/JSON results, figures, inspectable Markdown source,
and the manuscript PDF are bound by SHA-256 in `output/provenance/manifest.json`.
Validation fails when required artifacts are missing, changed, or inconsistent.

## Verification

```bash
uv run ruff check .
uv run basedpyright
uv run pytest --cov=src/antropy_hd --cov-branch --cov-report=term-missing
uv build
```

Tests use real arrays, files and subprocesses, including deliberate invalid input
and corrupted artifact controls. Template and pair workspace budgets bound the
controlled numerical work; caller inputs, file parsing, standard-deviation
temporaries and process RSS are outside that budget.
The numerical library does not depend on plotting, manuscript tooling or network
services. CI installs the built wheel in an isolated environment and runs its CLI.

## Scientific and project documentation

- [Method conventions](docs/implementation-contract.md) and [related primary sources](docs/sources-related.md)
- [Configuration and API](docs/configuration.md)
- [Reproducibility and artifact provenance](docs/reproducibility.md)
- [Manuscript source](docs/manuscript/manuscript.md)
- [Template adaptation](docs/template-adaptation.md)
- [Contribution guidance](CONTRIBUTING.md) and [security reporting](SECURITY.md)

Adapted from [docxology/template_code_project](https://github.com/docxology/template_code_project)
at commit `04040a1e8eda0b31ce61db888cd1b3598f1696ca`. Its source/test/script/data/
manuscript/output separation is retained while the template's demonstration domain
and monorepo publishing infrastructure are replaced by this standalone methods
package. The supplied published PDF is not redistributed. License: MIT.
