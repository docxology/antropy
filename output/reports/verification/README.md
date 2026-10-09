# Accepted verification evidence

The accepted frozen-source receipts are:

- `source-tests-final.log` and `source-coverage-final.json`: 354 passing tests,
  95.67% branch-inclusive source coverage, including all 16 numerical/CLI modules.
- `infrastructure-tests-final.log` and `infrastructure-coverage-final.json`:
  48 passing artifact tests and 82.28% branch-inclusive infrastructure coverage.
- `lint-final.log`, `format-final.log`, and `types-final.log`: successful strict
  lint, formatting and type checks. The successful quiet formatter emits no text.
- `build-final.log`, `wheel-final.log`, and `artifacts-final.log`: final wheel/sdist
  build, isolated installed-wheel execution, and 48 authenticated scientific files,
  54 result rows and five PDF pages.
- `../../reviews/final-review.md`: independent approval of exact source and artifact
  hashes, real CLI scenarios, numerical replay and physical-page visual inspection.

`source-tests.log` and `source-coverage.json` are retained earlier snapshots;
they do not certify the final source. The scoped pipeline receipt in
`../../provenance/pipeline-verification.json` records worker checks and temporary
disk failures; the final source and infrastructure receipts above take precedence.
Earlier rejected wheel bytes and full review history are retained locally in ignored
working directories and were replaced only after exact source/archive verification.

Tests use real numerical arrays, files and subprocesses. Invalid geometry, thresholds,
probabilities, numerical ranges, resources, missing/corrupt artifacts and coherently
incomplete experiments are explicit negative controls. The supplemental style
checker also rejected a deliberate forbidden-type fixture before accepting the source.
No mocking framework or silent failure suppression was introduced.
