# Methodology {#sec:methodology}

## Native spatial templates

Let $x$ be a finite real-valued array with axis lengths
$\boldsymbol L=(L_1,\ldots,L_d)$. An embedding specifies block shape
$\boldsymbol m$, delays $\boldsymbol\delta$, strides $\boldsymbol s$ and
extension axes. For an origin $\boldsymbol i$, the local template contains
$x_{\boldsymbol i+\boldsymbol k\odot\boldsymbol\delta}$ for
$0\leq k_j<m_j$. Only this extracted block is flattened, in C order. Its
feature count is $q=\prod_jm_j$.

Write $\boldsymbol m^+$ for the extended shape. Common origins are chosen from
the geometry supporting that extended block, so the paired population has

$$
n=\prod_{j=1}^{d}\max\!\left(0,
1+\left\lfloor\frac{L_j-1-(m_j^+-1)\delta_j}{s_j}\right\rfloor\right).
$$ {#eq:origins}

The numerical boundary rejects nonfinite, complex, boolean, string, object,
empty and scalar inputs. Geometry and resource failures raise typed errors.
Rectangular shapes, selected extension axes, delays and strides are explicit
extensions of the paper's common isotropic window construction.

## High-dimensional sample entropy

For paired base and extended templates, use the same admissible unordered origin
pair set $\mathcal P$. With Chebyshev distance
$D_\infty(u,v)=\max_k|u_k-v_k|$ and threshold $\tau=r\sigma_x$, define

$$
B=\sum_{(i,j)\in\mathcal P}\mathbf 1\{D_\infty(u_i,u_j)<\tau\},\qquad
A=\sum_{(i,j)\in\mathcal P}\mathbf 1\{D_\infty(u_i^+,u_j^+)<\tau\}.
$$ {#eq:matches}

When $B>0$ and $A>0$,

$$\operatorname{HDSE}(x)=-\ln(A/B).$$ {#eq:hdse}

The implementation counts unordered pairs; doubling numerator and denominator
recovers the corresponding ordered symmetric counting convention. The standard
deviation is computed over the complete input, with population variance by
default because the source does not specify the degrees-of-freedom convention.
Strict thresholding follows the published HDSE definition [@xia2026hdse].

The paper's prose requiring every origin coordinate to differ and its equations
excluding only the identical origin tuple produce distinct populations.
Ordinary tuple self-exclusion is the default. Coordinate exclusion is exposed
as a documented sensitivity choice, along with Theiler exclusions and other
distance norms. For HDSE, $B=0$ is undefined; $B>0,A=0$ is infinite. A constant
field has zero relative threshold, so strict matching yields no matches even
when its amplitudes are identical.

The executable procedure is:

1. Parse the real array and immutable configuration.
2. Resolve common valid origins and guard template/pair storage.
3. Extract native base and extended windows on those origins.
4. Resolve global tolerance once from the declared standard deviation.
5. Count both representations with the same pair-selection policy.
6. Return value, status, populations, matching counts and effective parameters.

## Related local-template estimators

One-dimensional SampEn uses the same paired engine with its separately declared
boundary convention [@richman2000]. Approximate entropy uses complete, separate
origin populations at each block size and includes self matches. Its statistic
is $\phi_m-\phi_{m+1}$, where
$\phi_m=n_m^{-1}\sum_i\ln C_i^{(m)}$ [@pincus1991]. These populations and
normalizers are not substituted into HDSE.

Fuzzy entropy uses the explicit kernel
$K(D)=\exp[-(D/\tau)^p]$, optionally centering each template, and accumulates
membership sums in the log domain [@chen2007]. Centering changes template
semantics, so fuzzy continuation need not share all monotonicity properties of
un-centered threshold counts. Nonfinite eligible distances or log weights raise
a numerical-range error rather than becoming mathematical undefined estimates.

Multiscale analysis uses trimmed block means at the configured scale vector
[@costa2002]. Original-input tolerance is preserved by default. Distribution
entropy uses a specified histogram of pairwise distances; using all valid local
origins, including the final valid origin omitted by the original DistEn
construction, is explicitly an implementation extension [@li2015distribution].

## Probability, ordinal and decomposition estimators

For a declared probability alphabet of size $M$,

$$H_b(P)=-\sum_{a=1}^{M}p_a\log_b p_a,$$ {#eq:shannon}

with zero-mass terms contributing zero. Renyi entropy is
$\log_b(\sum_a p_a^\alpha)/(1-\alpha)$, with explicit support-size, Shannon
and min-entropy limits. Tsallis entropy is
$(1-\sum_a p_a^\alpha)/(\alpha-1)$ with $k=1$ and a natural-log Shannon
limit [@renyi1961; @tsallis1988]. Conditional entropy and mutual information use
the named tensor-axis partitions, not the spatial-axis interpretation of an
amplitude field.

Permutation entropy applies Shannon entropy to local ordinal-pattern
probabilities; equal amplitudes are ordered stably by local C-order position
[@bandt2002]. Its weighted version uses local population variance
[@fadlallah2013]. Spectral entropy normalizes the complete multidimensional FFT
power distribution, retaining conjugate bins individually. SVD entropy
normalizes singular values of the local trajectory matrix without squaring them
[@rezek1998; @broomhead1986]. Units, normalization and alphabet sizes accompany
each result; singleton and zero-energy degeneracies are handled explicitly.

## Jensen-Shannon statistical complexity

Let $P_e$ be uniform on the complete configured alphabet and $\Delta_M$ a point
mass on that same alphabet. The statistic is

$$
C_{JS}(P)=\frac{H_b(P)}{\log_b M}
\frac{J_b(P,P_e)}{J_b(\Delta_M,P_e)},\qquad
J_b(P,Q)=H_b\!\left(\frac{P+Q}{2}\right)-\frac{H_b(P)+H_b(Q)}{2}.
$$ {#eq:statistical}

Zero-probability cells remain in the declared alphabet. A point mass has zero
normalized entropy; a uniform distribution has zero disequilibrium. Their
statistical complexities are therefore zero for different reasons
[@rosso2007; @martin2006]. The final statistic is dimensionless. It complements
entropy rather than acting as its renamed value.

The study's fixed-bin amplitude alphabet has $M-2$ interior intervals and two
overflow cells, giving $M$ total categories. Values below the lower bound or
at least the upper bound remain in the corresponding overflow cell; empty cells
remain in the probability vector. This symbolization is a declared descriptive
extension, not a causal ordinal partition.
