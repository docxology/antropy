# Antropy manuscript

Daniel Ari Friedman’s methods manuscript documents the estimator definitions,
synthetic experiments, computational costs and inference limits for
`antropy-hd` 0.3.1. Start with the [abstract](00_abstract.md), the
[methodology](03_methodology.md), the [results](06_results.md) and the
[inference and power analysis](07_inference_and_power.md).

The numbered Markdown files are the editable source. The native publication
builder uses [project.yaml](project.yaml). The pinned standalone replay uses
[config.yaml](config.yaml). Both use the same section order, [preamble](preamble.md)
and [bibliography](references.bib). Keep the section lists aligned when
changing the order. The native builder generates the [assembled manuscript](../archive/manuscript.md), copies the
resolved sections to `output/manuscript/`, and binds the claims and the
release PDF to its inputs.

Use the [native acceptance guide](../reproducibility.md) to regenerate the
artifacts or [replay the public snapshot](../template-adaptation.md#replay-the-pdf-from-the-checked-in-results)
to verify the canonical source against the checked-in results and figures.
