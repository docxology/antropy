# Contributing

Use CPython 3.14 and `uv sync --frozen`. Keep numerical source independent of
manuscript and plotting infrastructure. Each estimator needs a primary-source
definition, explicit input meaning, units, normalization, degeneracy handling and
resource policy. Spatial extensions must be labeled as extensions.

Reproduce defects using real arrays, files or subprocesses. Add an independently
computed numerical oracle or analytical example, and an input that demonstrates
the check can fail. Mocking frameworks and silent error fallbacks are prohibited.
Run lint, strict type checking, source branch-inclusive coverage at 90 percent,
infrastructure coverage at 60 percent, artifact validation, build and isolated
wheel checks. Regenerate artifacts after changing bound inputs.

Changes to scientific conventions require a documented rationale and independent
review. Do not infer a DOI, novelty claim or empirical result. Public release and
application-specific scientific validation are separate acceptance decisions.
