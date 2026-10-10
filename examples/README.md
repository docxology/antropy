# Runnable examples

Run these commands from the repository root. Each script emits one strict JSON
object on stdout and records the installed package version, seed, configuration
and computed results. Undefined/infinite estimates retain their status and a
null value. Synthetic inputs illustrate API behavior; they establish no biological
finding, classification accuracy or reproduction of a published experiment.

| Script | What it demonstrates |
|---|---|
| `spatial_embeddings.py` | Native 2D and 3D rectangular windows, per-axis delay/stride, selected extension axes, tuple/coordinate exclusions, and different valid-origin populations across measures. |
| `fixed_alphabet.py` | Fixed amplitude cuts, explicit lower/upper tail categories, retained zero counts, Shannon entropy, Jensen–Shannon divergence and normalized statistical complexity. |
| `planning_and_counts.py` | Allocation-free planning, real blocked-kernel replay, observed HDSE counts, a real one-byte-below-memory-guard failure, and an infeasible large shape evaluated without allocating its array. |
| `replicate_inference.py` | Actual permutation allocation counts, paired bootstrap effect intervals, Wilson intervals, and fixed-family Holm adjustment. |

For the checked-in dependency lock and project environment:

```sh
uv sync --locked
uv run --locked python examples/spatial_embeddings.py
uv run --locked python examples/fixed_alphabet.py
uv run --locked python examples/planning_and_counts.py
uv run --locked python examples/replicate_inference.py
uv run --locked python examples/spatial_embeddings.py --plan examples/configs/spatial.yaml
```

Each file also has PEP 723 metadata and an editable source pointing to this
checkout. Standalone script execution resolves its declared runtime dependencies:

```sh
uv run --script examples/spatial_embeddings.py
uv run --script examples/fixed_alphabet.py
uv run --script examples/planning_and_counts.py
uv run --script examples/replicate_inference.py
```

Standalone resolution uses the script metadata rather than the project lock.
Use the project commands above when reproducing the repository environment.
uv describes these execution modes in its [script documentation](https://docs.astral.sh/uv/guides/scripts/).

The entry points only read strict YAML, dispatch shared typed helpers and emit
JSON. Numerical controls live in `configs/{spatial,alphabet,planning,inference}.yaml`;
every plan field is consumed. Unknown or duplicate keys fail, and each wrapper
accepts `--plan` to select another design. Report schemas and original default
numerical outputs remain unchanged; the inference example has its own report.

The fixed alphabet contains one category below the first cut, bounded intervals
between cuts, and one category at or above the final cut. The configured tie
direction determines which category receives an observation exactly on a cut.
The cut locations stay fixed, all configured counts remain present, and every finite
observation contributes. Empty categories are never removed or used to redefine
the uniform reference. This is an amplitude-symbol example; temporal or spatial
causality is not inferred from that alphabet.

In the planning example, `replayed_distance_cells` is counted by replaying the
actual pair-block engine on extracted templates. `planned_distance_cells` comes
from integer combinatorics. `observed_hdse.diagnostics` comes from the estimator.
These are separate computations. A changed block size can change scheduled work
and guarded memory while preserving the selected pair population and entropy.
The negative budget control retains its actual `ResourceError` fields in JSON;
an unexpected successful calculation raises an error instead of printing a
copied success flag.

The inference example records the complete paired permutation and bootstrap
configuration and actual effect (second minus first). Its binomial counts and
additional p-values are explicit demonstration inputs, not empirical findings.
Small exact tests can have coarse resolution; inspect allocation counts and
inclusive-tail p-values instead of assuming the example must reject. Independent
whole-field power experiments are orchestrated separately through
`scripts/run_power.py` and `power_plan.yaml`.

See the [methods guide](../docs/methods-guide.md) for interpretation and the
[complexity guide](../docs/computational-complexity.md) for planning formulas and
measured benchmark commands. Source checks can include the examples directly:

```sh
uv run --locked ruff check examples
uv run --locked basedpyright examples
```
