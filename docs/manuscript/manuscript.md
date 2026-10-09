# antropy: a dimension-agnostic entropy methods framework

Daniel Ari Friedman

Computational methods manuscript accompanying antropy-hd 0.1.0. Generated from
the repository's deterministic experiment plan; this is an implementation report.

## Abstract

antropy organizes high-dimensional sample entropy and related complexity
estimators around validated spatial embedding, explicit estimator conventions,
typed results and reproducible orchestration. Local templates preserve native
coordinate structure before each window is flattened. Probability, ordinal,
spectral and trajectory measures share explicit finite, undefined and infinite
statuses. A seeded synthetic demonstration covers the configured spatial dimensions
and fields at several tolerances. The software and numerical examples are intended
to support reproducible methods development; they do not reproduce the empirical
experiments in Xia and Wang (2026), establish new scientific findings, or define
an estimator-independent ordering of complexity.

## Motivation and scope

Spatial data should not be flattened globally before local templates are formed.
A dimension-agnostic framework makes geometry, delay, stride, tolerance scaling,
exclusions, distance and memory budgets visible. The repository name combines
entropy and ant, reflecting interest in collective biological systems. The
distribution antropy-hd and import antropy_hd avoid shadowing the separate
AntroPy time-series library. The present examples use generated arrays only.

## HDSE and local template estimators

HDSE follows Xia and Wang's high-dimensional sample entropy construction:
compare m-sized local blocks and their m+1 extensions over common valid origins,
use maximum absolute component distance and a strict threshold r times global
standard deviation, exclude a template's comparison with itself, and return the
negative natural logarithm of the ratio of extended to base matches. Population
standard deviation (ddof=0) is the explicit default. The source's prose requires every coordinate to differ, while its equations
exclude the identical origin tuple; these define different pair populations;
ordinary tuple self-exclusion is the default, and coordinate exclusion is exposed
as sensitivity configuration. The implementation contract records this decision.

Zero base matches yield undefined status; positive base matches and zero extended
matches yield infinite status. Constant fields at zero strict tolerance produce no
matches. Rectangular windows, selected extension axes, other norms, delay, stride
and Theiler exclusions are declared extensions. One-dimensional sample entropy,
approximate entropy using separate complete origin populations with self matches,
fuzzy entropy with exp(-(distance/tolerance)^power), distance-distribution entropy,
and trimmed block-mean multiscale analysis have separately documented contracts.
Distance-distribution entropy uses all valid local origins; the original DistEn
paper omits the final valid origin, so this is an explicitly declared extension.
Fuzzy sums use log-domain accumulation to preserve small similarities. Multiscale
analysis preserves original-data tolerance by default.

## Related estimator definitions

For a normalized discrete distribution p, Shannon entropy is -sum(p log_b p),
with zero-mass terms contributing zero. Renyi entropy is log_b(sum(p^q))/(1-q),
with support-size, Shannon and maximum-probability limits at q=0, q=1 and positive
infinity. Tsallis entropy is (1-sum(p^q))/(q-1), with k=1 and a natural-log Shannon
limit at q=1. Joint entropy applies Shannon to the full probability tensor;
conditional entropy is H(X,Y)-H(Y), and mutual information is H(X)+H(Y)-H(X,Y).
Jensen-Shannon divergence is the weighted mixture entropy minus the weighted
component entropies. These probability identities do not estimate a distribution
from amplitude data by themselves.

Permutation entropy applies Shannon to local ordinal-pattern frequencies; weighted
permutation entropy replaces counts by local variance weights. Spectral entropy
applies Shannon to normalized FFT powers. SVD entropy applies Shannon to normalized
singular values of the trajectory matrix. Normalization divides by the documented
maximum for the probability alphabet, possible ordinal patterns, Fourier bins or
singular-value count. Zero spectral energy and zero total ordinal variance are
undefined, while unnormalized Shannon entropy for a singleton alphabet is zero.
Distance-distribution entropy applies Shannon to a configured histogram of pairwise
local-template distances. The histogram range and count affect that estimate.

## Related estimators and interpretation

