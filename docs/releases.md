# Releases and verification

The [GitHub Releases page](https://github.com/docxology/antropy/releases/latest)
is the download entry point for `antropy-hd`. The distribution installs the
`antropy_hd` Python namespace and the `antropy-hd` command. This guide describes
the v0.3.0 release bundle; it makes no claim of PyPI or DOI publication.

## Version history

These versions are recorded in package metadata at the linked source commits.
They describe cumulative capabilities, not a claim that every historical version
has a published release tag. [The changelog](../CHANGELOG.md) records changes.

| Version and source | Added method families and supporting capabilities |
| --- | --- |
| [0.1.0](https://github.com/docxology/antropy/tree/a0d55df) | Native-dimensional HDSE, sample/approximate/fuzzy/distribution entropy; Shannon, Rényi, Tsallis, joint/conditional entropy, mutual information and Jensen–Shannon divergence; histogram, spatial ordinal, FFT/SVD and multiscale measures. Typed results, strict configuration, CLI and deterministic artifact production. |
| [0.2.0](https://github.com/docxology/antropy/tree/7c29f8e) | Fixed-alphabet Shannon–Jensen–Shannon statistical complexity; allocation-free template/work/memory planning; replicated native-versus-flattened studies and kernel benchmarks. Stable weighted Jensen–Shannon arithmetic and the pinned template manuscript pipeline. |
| [0.3.0](https://github.com/docxology/antropy/tree/d2483ea) | Exact/Monte Carlo permutation inference, percentile bootstrap, Wilson intervals and Holm adjustment; reusable fixed-alphabet symbolization; strict YAML examples; prospective synthetic power studies with explicit unavailable outcomes and replay validation. |

The [method guide](methods-guide.md) specifies each estimator's input population,
units and normalization. HDSE's published conventions and configured spatial
extensions are distinguished in the [implementation contract](implementation-contract.md).
Changing geometry, exclusions, cut points or units can change the quantity being
estimated; a version number does not make different configurations comparable.

## Download, verify and install

Choose v0.3.0 on the Releases page and download the named assets into one
directory:

| Asset | Purpose |
| --- | --- |
| `antropy_hd-0.3.0-py3-none-any.whl` | Installable numerical package and CLI. |
| `antropy_hd-0.3.0.tar.gz` | Built source distribution, including research sources and reproducibility inputs. |
| `antropy-methods.pdf` | This project's generated methods manuscript. The supplied published source paper is not redistributed. |
| `manifest.json` | Scientific artifact inventory for the accepted research outputs. |
| `release-identity.json` | Release commit, version, renderer pin, source equivalence and asset identities. |
| `release-verification.json` | Scoped release checks and the evidence supporting them. |
| `SHA256SUMS` | SHA-256 inventory for the release assets. |

Use the uploaded source distribution for these instructions; GitHub's automatic
“Source code” archives are separate files. From the download directory, verify
the inventory before installation:

```sh
shasum -a 256 -c SHA256SUMS
```

Every listed file must report `OK`, and the command must exit successfully.
A missing file or checksum mismatch is a failed verification. Checksums bind
downloaded bytes to the release inventory; scientific validity also requires the
method and study assumptions below. Read `release-verification.json` for the
scope of each check: historical research tests and PDF inspection authenticate
the accepted artifact bytes, while fresh release checks cover the candidate
packages and release state. Historical acceptance does not imply a new render
or a new execution of every study.

Install the wheel into a new environment with [uv](https://docs.astral.sh/uv/):

```sh
uv venv --python 3.14 .venv-antropy
uv pip install --python .venv-antropy/bin/python ./antropy_hd-0.3.0-py3-none-any.whl
uv run --no-project --python .venv-antropy/bin/python antropy-hd methods
uv run --no-project --python .venv-antropy/bin/python python -c 'import antropy_hd; print(antropy_hd.__version__)'
```

The version command should print `0.3.0`. On Windows, substitute
`.venv-antropy/Scripts/python.exe` for `.venv-antropy/bin/python`.
The numerical package needs neither manuscript tooling nor a TeX installation.

For configuration examples and research reproduction, extract the source
distribution and use its locked development environment:

```sh
tar -xzf antropy_hd-0.3.0.tar.gz
cd antropy_hd-0.3.0
uv sync --locked
uv run --locked python examples/spatial_embeddings.py --plan examples/configs/spatial.yaml
uv run --locked python examples/fixed_alphabet.py --plan examples/configs/alphabet.yaml
uv run --locked python examples/planning_and_counts.py --plan examples/configs/planning.yaml
uv run --locked python examples/replicate_inference.py --plan examples/configs/inference.yaml
```

The [example guide](../examples/README.md) explains the emitted JSON and each
plan's controls. [Configuration and API documentation](configuration.md) covers
the strict numerical boundary. Use the checked-in plans as the source of seeds,
budgets and design parameters instead of copying manuscript settings by hand.

## Interpret results and reproduce the manuscript

Finite estimates carry a finite value. Infinite and undefined entropy estimates
carry a JSON `null` with a distinct status and diagnostics. For HDSE, no base
matches is undefined; positive base matches with no extended matches is infinite.
Neither case means zero entropy. Preserve those outcomes and denominators when
summarizing results; see [result-state interpretation](methods-guide.md#multiscale-boundaries-and-result-states).

Inference operates on declared whole-observation replicate values. Independent
permutation tests require exchangeable labels under the null; paired tests require
exchangeability within independent pairs. Overlapping templates are not independent
replicates. Bootstrap, Wilson and Holm assumptions and limitations are specified
in the [inference contract](inference.md). The [power protocol](power-design.md)
distinguishes conditional rejection, unconditional rejection and unavailable
decisions. Synthetic power curves do not certify biological sample sizes or
transfer the source paper's scientific conclusions to new data.

Follow the [README reproduction commands](../README.md#reproduce-the-research-artifacts)
in order. The manuscript uses the actual
[docxology/template](https://github.com/docxology/template) provider, pinned in
[`uv.lock`](../uv.lock), with its source identity verified against installed
package metadata and RECORD hashes. Pandoc, pandoc-crossref, BibTeX and XeLaTeX
are required for rendering. The [adaptation record](template-adaptation.md)
documents attribution, the source revision and the boundary between scaffold
reuse and this project's evidence.

The [publication profile](manuscript/project.yaml) and consumed plans supply
rendering controls and sourced variables. Missing producer inputs, unresolved
variables and invalid references fail rendering. The
[provenance manifest](../output/provenance/manifest.json) binds artifacts by
SHA-256; its own identity must be recorded externally by a reviewed commit or
release. [Reproducibility and acceptance](reproducibility.md) describes exact
custody checks, bounded finite synthetic replay, numerical replay and corrupted
input controls. PDF layout inspection remains a separate acceptance step.
