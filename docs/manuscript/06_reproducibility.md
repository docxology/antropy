# Reproducibility and software architecture {#sec:reproducibility}

## Numerical and file boundaries

The numerical package separates array validation, geometry, blocked pair work
and estimator-specific semantics. It does not import manuscript or plotting
tooling. Immutable configurations reject unknown options. The registry binds
the complete call signature, distinguishes observations from probability
alphabets and retains effective parameters in every result. NPY loading disables
pickle; CSV inputs retain their declared grid meaning. Strict JSON represents
nonfinite estimates through explicit statuses and null values.

Tests use analytical examples, independently computed loop oracles, seeded
arrays, real files and actual subprocesses. Deliberately invalid inputs and
coherently altered artifact records are controls proving that checks can fail.
Configured coverage floors are {{SOURCE_COVERAGE_FLOOR}} percent for numerical
source and {{INFRA_COVERAGE_FLOOR}} percent for research infrastructure.

{{VERIFICATION_NARRATIVE}}

## Source-bound manuscript generation

The title, author metadata, version, design, measurements, tables and figure
paths are sourced from the validated publication profile, project manifest and
generated reports. Template variables must all resolve before rendering. The
shared implementation is [docxology/template]({{TEMPLATE_REPOSITORY}}), pinned at
`{{TEMPLATE_REVISION}}`, using the canonical `{{TEMPLATE_EXEMPLAR}}` conventions.
Actual installed Python and Lua source files are authenticated against their
installer RECORD hashes. Pandoc, Pandoc-crossref, BibTeX and the selected LaTeX
engine produce mathematical typesetting, resolved references and a real TOC.
No custom ReportLab manuscript fallback is used.

The inspectable resolved section tree, variable inventory, renderer source/tool
receipt, generated TeX/TOC diagnostics and final PDF remain distinct artifacts.
Figure staging uses exact-byte copies of producer outputs because the shared
PDF renderer expects a sibling figure directory. Staging does not recompute or
alter those figures.

## Provenance bindings

\begingroup\small

```text
Results CSV SHA-256: {{BASELINE_CSV_SHA256}}
Study CSV SHA-256: {{STUDY_CSV_SHA256}}
Study report SHA-256: {{STUDY_REPORT_SHA256}}
```

\endgroup

The manifest binds actual input, configuration, code and output bytes. Stored
file, canonical array, configuration, result and table identities remain exact.
Synthetic design replay alone uses a declared, machine-epsilon-derived float64
envelope after exact shape and finite-value checks. This accommodates bounded
platform roundoff without changing stored inputs, smoothing matching thresholds
or relabeling stale results. The initial hosted failure and its adversarial
regression controls are retained in the project record.

The supplied published PDF is not redistributed. No project DOI, journal
acceptance, empirical source-paper replication or independent application
validation is claimed by the software build. Independent scientific and release
review remains separate from these executable engineering checks.
