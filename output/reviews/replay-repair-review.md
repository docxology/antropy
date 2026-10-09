# Independent synthetic replay repair review

Date: 2026-10-09

- codeQualityStatus: **CLEAR**
- recommendation: **APPROVE** for the local source repair and scoped workflow change
- blockers: **None in the reviewed patch**
- Corrected hosted CI: **Pending; no successful rerun claimed**

The reviewer did not implement this repair or its tests. Final archive/manifest/staged-byte acceptance is recorded separately below when available. This report supplements the initial final review without rewriting the initial publication failure.

## Preserved failure

The first hosted workflow, [run 37978727833](https://github.com/docxology/antropy/actions/runs/37978727833), passed its numerical and tooling gates but failed synthetic design replay validation. Its actual failure log is preserved at `output/reports/verification/hosted-initial-failure.log`. The log identifies the old bit-identical replay comparison as the failure point; it does not establish the precise size of cross-platform rounding differences.

An intermediate repair also had a real fail-open defect: comparing a finite stored value with an infinite regenerated reference could accept `infinity <= infinity`. The reviewer reproduced acceptance of finite zero against both positive and negative infinity before the finite guard. That defect is now repaired and retained in the review history.

## Bounded behavior change

Synthetic replay requires identical shapes and finite values in **both** stored and regenerated arrays before any tolerance calculation. It then applies only:

`abs(x-y) <= 2*gamma_k*max(1,abs(y))`, with `epsilon=2^-52`, `k=16+8D`, and `gamma_k=k*epsilon/(1-k*epsilon)`.

There is no additional relative tolerance. The documentation identifies this as a declared finite float64 replay acceptance policy, not a universal bound on transcendental-library error. Outside-envelope differences and nonfinite synthesis fail closed.

This changes only comparison with a regenerated synthetic reference. Manifest byte counts and SHA-256, actual NPY hashes, canonical stored-array hashes, configurations, complete experiment coverage, CSV values/statuses, and manuscript/result bindings remain exact. It does not modify stored scientific arrays, loosen entropy thresholds or imply bit-identical regenerated entropy estimates across platforms.

The workflow's only change adds `tests/test_artifact_roundoff.py` to its infrastructure test invocation. The 60% infrastructure floor and all other gates remain unchanged. All 16 numerical package modules retain their previously approved hashes. The reviewed manuscript PDF also retains its previous hash.

## Independent evidence

- **Actual prior-validator RED/GREEN:** loaded the original Git revision's validator into a separate module and generated a real 30-row temporary project. The old validator passed the baseline. After changing one NPY value by one ULP and genuinely recomputing batch estimates, CSV, manuscript and hashes, exact report bindings passed; the old validator rejected at the `seed` boundary while the repaired validator accepted that same fixture.
- **Fail-closed nonfinite checks:** independently checked positive infinity, negative infinity and NaN in either array. All six combinations reject.
- **Real overflow plan:** a valid finite plan with seed 17, shape 12 and mixed-noise amplitude `1e308` produced three nonfinite reference entries. The warning was captured as evidence. Replacing those entries with finite zeros did not pass replay validation.
- **Precision boundary:** additional exact-rational checks covered dimensions 1–5 and reference values zero, positive/negative unit values and positive/negative large finite values. Half-envelope differences passed; twice-envelope differences and shape changes failed. Tests also check the last permitted binary64 step and the first step outside the envelope.
- **Custody negatives:** unrehashed one-ULP mutation, partial rehash without report identity, coherently resealed out-of-envelope mutation and coherently reseeded noise all remain rejected.
- **Focused suite:** 64 tests passed in 11.12 seconds using real arrays, files, subprocesses and resealed artifacts.
- **Static checks:** scoped Ruff passed; basedpyright reported zero errors, warnings and notes.

Temporary fixtures did not alter published scientific arrays or manuscript content. The initial hosted failure is not relabeled as a success; successful local checks and a future hosted result are separate claims.

## Severity and skill-perspective review

CRITICAL: none remaining. HIGH: none remaining. MEDIUM: none remaining. LOW: none requiring remediation.

The programming and remove-ai-slops perspectives were applied. Tests verify numerical policy and actual custody failures, not prose or requested deletions. Exact-rational boundary calculations are independent of the production float calculation. The typed failure helper preserves the same artifact exceptions while reducing repeated boilerplate; no fallback or swallowed failure was introduced. The comparison is isolated at the replay boundary and does not add normalization to the numerical estimator APIs.

## Reviewed patch identities

- `scripts/validate_artifacts.py`: `82b9f857719a256554227f8ceb423c8f7ffe2f11294c876663dc3966869c1c24`
- `tests/test_artifact_roundoff.py`: `bd989060dbe471ca538d1303aaf88df4501fc29996067e998868f2fad88fb233`
- `docs/reproducibility.md`: `b6cff8a97e8419da5ab1097f8f944c754301310aee562b9c2abc195c4b3d1271`
- `.github/workflows/verify.yml`: `a01d14ed1a8aa1c98be334e59756335b6eaffdbc23988b6f55457ee16745581b`
- `output/reports/verification/hosted-initial-failure.log`: `c70db14a1f210781bec1eb5a382448d428c36f31867ff48889ddc5693d65234a`
- `output/pdf/antropy-methods.pdf`: `3b329b9de395655f00ba358366e49bf5b08d0132060c1b453fa4e69231c05637`

## Final local acceptance and archive binding

**CLEAR / APPROVE.** Final root receipts were inspected directly: 370 tests passed in 8.69 seconds with **95.67%** branch-inclusive source coverage across all 16 numerical modules; the infrastructure run passed 64 tests in 8.26 seconds with **82.91%** branch-inclusive coverage. Required floors remain 90% and 60%. The reviewer independently ran the 64 affected artifact tests and static checks as recorded above.

The rebuilt source archive has 82 entries and contains the exact reviewed repair, documentation, new tests, workflow, manifest and all 16 numerical modules. It excludes private work and external review/verification receipts. The wheel is byte-identical to its previously approved version, and the real isolated-wheel check passed again. The current artifact validator authenticates 48 files, 54 results and five PDF pages.

Every one of the manifest's **16 scientific output records** was independently compared with the initial public Git commit: all bytes are unchanged. The 16 numerical module hashes and PDF hash are also unchanged. Only the synthetic replay policy, its tests/documentation, the targeted workflow invocation and provenance/verification records change.

This is approval of the exact local correction and archive bindings below. The initial hosted failure remains part of the record. **A successful corrected hosted CI run has not yet been observed or claimed.** Commit/push and subsequent hosted acceptance are separate steps outside this reviewer's actions.

Final artifact and verification identities:
- `output/provenance/manifest.json`: `77fcb285afd720c41a5d5b41cd9247841ea4a1ebd057c71b243db79ba7a7c654`
- `dist/antropy_hd-0.1.0-py3-none-any.whl`: `3a902f5eaa4100c84313e24936a7f72467a8431a79594c83a7224050baae6a78`
- `dist/antropy_hd-0.1.0.tar.gz`: `080852a115d174efe68b34a936879021ce8d505feeb374b29917f4a8cddedab6`
- `output/reports/verification/archive-roundoff.json`: `46dc1b7a7d6c878c1e200b26142dd2d7cd545c0902beee7968874cc9d431ae26`
- `output/reports/verification/source-coverage-roundoff.json`: `af7c6dfd1f396666e42512d2ed67fff5023d776110420276078d039e26226bab`
- `output/reports/verification/infrastructure-coverage-roundoff.json`: `3cbff1d922240f560b95072dafbae7db4df663f439baf3b5a12b837f669c3b04`
- `output/reports/verification/source-tests-roundoff.log`: `dfe864fab0fb5c893976c1cbeb5674e2743a7e4e4f57423f86153d407c200c84`
- `output/reports/verification/infrastructure-tests-roundoff.log`: `77a5feac700dfc3bf04693fa3798d1bf73098c7845ade6a56a1254581aecc304`
- `output/reports/verification/wheel-roundoff.log`: `6c79feb9b24e5f51cfcdc3e6e38388669fac7ea7465843ba14a7816f33a5d279`
- `output/reports/verification/artifacts-roundoff.log`: `9f27f8522bb03528846560e43a1752a7520172adca04dfda6b4c3b2ea3fe2f76`

## Final staged-byte confirmation

Independently read the real Git index after explicit staging. The staged manifest equals its disk version. All **48** staged manifest records equal their disk files and match the declared byte counts and SHA-256 values. The staged repair source, test, documentation and workflow also equal their reviewed disk bytes; the rebuilt source archive contains those same staged bytes and staged manifest. `git diff --cached --check` passed. This confirms local publication-byte custody for the correction; it does not claim a successful corrected hosted run. The final report itself must be re-staged after this append.
