# Related measures: source and convention record

Primary sources were checked on 2026-10-09. These are method definitions, not
claims of reproducing the source papers' empirical experiments.

| Method | Primary source | Implementation convention |
|---|---|---|
| Shannon entropy, joint and conditional entropy, mutual information | C. E. Shannon (1948), *A Mathematical Theory of Communication*, Bell System Technical Journal 27, 379–423. [DOI](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x) | Discrete probability tensors; zero-mass cells contribute zero; user selects a logarithm base greater than one. Raw amplitude histograms are a separately named estimator. |
| Rényi entropy | A. Rényi (1961), *On Measures of Entropy and Information*, Fourth Berkeley Symposium, volume 1, 547–561. [Author-institute scan](https://static.renyi.hu/renyi_cikkek/1961_on_measures_of_entropy_and_information.pdf) | Orders zero, one, and positive infinity use support, Shannon, and min-entropy limits. No DOI was inferred for this proceedings chapter. |
| Tsallis entropy | C. Tsallis (1988), *Possible generalization of Boltzmann-Gibbs statistics*, Journal of Statistical Physics 52, 479–487. [Publisher and DOI](https://link.springer.com/article/10.1007/BF01016429) | Boltzmann constant set to one; order-one limit uses natural logarithms. No logarithm-base rescaling is applied to this measure. |
| Jensen–Shannon divergence | J. Lin (1991), *Divergence measures based on the Shannon entropy*, IEEE Transactions on Information Theory 37, 145–151. [Publisher](https://ieeexplore.ieee.org/document/61115), DOI 10.1109/18.61115 | Two same-shaped distributions over the same alphabet, explicit mixture weight; divergence rather than its square-root distance. |
| Permutation entropy | C. Bandt and B. Pompe (2002), *Permutation Entropy: A Natural Complexity Measure for Time Series*, Physical Review Letters 88, 174102. [Publisher and DOI](https://doi.org/10.1103/PhysRevLett.88.174102) | Order local samples, with ties broken by position. Multidimensional rectangular windows flattened in C order only after spatial extraction are a documented extension. |
| Weighted permutation entropy | B. Fadlallah, B. Chen, A. Keil and J. Príncipe (2013), *Weighted-permutation entropy: A complexity measure for time series incorporating amplitude information*, Physical Review E 87, 022911. [Publisher manuscript](https://link.aps.org/accepted/10.1103/PhysRevE.87.022911), DOI 10.1103/PhysRevE.87.022911 | Population variance weights each local window; zero total variance means undefined. Multidimensional windows are an extension. |
| Spectral complexity | I. A. Rezek and S. J. Roberts (1998), *Stochastic complexity measures for physiological signal analysis*, IEEE Transactions on Biomedical Engineering 45, 1186–1191. [Publisher](https://ieeexplore.ieee.org/document/709563), DOI 10.1109/10.709563 | This implementation uses the complete N-D FFT periodogram, including conjugate bins separately, with explicit demeaning and DC retention. It does not claim equivalence to every one-sided or Welch spectral convention. |
| Singular-value embedding | D. S. Broomhead and G. P. King (1986), *Extracting qualitative dynamics from experimental data*, Physica D 20, 217–236. [Publisher and DOI](https://www.sciencedirect.com/science/article/pii/016727898690031X) | Shannon entropy of normalized singular values of a local trajectory matrix, without squaring singular values. The spatial window generalization and this exact entropy convention are explicitly specified here. |

Probability APIs require a finite, nonnegative tensor whose sum is one within
floating-point tolerance; counts are never silently interpreted as probabilities.
Probability tensor axes represent variables, unlike amplitude-array axes, which
represent spatial or temporal coordinates. Joint entropy includes all tensor axes;
conditional entropy conditions on named axes; mutual information partitions axes
into an explicit X set and its complement. Normalization uses the stated alphabet
size, possible ordinal pattern count, Fourier-bin count, or singular-value count.

NumPy implementation semantics were checked against its official documentation:
[stable argsort](https://numpy.org/doc/stable/reference/generated/numpy.argsort.html),
[N-dimensional FFT](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html),
and [SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html).
Stable sorting preserves the local C-order position of equal values. The full FFT
retains the original axis structure until power bins are pooled. Numerical scaling
before FFT, SVD, or variance calculation preserves the normalized distribution
while preventing overflow for finite but very large amplitudes. To preserve small
representable fluctuations on a large baseline, variance-weighted permutation
entropy translates each window by its midpoint before applying a common amplitude
scale. Demeaned spectral entropy first translates by the global midpoint; demeaned
SVD first translates each trajectory column by its own midpoint. Midpoints use
`min/2 + max/2` to avoid overflow. Ordinal ranks retain the original values, and
uncentered Fourier and SVD calculations retain their original amplitude origin.

The local test environment uses CPython 3.14.7, NumPy 2.5.3, and coverage.py
7.16.2. Collecting coverage through separate dotted source-package names triggered
a NumPy reentrant-import failure (`cannot load module more than once per process`)
during collection. Plain tests passed, and coverage collection through the source
directory succeeded; scoped branch-inclusive coverage was checked separately with
the unchanged 90% threshold. This is a test-tool invocation limitation, with no
product fallback or skipped numerical computation.
