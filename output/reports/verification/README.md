# Accepted verification evidence

The accepted local receipts for the bounded replay correction are:

- `source-tests-roundoff.log` and `source-coverage-roundoff.json`: 370 passing
  tests and 95.67% branch-inclusive source coverage across all 16 package modules.
- `infrastructure-tests-roundoff.log` and `infrastructure-coverage-roundoff.json`:
  64 passing artifact tests and 82.91% branch-inclusive infrastructure coverage.
- `lint-roundoff.log`, `format-roundoff.log`, `types-roundoff.log`, and
  `programming-roundoff.log`: successful lint, formatting, strict type and
  supplemental programming checks.
- `build-roundoff.log`, `wheel-roundoff.log`, `artifacts-roundoff.log`, and
  `archive-roundoff.json`: rebuilt archives, isolated installed-wheel execution,
  48 authenticated scientific files, 54 result rows and five unchanged PDF pages.
- `../../reviews/replay-repair-review.md`: independent review of the correction.

The first public commit's hosted run failed the former exact synthetic replay
check on Linux. `hosted-initial-failure.log` preserves its actual failed output.
Local acceptance does not certify a hosted run; the corrective commit's GitHub
Actions result is a separate receipt.

The initial public commit's accepted frozen-source receipts remain preserved:

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
disk failures; the current roundoff receipts above take precedence for the repair.
Earlier rejected wheel bytes and full review history are retained locally in ignored
working directories and were replaced only after exact source/archive verification.

Tests use real numerical arrays, files and subprocesses. Invalid geometry, thresholds,
probabilities, numerical ranges, resources, missing/corrupt artifacts and coherently
incomplete experiments are explicit negative controls. The supplemental style
checker also rejected a deliberate forbidden-type fixture before accepting the source.
No mocking framework or silent failure suppression was introduced.
