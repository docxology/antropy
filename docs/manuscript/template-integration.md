# Shared research-template integration

The build imports `infrastructure.rendering.pdf_renderer.PDFRenderer` from the
`research-project-template[rendering]` Git dependency pinned in `pyproject.toml`
and `uv.lock`. Its upstream repository is `docxology/template`, source revision
`d39f2478da2512b42ad961e98a5f3b854723f92e`. The canonical authoring exemplar at
that revision is `projects/templates/template_code_project/manuscript`.
The separate `template_code_project` scaffold remains attributed in the project
adaptation record; neither external checkout is modified by this integration.

This manuscript follows the exemplar's ordered section, `config.yaml`, fenced
LaTeX `preamble.md`, and `references.bib` conventions. Its additional sections
cover related measures, synthetic design, resource estimates and reproducibility.
`project.yaml` is the project-specific strict publication profile. Project name,
version, license and authors come from `pyproject.toml`; measured values and design
controls come from producer reports, CSVs and plans. The configured profile
controls section order, figures, caption variables, toolchain and typography.

The build uses the upstream `substitute_manuscript_text` boundary to hydrate
section copies and rejects unresolved tokens. The actual upstream renderer then
runs Pandoc, Pandoc-crossref, BibTeX and LaTeX, including its native title page,
mathematical equation rendering, bibliography, TOC and deterministic PDF
canonicalization. There is no alternate ReportLab manuscript renderer.

`output/provenance/manuscript-template.json` records the installed dependency's
PEP 610 Git revision, authenticated Python/Lua RECORD hashes, actual rendering
tool versions, configured source-date epoch, section order and hashes of resolved
source sections, variables, profile, figures, TeX, TOC and final PDF. Native
diagnostics and bibliography output are copied to `output/manuscript/rendered.*`.
The artifact manifest binds these files separately from the generated science.

The adapter adds fail-closed checks for LaTeX errors, missing glyphs, unresolved
citations, duplicate labels, missing TOC and absent diagnostics because an engine
can write a PDF despite diagnostic failures. A real undefined-command fixture
proves this boundary. Figure staging copies exact producer bytes into the sibling
directory expected by the upstream renderer and rejects basename collisions.
No supplied copyrighted paper PDF is included in this repository.

The main profile requires the replicated study, analytical costs and benchmark
outputs. Small tests explicitly disable these requirements or generate their own
small real-file study. A missing main-study output is a build failure, not a
replacement with fixture results. Standalone builds need the pinned development
environment, Pandoc, Pandoc-crossref, BibTeX and the configured LaTeX engine.
