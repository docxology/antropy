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
Configured coverage floors are 90 percent for numerical
source and 60 percent for research infrastructure.

The configured verification receipts report 900 passing tests, 94.5148 percent source coverage and 90.3808 percent infrastructure coverage. These are recorded runs, not a substitute for independent release review.

Receipt identities (SHA-256):

\begingroup\small

```text
Source coverage: 03540005d22140e5a9c01a3285f3a7a296fd00face280f7de5ee925a49c6c2f2
Infra coverage:  eac3d86e592fd68e400e59f9fdaaf572c374a255d6792b2bcebeaacfc5a1a214
Test log:        8002be50f04715d7253e93f2de3b567791818dcc083ab85ec5923ac4769c6086
```

\endgroup

## Source-bound manuscript generation

The title, author metadata, version, design, measurements, tables and figure
paths are sourced from the validated publication profile, project manifest and
generated reports. Template variables must all resolve before rendering. The
shared implementation is [docxology/template](https://github.com/docxology/template), pinned at
`d39f2478da2512b42ad961e98a5f3b854723f92e`, using the canonical `projects/templates/template_code_project/manuscript` conventions.
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
Results CSV SHA-256: a4104429035874774f07cb2ec816a1cd656504435f245754d730e3bc06526727
Study CSV SHA-256: 493fd105d2410a1ac66c3bcf75e2a0313dc69e7b6ccd58625508454cc3ae57ce
Study report SHA-256: e77af9a7e5a55ddca73d9f779e55cf5e715d60e77b0fadd7c93f91f409f425be
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