Discrete Shannon, Renyi, Tsallis, joint and conditional entropy, mutual information
and Jensen-Shannon divergence consume normalized probability arrays. Histogram
entropy explicitly discretizes observed amplitudes. Spatial permutation entropy
uses stable position-based tie ordering within local windows; its weighted form
weights by local population variance. N-dimensional spectral entropy normalizes
the full FFT periodogram, retaining conjugate bins individually. SVD entropy
normalizes singular values of the local trajectory matrix without squaring them.
These conventions are not interchangeable: output units, normalization, alphabet,
and input meaning are part of each result. A value from one estimator should not
be treated as a calibrated value of another estimator.

## Software architecture and verification

The numerical package depends on NumPy, Pydantic and Typer. Numerical routines do
not import plotting, manuscript rendering or network services. Configurations
reject unknown fields, method dispatch binds the full function signature, arrays
must be finite real numeric data, and resource limits constrain template and pair
work. Memory bounds cover controlled template and pair workspace, excluding
caller arrays, parsing, SD temporaries and process RSS. Nonfinite eligible fuzzy
distances or log weights raise a numerical-range error instead of returning a
mathematical undefined estimate. The CLI reads NPY with pickle disabled and CSV as a two-dimensional grid.
Strict JSON represents nonfinite estimates as null plus an explicit status.
Tests use analytical examples, a direct loop oracle, seeded numerical inputs,
real file boundaries and subprocesses. Deliberately malformed inputs and missing
or altered artifacts must cause checks to fail. CI runs lint, strict type checks,
branch-inclusive source coverage at a 90 percent floor, artifact validation and
an installed-wheel CLI scenario. Passing these checks is evidence for the tested
contracts, not proof of every possible scientific use.

## Synthetic experiment design

The complete design is in experiment_plan.yaml. Independent seeded generators
produce periodic fields, Gaussian noise and periodic fields with additive Gaussian
noise. Fields have shapes 64, 16 x 16, 8 x 8 x 8. HDSE uses shape 2 on every
axis and relative tolerances 0.2, 0.5, 1.0; default strict Chebyshev matching
and self-exclusion are retained. Histogram entropy, normalized spatial permutation
entropy and normalized full-FFT entropy are also recorded for each field.
Changing dimension changes both window feature count and finite sample geometry;
the experiment is a software demonstration rather than a controlled scientific
comparison attributing differences solely to dimension.

## Computational results

The pipeline recorded 54 estimator rows: 45 finite,
3 undefined and 6 infinite. Every status
is retained. The following HDSE values are generated directly from the CSV.
No monotonic relationship or classification accuracy is claimed.

| Dimension | Structure | Relative radius r | HDSE (nats) | Status |
|---|---|---|---|---|
| 1 | periodic | 0.2 | 0 | finite |
| 1 | periodic | 0.5 | 0.451985 | finite |
| 1 | periodic | 1.0 | 0.245482 | finite |
| 1 | noise | 0.2 | 1.4816 | finite |
| 1 | noise | 0.5 | 1.22536 | finite |
| 1 | noise | 1.0 | 0.680827 | finite |
| 1 | mixed | 0.2 | 2.70805 | finite |
| 1 | mixed | 0.5 | 1.02233 | finite |
| 1 | mixed | 1.0 | 0.488638 | finite |
| 2 | periodic | 0.2 | 0.262364 | finite |
| 2 | periodic | 0.5 | 1.07654 | finite |
| 2 | periodic | 1.0 | 0.765302 | finite |
| 2 | noise | 0.2 | - | undefined |
| 2 | noise | 0.5 | - | infinite |
| 2 | noise | 1.0 | 3.31381 | finite |
| 2 | mixed | 0.2 | - | infinite |
| 2 | mixed | 0.5 | 3.17109 | finite |
| 2 | mixed | 1.0 | 1.75318 | finite |
| 3 | periodic | 0.2 | - | infinite |
| 3 | periodic | 0.5 | 1.86322 | finite |
| 3 | periodic | 1.0 | 0.898039 | finite |
| 3 | noise | 0.2 | - | undefined |
| 3 | noise | 0.5 | - | infinite |
| 3 | noise | 1.0 | - | infinite |
| 3 | mixed | 0.2 | - | undefined |
| 3 | mixed | 0.5 | - | infinite |
| 3 | mixed | 1.0 | 4.71253 | finite |

![HDSE across tolerances and dimensions](../../output/figures/hdse-tolerance.png)

Figure 1. Finite HDSE estimates for the seeded synthetic fields. Text annotations
preserve undefined and infinite outcomes; those outcomes are not plotted as zero.
Lines connect configured tolerances and serve as visual guides only.

