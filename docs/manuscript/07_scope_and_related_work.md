# Scope and related work {#sec:scope}

Shannon's discrete entropy defines information over a probability alphabet
[@shannon1948]. Renyi and Tsallis generalize that functional while changing its
order or extensivity conventions [@renyi1961; @tsallis1988]. Joint entropy,
conditional entropy and mutual information retain the variable-axis meanings
of probability tensors. Jensen-Shannon divergence compares distributions over a
shared alphabet [@lin1991]. These identities do not choose an amplitude
discretization or establish a spatial embedding.

Approximate entropy and sample entropy make local-pattern continuation central
[@pincus1991; @richman2000]. HDSE extends local sample-template reasoning to
higher-dimensional fields [@xia2026hdse]. Fuzzy entropy replaces a discontinuous
threshold indicator with a specified similarity kernel [@chen2007]. Multiscale
entropy asks related questions after coarse graining [@costa2002]. Distribution
entropy summarizes the empirical distribution of template distances
[@li2015distribution].

Permutation entropy constructs ordinal-pattern probabilities, with weighted
permutation entropy retaining local amplitude variability [@bandt2002;
@fadlallah2013]. Spectral and trajectory decompositions provide additional
representations [@rezek1998; @broomhead1986]. The implementation uses a full
multidimensional FFT periodogram and normalized singular values; neither
convention is assumed identical to every spectral or SVD estimator in use.

Statistical complexity combines normalized entropy with disequilibrium. Here the
Jensen-Shannon construction follows Rosso and colleagues and the broader family
described by Martin and colleagues [@rosso2007; @martin2006]. Fixed-bin amplitude
probabilities are a declared descriptive extension. This study does not infer
Bandt-Pompe causality or diagnose noise versus chaos from those amplitudes.

The unified framework is an engineering and mathematical organization of these
contracts. It does not assert that the estimators define one calibrated scalar
ordering of complexity. Native HDSE versus flattened SampEn also changes feature
count and extension geometry; that comparison is not a controlled intervention
on flattening alone.
