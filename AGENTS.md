# antropy engineering contract

Use `uv sync --locked` and `uv run` on CPython 3.14. Preserve unrelated changes.
The numerical core in `src/antropy_hd` has no manuscript, plotting, network, or
repository infrastructure dependencies. The CLI is the file boundary; `scripts/`
orchestrate research and validation. Manuscript sources live in `docs/manuscript/`.

Use real numerical inputs, files and subprocesses. Mocking frameworks are prohibited.
Maintain at least 90% branch-inclusive source coverage, strict type checking and lint.
Checks must reject deliberately broken inputs. Never silently substitute results,
drop nonfinite data, flatten spatial data before local embedding, or invent claims.

Published HDSE uses common origins, Chebyshev distance, strict threshold and global
standard deviation. Document extensions and the paper's self-exclusion ambiguity.
Undefined and infinite estimates must carry explicit status and counts.
Never audit work you built. Independent review is required before initial push.