## Provenance and reproducibility

Results CSV SHA-256: a4104429035874774f07cb2ec816a1cd656504435f245754d730e3bc06526727

The manifest records hashes and byte counts for generated inputs, strict JSON,
the CSV, figure, inspectable Markdown manuscript and PDF, as well as source and
configuration inputs. The validator requires the complete artifact set, verifies
actual bytes, cross-checks JSON rows against CSV, and inspects PDF text. Re-running
the scripts reproduces the specified experiment; a changed configuration or
implementation requires regeneration of the manifest and manuscript.

The project adapts docxology/template_code_project at commit
04040a1e8eda0b31ce61db888cd1b3598f1696ca. Its domain-neutral separation of source,
tests, scripts, data, manuscript and output is retained. A standalone package,
focused synthetic design and reportlab renderer replace the template's monorepo
demonstration and publication infrastructure. The supplied copyrighted paper is
not included in this repository. No DOI is claimed for this unreleased project.

## Limitations and next work

Pair counting remains quadratic in the number of templates. Blocked comparisons
bound intermediate memory but do not eliminate that computational growth. High
dimension and low tolerance can leave few or no matches, so status and counts
must accompany any estimate. Stable ordinal ties are a deterministic convention,
not a model of measurement noise. Histogram estimates depend on binning; FFT and
SVD estimates depend on preprocessing and normalization. The synthetic experiment
does not validate use in ant behavior, biomedical diagnosis, or classification.
Independent review, application-specific validation and appropriately controlled
scientific studies remain necessary for those uses.

## References

Pincus SM (1991). Approximate entropy as a measure of system complexity.
Proceedings of the National Academy of Sciences 88, 2297-2301.
https://doi.org/10.1073/pnas.88.6.2297

Richman JS and Moorman JR (2000). Physiological time-series analysis using
approximate entropy and sample entropy. American Journal of Physiology - Heart
and Circulatory Physiology 278, H2039-H2049.
https://doi.org/10.1152/ajpheart.2000.278.6.H2039

Chen W et al. (2007). Characterization of surface EMG signal based on fuzzy entropy.
IEEE Transactions on Neural Systems and Rehabilitation Engineering.
https://doi.org/10.1109/TNSRE.2007.897025

Costa M, Goldberger AL and Peng CK (2002). Multiscale entropy analysis of complex
physiologic time series. Physical Review Letters 89, 068102.
https://doi.org/10.1103/PhysRevLett.89.068102

Li P et al. (2015). Assessing the complexity of short-term heartbeat interval
series by distribution entropy. Medical and Biological Engineering and Computing.
https://doi.org/10.1007/s11517-014-1216-0

Xia W and Wang F (2026). High-dimensional sample entropy for uncovering rich
complex structures in data. Chaos, Solitons and Fractals 208, 118076.
https://doi.org/10.1016/j.chaos.2026.118076

Shannon CE (1948). A Mathematical Theory of Communication. Bell System Technical
Journal 27, 379-423. https://doi.org/10.1002/j.1538-7305.1948.tb01338.x

Renyi A (1961). On Measures of Entropy and Information. Fourth Berkeley Symposium,
volume 1, 547-561. Primary source and complete conventions: docs/sources-related.md.

Tsallis C (1988). Possible generalization of Boltzmann-Gibbs statistics. Journal of
Statistical Physics 52, 479-487. https://doi.org/10.1007/BF01016429

Lin J (1991). Divergence measures based on the Shannon entropy. IEEE Transactions
on Information Theory 37, 145-151. https://doi.org/10.1109/18.61115

Bandt C and Pompe B (2002). Permutation Entropy: A Natural Complexity Measure for
Time Series. Physical Review Letters 88, 174102. https://doi.org/10.1103/PhysRevLett.88.174102

Fadlallah B, Chen B, Keil A and Principe J (2013). Weighted-permutation entropy.
Physical Review E 87, 022911. https://doi.org/10.1103/PhysRevE.87.022911

Rezek IA and Roberts SJ (1998). Stochastic complexity measures for physiological
signal analysis. IEEE Transactions on Biomedical Engineering 45, 1186-1191.
https://doi.org/10.1109/10.709563

Broomhead DS and King GP (1986). Extracting qualitative dynamics from experimental
data. Physica D 20, 217-236. https://www.sciencedirect.com/science/article/pii/016727898690031X
