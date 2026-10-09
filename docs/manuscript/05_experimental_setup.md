# Experimental setup {#sec:experiments}

## Retained baseline

The original implementation demonstration is retained as a distinct dataset.
Its shapes are {{BASELINE_SHAPES}}, embedding shape {{BASELINE_EMBEDDING}},
relative radii {{BASELINE_RADII}} and seed {{BASELINE_SEED}}. It uses periodic,
Gaussian and additive-mixture fields with period {{BASELINE_PERIOD}} and mixture
amplitude {{BASELINE_NOISE_AMPLITUDE}}. This smaller demonstration is not pooled
with the replicated study.

## Replicated Bernoulli-replacement design

The main study uses shapes {{STUDY_SHAPES}}, embedding shape
{{STUDY_EMBEDDING}}, relative radii {{STUDY_RADII}} and mixing probabilities
{{STUDY_MIXING}}. Each condition has {{STUDY_REPLICATES}} generated trials.
The period is {{STUDY_PERIOD}} and the root seed is {{STUDY_SEED}}. The complete
consumed design is generated below from the actual stored plan.

{{STUDY_PLAN_TABLE}}

The MIX construction follows the source paper's replacement form rather than
the baseline's additive Gaussian mixture [@xia2026hdse]. For coordinate
$\boldsymbol u$,

$$
s(\boldsymbol u)=\sum_{j=1}^{d}\sin(2\pi (u_j+u_0)/T),\qquad
x_p(\boldsymbol u)=(1-\xi_{p,\boldsymbol u})s(\boldsymbol u)
+\xi_{p,\boldsymbol u}\eta_{\boldsymbol u},
$$ {#eq:mix}

where $u_0={{STUDY_PHASE_ORIGIN}}$ is the configured coordinate phase origin,
$\xi$ is Bernoulli with parameter $p$ and $\eta$ is uniform on
$[-\sqrt3,\sqrt3]$. The periodic sum is not divided by $\sqrt d$. Common random
numbers couple the mixing sweep within a trial, while the trial seed schedule
separates generated fields. The design is bounded by explicit template, pair,
input-element and workspace budgets.

Controls are {{STUDY_CONTROLS}}. The Gaussian scale is {{STUDY_GAUSSIAN_SD}};
the configured correlation procedure uses {{STUDY_CORRELATION_STEPS}} steps.
Fixed amplitude symbolization declares {{STUDY_SYMBOL_BINS}} cells over
{{STUDY_SYMBOL_RANGE}}. Complete probability vectors include empty cells.
Input meaning and symbolization policy are therefore part of the recorded
configuration rather than inferred from a plot.

{{INPUT_FIGURE}}

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
