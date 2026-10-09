# Experimental setup {#sec:experiments}

## Retained baseline

The original implementation demonstration is retained as a distinct dataset.
Its shapes are 64, 16 x 16, 8 x 8 x 8, embedding shape 2,
relative radii 0.2, 0.5, 1 and seed 20261009. It uses periodic,
Gaussian and additive-mixture fields with period 8 and mixture
amplitude 0.35. This smaller demonstration is not pooled
with the replicated study.

## Replicated Bernoulli-replacement design

The main study uses shapes 48, 10 x 12, 6 x 7 x 8, embedding shape
2, relative radii 1.5, 2, 2.5 and mixing probabilities
0, 0.25, 0.5, 0.75, 1. Each condition has 5 generated trials.
The period is 12 and the root seed is 20261009. The complete
consumed design is generated below from the actual stored plan.

| Control | Configured value |
|---|---|
| schema version | 1 |
| seed | 20261009 |
| shapes | [[48], [10, 12], [6, 7, 8]] |
| mixing probabilities | [0.0, 0.25, 0.5, 0.75, 1.0] |
| controls | ["constant", "checkerboard", "gaussian", "correlated", "shuffled"] |
| replicates | 5 |
| radii | [1.5, 2.0, 2.5] |
| period | 12.0 |
| phase origin | 1 |
| embedding shape | 2 |
| gaussian sd | 1.0 |
| correlation steps | 3 |
| symbol range | [-4.0, 4.0] |
| symbol bins | 16 |
| max input elements | 10000 |
| max fields | 200 |
| max distance component visits | 500000000 |
| max templates | 1000 |
| max pairs | 500000 |
| max memory bytes | 134217728 |
| block size | 64 |

The MIX construction follows the source paper's replacement form rather than
the baseline's additive Gaussian mixture [@xia2026hdse]. For coordinate
$\boldsymbol u$,

$$
s(\boldsymbol u)=\sum_{j=1}^{d}\sin(2\pi (u_j+u_0)/T),\qquad
x_p(\boldsymbol u)=(1-\xi_{p,\boldsymbol u})s(\boldsymbol u)
+\xi_{p,\boldsymbol u}\eta_{\boldsymbol u},
$$ {#eq:mix}

where $u_0=1$ is the configured coordinate phase origin,
$\xi$ is Bernoulli with parameter $p$ and $\eta$ is uniform on
$[-\sqrt3,\sqrt3]$. The periodic sum is not divided by $\sqrt d$. Common random
numbers couple the mixing sweep within a trial, while the trial seed schedule
separates generated fields. The design is bounded by explicit template, pair,
input-element and workspace budgets.

Controls are constant, checkerboard, gaussian, correlated, shuffled. The Gaussian scale is 1;
the configured correlation procedure uses 3 steps.
Fixed amplitude symbolization declares 16 cells over
-4.0, 4.0. Complete probability vectors include empty cells.
Input meaning and symbolization policy are therefore part of the recorded
configuration rather than inferred from a plot.

\clearpage

![Illustrative generated fields from the stored synthetic design. Full inputs and seeds are preserved separately from their visual examples.](../../output/study/figures/input-fields.png){#fig:inputs width=100% fig-pos=p}

\clearpage

## Geometry and repetition

Native HDSE and row-major flattened SampEn receive the same underlying amplitude
field and relative-radius setting, but their local representations differ. A
native block has $m^d$ base features and an all-axis extension has $(m+1)^d$;
the flattened one-dimensional continuation adds one feature. Origin populations
and continuation dimensions also differ. These are comparison conditions, not
an assumption that the estimators must agree.

Reported means and sample standard deviations condition on finite outcomes.
Every summary separately retains total, finite, undefined and infinite counts.
Generated trials are the unit of variation; overlapping template pairs are not
treated as independent experimental replicates. No significance test or
classification accuracy is inferred from this synthetic design.
Deterministic conditions can produce identical fields across trial identities;
their repeated values do not establish empirical uncertainty.
