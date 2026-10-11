# Documentation

antropy provides native-dimensional entropy and complexity methods, explicit
result states, computational planning and replicate inference. The distribution
is `antropy-hd`; import it as `antropy_hd`. Return to the
[project overview](../README.md) for the scope and development checks.

These pages follow the current `main` branch. For the frozen v0.3.0 bundle, use
the [tagged documentation](https://github.com/docxology/antropy/tree/v0.3.0/docs)
and [v0.3.0 downloads](https://github.com/docxology/antropy/releases/tag/v0.3.0).
Documentation updates on `main` do not regenerate or replace those release assets.

## Start here

1. [Getting started](getting-started.md): install a source checkout, analyze the
   existing demo, inspect a plan and run the four strict YAML examples.
2. [Methods guide](methods-guide.md): choose a measure by input meaning,
   geometry, units and interpretation; preserve undefined and infinite outcomes.
3. [Configuration and API](configuration.md): configure embeddings and matches,
   understand CSV/NPY input and read the result/provenance fields.
4. [Computational work and memory](computational-complexity.md): inspect exact
   scheduled work, feasibility and the limits of the workspace guard.

## Choose the next task

| Task | Guide |
| --- | --- |
| Understand HDSE conventions, exclusions and extensions | [Implementation contract](implementation-contract.md) and [primary sources](sources-related.md) |
| Explore spatial geometry, fixed alphabets, planning or replicate inference | [Runnable examples and YAML controls](../examples/README.md) |
| Compare declared independent or paired observations | [Inference assumptions and contracts](inference.md) |
| Understand the synthetic prospective power design | [Power protocol](power-design.md) |
| Inspect field generation, pairing and native-versus-flattened comparisons | [Replicated study design](study-design.md) |
| Reproduce research outputs and check their provenance | [Reproduction commands](../README.md#reproduce-the-research-artifacts) and [acceptance contract](reproducibility.md) |
| Download and verify a released package | [Release installation and verification](releases.md) and [changelog](../CHANGELOG.md) |
| Change code or report a vulnerability | [Contributing](../CONTRIBUTING.md) and [security reporting](../SECURITY.md) |

## Read the manuscript

The [v0.3.0 methods PDF](https://github.com/docxology/antropy/releases/download/v0.3.0/antropy-methods.pdf)
is this project's generated manuscript. Verify downloaded release assets with
the accompanying [SHA256SUMS](https://github.com/docxology/antropy/releases/download/v0.3.0/SHA256SUMS)
as described in the [release guide](releases.md#download-verify-and-install).
The supplied published source paper is not redistributed.

The checkout contains the [manuscript source](manuscript/manuscript.md),
[publication profile](manuscript/project.yaml) and
[template adaptation record](template-adaptation.md). Numerical examples and
synthetic studies demonstrate the declared methods; they do not establish
biological findings or application-specific sample sizes. Research replay and
rendered PDF inspection have separate acceptance requirements in the
[reproducibility guide](reproducibility.md).
