# Configuration and API

The authoritative signatures are the typed public functions in `antropy_hd`.
`antropy-hd methods` lists registered methods and input meanings. A JSON batch
contains a schema version and a nonempty array of uniquely identified analyses:

```json
{
  "schema_version": 1,
  "analyses": [
    {"id": "hdse", "measure": "hdse", "parameters": {
      "embedding": {"shape": [2, 2], "delay": 1, "stride": 1},
      "match": {"tolerance": 0.5, "relative": true, "ddof": 0,
                "closed": false, "metric": "chebyshev", "exclusion": "self"}
    }},
    {"id": "histogram", "measure": "histogram_entropy", "parameters": {"bins": 16}}
  ]
}
```

`EmbeddingConfig` accepts scalar or per-axis `shape`, `delay` and `stride`,
optional `extend_axes`, and hard `max_templates`, `max_pairs`,
`max_memory_bytes` limits. `MatchConfig` selects threshold, relative/global SD
scaling, `ddof`, strict versus closed comparison, metric, origin exclusion,
Theiler distance and comparison block size. All nested and top-level unknown keys
fail. Geometry remains spatial; only values within a window are flattened.
Memory limits cover controlled template storage and pair workspace; they are not
a bound on caller-owned input, file loading, SD temporaries, allocator overhead
or process resident memory.

Methods expose their additional keyword arguments directly. Fuzzy entropy has
`power` and `center`; histogram entropy has `bins` and `max_bins`; probability
information measures have explicit logarithm base or order as applicable.
Ordinal methods have normalization and maximum pattern length controls; spectral
and SVD methods expose demeaning and normalization. Jensen-Shannon divergence
consumes the primary input as `p` and requires a same-shaped `q` parameter.
Multiscale entropy accepts `scales` and `preserve_tolerance` and returns an ordered
array of scalar result objects. Method-specific arguments are validated by the
same numerical function used in Python, and an unknown argument fails before
batch execution begins.

Results record measure, status, value, observations, effective parameters and
diagnostics. `finite` requires a finite value; `undefined` and `infinite` require
`null`. Counts and degeneracy explanations travel with estimates. The batch adds
package version, input shape, canonical array hash, consumed configuration and
canonical configuration hash. The CLI also hashes the actual input file bytes.

NPY preserves arbitrary dimension; loading disables pickle. CSV analysis input denotes
a two-dimensional numeric grid, including one-row or one-column files. A one-
dimensional signal should use NPY. Boolean, string, object, complex, scalar,
empty and nonfinite arrays fail. Output creation is exclusive by default;
`--overwrite` explicitly permits replacement.

Probability tensors and amplitude fields have different axis meanings. Entropy
on probabilities requires a nonnegative array with total mass one; a joint
tensor's axes denote discrete random variables. Histogram entropy uses amplitude
bins; it does not preserve spatial geometry. Shannon/histogram/ordinal/spectral/
SVD outputs default to bits, local template measures to nats, and normalized
outputs are dimensionless. See [primary sources](sources-related.md) and
[the implementation contract](implementation-contract.md) for exact conventions.

CLI parameter JSON must use finite numbers. The Python Renyi API additionally
accepts positive infinity for the min-entropy limit; non-standard Infinity/NaN
JSON is rejected by strict serialization, so that order currently requires the
Python API. This constraint does not erase finite/infinite/undefined estimate
statuses, which remain explicitly represented in CLI results.

The `compare` command consumes two explicit observation vectors and a required
`PermutationConfig` JSON file, including a seed. For this command only, CSV can
be a single row or column of observation values; an NPY input must be a vector.
It rejects multidimensional grids rather than treating their cells as independent
subjects. The result binds both actual input files and the consumed configuration
bytes. See [inference contracts](inference.md) for pairing, tail, enumeration,
resampling, work-limit and interval controls. `fixed_alphabet` is a separate typed
transformation with immutable increasing cuts and explicit tie direction; it
returns counts and probabilities over the entire declared alphabet.
