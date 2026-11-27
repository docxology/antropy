# Computational complexity and resources {#sec:cost}

For $n$ local templates with $q$ components, explicit extraction requires
$O(nq)$ component work and storage. Exhaustive pair comparison contributes
$O(n^2q)$ distance-component work. Extending all axes replaces $q$ by
$q^+=\prod_j(m_j+1)$, so native-dimensionality changes feature count as well as
the valid-origin population in [@eq:origins]. Flattening changes both quantities.

The implementation processes bounded pair blocks. This controls workspace but
does not remove quadratic total pair work. Its allocation-free estimator reports
the actual scheduled distance cells, component visits, blocks, origin arrays and
conservative guard bytes for the selected request. Distance work can include
cells later excluded by pair masks; admissible pair counts and computed
distance cells are distinct quantities. Exact scheduled counts, asymptotic size
terms and host runtime observations retain separate interpretations.

Identical scheduled-work rows across radius settings are listed once below;
the complete per-analysis estimates remain in the stored complexity report.

Here flat denotes row-major flattened observations; maximum and histogram denote the distance passes.

\begingroup\small\setlength{\tabcolsep}{8pt}

| Input | Stage | $n$ | $q$ | Pairs | Visits | Guard (B) |
|---|---|---:|---:|---:|---:|---:|
| 6 x 7 x 8 | base native | 120 | 8 | 7140 | 86528 | 695936 |
| 6 x 7 x 8 | extended native | 120 | 27 | 7140 | 292032 | 695936 |
| 6 x 7 x 8 | maximum native | 210 | 8 | 21945 | 226848 | 683056 |
| 6 x 7 x 8 | histogram native | 210 | 8 | 21945 | 226848 | 683056 |
| 6 x 7 x 8 | local native | 210 | 8 | 0 | 0 | 85680 |
| 336 | base flat | 334 | 2 | 55611 | 132232 | 675488 |
| 336 | extended flat | 334 | 3 | 55611 | 198348 | 675488 |
| 10 x 12 | base native | 80 | 4 | 3160 | 21504 | 669056 |
| 10 x 12 | extended native | 80 | 9 | 3160 | 48384 | 669056 |
| 10 x 12 | maximum native | 99 | 4 | 4851 | 30244 | 669328 |
| 10 x 12 | histogram native | 99 | 4 | 4851 | 30244 | 669328 |
| 10 x 12 | local native | 99 | 4 | 0 | 0 | 20592 |
| 120 | base flat | 118 | 2 | 6903 | 20936 | 665120 |
| 120 | extended flat | 118 | 3 | 6903 | 31404 | 665120 |
| 48 | base native | 46 | 2 | 1035 | 4232 | 344864 |
| 48 | extended native | 46 | 3 | 1035 | 6348 | 344864 |
| 48 | maximum native | 47 | 2 | 1081 | 4418 | 363784 |
| 48 | histogram native | 47 | 2 | 1081 | 4418 | 363784 |
| 48 | local native | 47 | 2 | 0 | 0 | 7120 |
| 48 | base flat | 46 | 2 | 1035 | 4232 | 344864 |
| 48 | extended flat | 46 | 3 | 1035 | 6348 | 344864 |

\endgroup

Guard bytes cover the controlled template and pair workspace. Caller-owned
input arrays, file loading, standard-deviation temporaries, allocator overhead,
vendor-library workspaces and process resident memory are outside that bound.
The guard must reject infeasible requests; it is not a measurement of process
RSS or a universal memory guarantee.

## Empirical timing observations

The recorded environment is Python 3.14.7, NumPy 2.5.3, macOS-27.0.1-arm64-arm-64bit-Mach-O, machine arm64. The configured plan uses 1 warmups and 3 measured repetitions per request; block sizes are 16, 64.

| Shape | Block | Median (s) | Sample SD (s) | Visits | Guard (B) |
|---|---|---|---|---|---|
| 4 x 4 x 4 | 16 | 0.000233416 | 3.24125e-05 | 2240 | 16768 |
| 4 x 4 x 4 | 64 | 0.000179125 | 6.43296e-06 | 2240 | 16768 |
| 6 x 6 | 16 | 0.000105208 | 2.92041e-06 | 3328 | 46976 |
| 6 x 6 | 64 | 0.000101584 | 4.27311e-06 | 3328 | 46976 |
| 6 x 6 x 6 | 16 | 0.000730875 | 4.06458e-06 | 89600 | 64512 |
| 6 x 6 x 6 | 64 | 0.000358125 | 3.68909e-06 | 143360 | 678912 |
| 8 x 8 x 8 | 16 | 0.00741188 | 0.000489106 | 875840 | 110720 |
| 8 x 8 x 8 | 64 | 0.00221696 | 0.000139051 | 1041600 | 725120 |
| 10 x 10 | 16 | 0.000394875 | 2.604e-05 | 33280 | 52736 |
| 10 x 10 | 64 | 0.000279375 | 5.43607e-05 | 53248 | 667136 |
| 14 x 14 | 16 | 0.00151417 | 8.36652e-05 | 149760 | 62336 |
| 14 x 14 | 64 | 0.000536333 | 0.000197742 | 189696 | 676736 |
| 32 | 16 | 0.000118458 | 8.8355e-06 | 3380 | 46496 |
| 32 | 64 | 9.5167e-05 | 5.26603e-05 | 4500 | 149536 |
| 64 | 16 | 0.00025375 | 5.37063e-05 | 12020 | 48032 |
| 64 | 64 | 0.000103292 | 3.42341e-06 | 19220 | 622112 |
| 96 | 16 | 0.000437917 | 8.76008e-06 | 25780 | 49568 |
| 96 | 64 | 0.000261333 | 7.39915e-05 | 34580 | 663968 |

![Measured runtime and configured deterministic work estimates. Host timings are diagnostic observations; exact scheduled counts and asymptotic terms have separate interpretations.](../../output/study/figures/cost-scaling.png){#fig:cost width=100%}

Timings are observed on the recorded environment and inputs. They do not prove
an asymptotic theorem or promise portable latency. Block size can change
workspace, call scheduling and runtime without changing the mathematical pair
population or estimator value. Numerical validity, analytical cost and measured
runtime are therefore checked and reported independently.
