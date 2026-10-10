# Independent numerical inference and prospective power review

- codeQualityStatus: **CLEAR**
- recommendation: **APPROVE**
- Scope verdict: **PASS — reviewed numerical/power source only**
- blockers: **None in this scope**
- Date: 2026-10-09
- Baseline HEAD: `7c29f8ef46623d682308f6659d92cd76184d3d04`

The reviewer authored no production code or tests. The review inspected the new inference, symbolization, CLI comparison, prospective power models, generation, preflight, serialization, summaries and three replay-validation modules, with their numerical and real-file tests. The implementation was initially dirty/untracked against the baseline. Exact reviewed bytes for 33 files are recorded in `.omo/evidence/antropy-power-reviewed-sha256.json`, SHA-256 `66f5f64e83ebd0e9bec9d20f97ffa77cfebdcb9bcc65a6004954f48d58788097`. This includes the builder's final preflight correction.

`omo-agent-toolkit ulw-loop status --json` returned `ULW_LOOP_PLAN_MISSING`; the required fallback report location is used. No notepad path was supplied. The parent supplied scope, expected scientific artifact hashes and claimed focused evidence; those claims were independently checked below.

## Findings by severity

### CRITICAL

None.

### HIGH

None.

### MEDIUM

No open findings. **Closed M1:** `scripts/power_preflight.py:65-80` originally accepted `conditional_entropy` and `mutual_information` with `geometry="symbols"`, although the generated one-dimensional probability vector cannot supply their required proper conditioning-axis partition. The reviewer reproduced preflight acceptance followed by an actual numerical `ParameterError` in `work/reviewer-inference-adversarial.log`. The builder now evaluates the configured probability method on the declared vector geometry during preflight. Independent recheck confirms both methods fail early, the actual published plan's resource estimates are unchanged, and real-run negative controls confirm no output is created. The correction also catches incompatible reference-probability shapes. Evidence: `work/reviewer-preflight-fix.log`, `work/reviewer-inference-r2-tests.log`.

### LOW

None requiring changes.

## Independent verification

- **228 focused tests PASS** after the final correction, including exact/Monte Carlo tails, paired bootstrap, Wilson intervals, Holm adjustment, invalid/extreme data, immutable settings, CLI file custody, fixed alphabets, model contracts, actual execution and coherently corrupted artifacts. Command: `uv run pytest tests/test_inference.py tests/test_inference_intervals.py tests/test_inference_validation.py tests/test_symbolization.py tests/test_cli_inference.py tests/test_power_execution.py tests/test_power_models.py tests/test_power_tensor_validation.py tests/test_power_validation.py --no-cov --basetemp=work/reviewer-inference-r2-pytest`. Log: `work/reviewer-inference-r2-tests.log`. This is a focused test result, not an independently measured whole-project coverage claim.
- **120 additional independent exact enumeration cases PASS**, using `fractions.Fraction` means and explicit subset complements rather than production contrast arithmetic. Cases include unequal group sizes, nextafter near ties, tiny values and large mixed scales. Log: `work/reviewer-inference-adversarial.log`. Its subsequent rejected-method findings are preserved as pre-fix evidence.
- **Independent null smoke simulations:** 25/500 rejections for independent exact tests and 11/500 for paired exact tests with six observations/pairs, under independently generated identical normal distributions. The paired test is conservative because of its attainable two-sided p-value grid. These are bounded checks, not a general calibration proof. An explicit Holm reference vector and constant paired-difference bootstrap also passed. Log: `work/reviewer-null-calibration.log`.
- **Actual complete power replay PASS:** 18,432 retained field estimates, 6,912 decisions and 108 summary cells. Log: `work/reviewer-power-replay.log`. Report SHA-256: `1e4ff2f8b8a38d3c29916d3d6f905ffb3ebbf240c2f0adfaa6526f2b1b1fb301`; plan SHA-256: `de602e182e541b4a64956b1dc30b661c29ac4f2f4b742a9695de245c80fb2914`. Full replay ran before the preflight-only correction; the final correction was independently checked against the same complete report's resource record and the full focused suite rerun.
- Targeted source/helper `basedpyright`: **0 errors, 0 warnings, 0 notes** (`work/reviewer-inference-types.log`); final changed preflight check likewise clean (`work/reviewer-preflight-types.log`). Targeted no-excuse checker returned no violations across the seven core numerical/preflight/orchestration files checked. Scoped tracked diff whitespace check passed.

All tests use the project's `uv` environment and isolated external temporary directories. No production files, tests, retained scientific outputs or historical receipts were edited by the reviewer.

## Correctness and scientific scope assessment

Exact tails compare rational representations of binary64 observations inclusively. Exact enumeration includes the observed allocation; Monte Carlo draws are uniform with replacement and use `(extreme+1)/(draws+1)`. Independent tests state exchangeability of complete observations; paired tests state within-pair label exchangeability. The reported resolution is a grid increment rather than a promise that every multiple is attainable.

Power observations are complete fields. The null groups use separate RNG namespaces, outer repetitions are independent, and prefix reuse across sample sizes is explicitly documented as correlating curve points. The inner seed is consumed separately from field generation. Inference never treats grid cells as independent subjects. The fixed Holm family retains unavailable methods as conservative bookkeeping p-values of one while preserving null actual results and nonrejection. Summaries retain attempted/available/unavailable/rejected counts, distinguish conditional and unconditional rejection, and label the missing-decision range separately from Wilson uncertainty.

Preflight checks bound field counts, distance-component work, inference work and pool-array bytes. These are explicitly not process RSS or runtime promises. Serialized report size is checked after construction and before publication; failure preserves generated pool evidence. Replay verifies the declared design matrix, seeded field construction, actual kernels, complete tests/family adjustment, denominators, intervals and canonical CSV projections. Real-file negative controls demonstrate that coherent rehashing or CSV updates cannot conceal changed scientific records.

## Skill-perspective check

The **remove-ai-slops** and **programming** skills were explicitly loaded and consulted, including the Python reference. The overfit/slop pass examined production boundaries and numerical/real-file tests. No deletion-only tests, requested-removal assertions, brittle prose tests, tautological-only tests or tests merely pinning implementation constants were found. Independent fraction oracles and manually specified alphabet counts provide substantive expected outcomes. CLI equality checks appropriately test integration with separately tested numerical kernels. Assertions that failed runs create no outputs exercise an observable failure contract, rather than testing source deletion.

Parsing and normalization are confined to genuine configuration/file boundaries; strict JSON duplicate/nonfinite rejection and replay are required by this scientific artifact-custody goal. No untyped escape hatch or needless production abstraction requiring correction was identified. Dynamic maps keyed by declared analysis identities carry typed values. No material violation of either skill perspective remains in the reviewed scope.

## Approval boundary

This report approves the bounded numerical/power source revision and its focused evidence. It does **not** approve final manuscript prose, physical PDF pages, figure appearance, template integration, full-project coverage, built archives, installed-wheel behavior, hosted CI, a commit, or publication. Those release gates remain with the parent task and its separately scoped independent final review.

Graft was attempted once and answered from the enclosing vault index with unrelated results; direct source inspection was therefore used. Its reported saving was approximately 416 tokens; this does not imply the antropy checkout itself was indexed.
