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

{{COMPLEXITY_TABLE}}

Guard bytes cover the controlled template and pair workspace. Caller-owned
input arrays, file loading, standard-deviation temporaries, allocator overhead,
vendor-library workspaces and process resident memory are outside that bound.
The guard must reject infeasible requests; it is not a measurement of process
RSS or a universal memory guarantee.

## Empirical timing observations

{{BENCHMARK_NARRATIVE}}

{{BENCHMARK_TABLE}}

{{COST_FIGURE}}

Timings are observed on the recorded environment and inputs. They do not prove
an asymptotic theorem or promise portable latency. Block size can change
workspace, call scheduling and runtime without changing the mathematical pair
population or estimator value. Numerical validity, analytical cost and measured
runtime are therefore checked and reported independently.
