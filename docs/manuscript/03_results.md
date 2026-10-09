# Computational results {#sec:results}

## Baseline outcomes

The baseline records {{BASELINE_ROWS}} estimates: {{BASELINE_FINITE}} finite,
{{BASELINE_UNDEFINED}} undefined and {{BASELINE_INFINITE}} infinite. Its HDSE
values are displayed directly from the stored CSV.

{{BASELINE_TABLE}}

{{BASELINE_FIGURE}}

## Replicated native HDSE

The replicated report contains {{STUDY_FIELDS}} fields and {{STUDY_ROWS}}
estimates: {{STUDY_FINITE}} finite, {{STUDY_UNDEFINED}} undefined and
{{STUDY_INFINITE}} infinite. The tables retain the finite conditional mean and
sample SD, the finite fraction and the undefined/infinite counts (U/I). A dash
indicates an unavailable finite mean or SD; it does not denote zero entropy.

{{MIX_TABLE}}

{{MIX_FIGURE}}

{{DEGENERACY_FIGURE}}

Matching probabilities provide another view of these outcomes. A positive base
count followed by zero extended matches gives infinite continuation entropy;
zero base matches give undefined entropy. Increasing native feature count and
changing spatial geometry can therefore affect interpretability even when all
input amplitudes are valid.

{{MATCH_FIGURE}}

## Structured controls and alternative representations

{{CONTROL_TABLE}}

{{GEOMETRY_FIGURE}}

The geometry comparison is read together with feature counts and populations.
Neither a difference nor an agreement alone establishes estimator superiority.
The observed tables are specific to the declared synthetic design, radius,
finite sample and block geometry.

## Related entropy and statistical complexity

The recorded normalization options make these related-measure summaries
dimensionless. Display labels are {{MEASURE_LABELS}}.

{{RELATED_RESULTS_TABLE}}

{{STATISTICAL_FIGURE}}

The entropy-complexity plane separates distributional uncertainty from distance
to the uniform alphabet. A high normalized entropy and a high statistical
complexity are different conditions. These fixed-amplitude-bin observations
do not carry the causal ordinal interpretation of a Bandt-Pompe analysis.
