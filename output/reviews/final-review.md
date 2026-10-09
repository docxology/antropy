# Independent final review — antropy-hd 0.1.0

Review date: 2026-10-09

- codeQualityStatus: **CLEAR**
- recommendation: **APPROVE**
- blockers: **None**

This review covers the exact local source, tests, configuration, built distributions and generated manuscript artifacts identified below. The reviewer did not implement the reviewed code or author its tests. Approval covers the checked software and computational methods report; it does not establish empirical replication, biological validity, or hosted CI completion.

## Findings by severity

- **CRITICAL:** None remaining.
- **HIGH:** None remaining.
- **MEDIUM:** None remaining.
- **LOW:** No unresolved acceptance issue. Figure annotations are compact at print size; the full result table separately records every nonfinite status.

Earlier review findings were reproduced before repair and independently checked afterward. Repairs addressed simultaneous template/pair/histogram workspace accounting, pre-allocation resource rejection, stable radius arithmetic, translation precision in fuzzy/weighted-ordinal/demeaned spectral and SVD methods, explicit fuzzy numerical-range errors, and final-package byte identity. Failed receipts remain in the private review history; they were not relabeled as successful runs.

## Scope and scientific contract

Reviewed all 16 numerical/package modules, static method dispatch, file-loading and JSON boundaries, research scripts, tests, packaging, workflow and method documentation. The supplied Xia–Wang paper's section 2 and equations (1)–(6) were compared with native-dimensional embedding, common origins, strict Chebyshev matching, global SD and pair-count normalization. The paper's tuple-versus-coordinate exclusion ambiguity is explicitly documented. Rectangular windows, alternative norms, delay/stride, selected extension axes and related spatial estimators are labeled extensions.

The manuscript identifies synthetic demonstrations and does not claim replication of source-paper empirical experiments or new biological findings. Method references and precise estimator conventions are present. Numerical workspace limits exclude caller-owned arrays, preprocessing and process RSS, as documented; conservative limits can reject requests that might fit a particular runtime.

## Independent verification

| Check | Observed result |
|---|---|
| Full frozen-source suite | **354 passed**, independently rerun in 6.29 s |
| Authoritative source coverage run | **354 passed**, 39.49 s; **95.67%** branch-inclusive coverage over all 16 modules, including `fuzzy.py`; required floor 90% |
| Authoritative infrastructure coverage | **48 passed**, 39.49 s; **82.28%** branch-inclusive coverage; required floor 60% |
| Ruff | Passed |
| Formatting | 49 files already formatted |
| Strict basedpyright | 0 errors, 0 warnings, 0 notes |
| Real CLI method matrix | All **18 registered methods** exercised through real subprocesses and NPY files; exact API-result and input-byte provenance agreement |
| Installed final wheel | Passed isolated-environment import, analytical Shannon result, CLI methods/version and input-file hash checks |
| Wheel and source archive custody | Every one of 16 source modules byte-identical to the reviewed checkout; wheel includes `py.typed`; source archive excludes work directories, private reviews, virtual environments and caches |
| Artifact validator | **48 authenticated files, 54 result rows, 5 PDF pages** |
| Exact experiment replay | Independently reran all **9 field batches / 54 complete result objects**; exact stored JSON agreement including values, statuses, counts, configurations and provenance |

Coverage JSON and final logs under `output/reports/verification/` were inspected directly. The final coverage report includes the extracted fuzzy module; an older coverage report that omitted it was rejected as stale evidence. An older wheel that passed a narrow CLI smoke test but differed from reviewed source was also rejected. The final distributions below passed both byte comparison and functional verification.

Commands used included:

```sh
uv run ruff check .
uv run ruff format --check .
uv run basedpyright
TMPDIR="$PWD/work/test-tmp" uv run pytest -q
TMPDIR="$PWD/work/test-tmp" uv run python scripts/check_installed_wheel.py --wheel dist/antropy_hd-0.1.0-py3-none-any.whl
TMPDIR="$PWD/work/test-tmp" uv run python scripts/validate_artifacts.py
```

The repository-local temporary directory avoided an independently observed system temporary-volume capacity failure. Tests still used real files, subprocesses and isolated environments; no mocks or skipped checks substituted for the failing environment.

Additional reviewer-owned numerical checks used direct formulas and explicit coordinate enumeration rather than production embedding/FFT helpers:

- 60 HDSE pair-count comparisons spanning dimensions 1–5, all three metrics, both exclusion conventions, strict/closed thresholds, delay, stride, selected axes and Theiler exclusions.
- Direct separate-population ApEn, centered/uncentered fuzzy membership sums, and block-mean coarse graining.
- Shannon/Renyi/Tsallis checks across probability alphabet sizes 2–11 and multiple orders, plus direct conditional-entropy and mutual-information sums.
- Direct Fourier sums in dimensions 1–3, direct ordinal/weighted spatial motifs in dimensions 1–4, and analytic diagonal singular-value examples of sizes 2–8.
- Constant/no-match/no-eligible-pair cases, exact threshold boundaries, extreme finite amplitudes, translated nearby large floats, tiny/huge tolerances, and deliberately invalid resource budgets.

## Test relevance and maintainability perspectives

The `programming` and `remove-ai-slops` skills, including the Python reference, were explicitly consulted. Reviewed tests observe numerical results, routing/file behavior, or genuine adversarial rejection. No remaining deletion-only, tautological, implementation-constant-mirroring or brittle prose test finding was identified. Artifact-removal controls test required-file rejection, not a requested source-code deletion. Boundary parsing and numerical normalization serve the declared input and estimator contracts. Modules remain focused; the fuzzy extraction preserves public imports. No unresolved material violation of either review perspective remains.

## Manuscript visual review

The actual five-page PDF was rasterized with Poppler and every physical page was inspected:

1. Title, author, abstract, motivation and HDSE conventions.
2. Related estimator definitions, implementation and experiment design.
3. Complete 27-row HDSE table, including finite, undefined and infinite states.
4. Three-panel figure, legend, provenance, limitations and beginning of references.
5. Remaining references.

No clipped text, overlapping objects, missing glyphs, cut tables or footer defects were observed. The figure uses an external legend and common configured tolerance positions. Its nonfinite annotations agree with the table. The PDF hash was unchanged before and after visual inspection.

## Exact reviewed artifacts

- `dist/antropy_hd-0.1.0-py3-none-any.whl`: `3a902f5eaa4100c84313e24936a7f72467a8431a79594c83a7224050baae6a78`
- `dist/antropy_hd-0.1.0.tar.gz`: `4dd1298801bc644bde19f0744a63cd6289d5dd983ccced74fdc91c88afb6a6ef`
- `output/pdf/antropy-methods.pdf`: `3b329b9de395655f00ba358366e49bf5b08d0132060c1b453fa4e69231c05637`
- `output/provenance/manifest.json`: `593f7df03ed97685d92a71225dc0f7edcc9e83d78b6045e6a4b943e532a0ddbd`
- `output/data/results.csv`: `a4104429035874774f07cb2ec816a1cd656504435f245754d730e3bc06526727`
- `output/reports/experiments.json`: `6682b52828a6f8804753a6c10a96daaf8fbc3ccb77e17cc9f81cb7ec55306a3c`
- `output/figures/hdse-tolerance.png`: `0a50e08c3971a0f35e4a78cc70d86451cb2a4ec9d0465edb34da1de5994760bf`
- `output/reports/verification/source-coverage-final.json`: `ed6c6202b839f39f1f9d9910e1540859422bdcf4f135ffd06d747560bdc391b2`
- `output/reports/verification/infrastructure-coverage-final.json`: `ac856ff966f25f947cec6f6d293edb288d79fa390a1a6a53ddae6079da55a318`
- `output/reports/verification/source-tests-final.log`: `e487965d8e062dfb95c48bca3380746155f6566dc78c5c13352b714a7d9b7261`
- `output/reports/verification/infrastructure-tests-final.log`: `3987393a767de5d42ca2454173bb5c7407b04675cebdc13fbdea1fd1762c7d9c`
- `output/reports/verification/build-final.log`: `573fcc538618d0f9f5cea5a28e97472605d3ec98dc19d4cae83564770bb77931`
- `output/reports/verification/wheel-final.log`: `6c79feb9b24e5f51cfcdc3e6e38388669fac7ea7465843ba14a7816f33a5d279`

## Reviewed source and configuration hashes

- `.github/workflows/verify.yml`: `2d8a918ef345cf2461aa589b7c094d458d82eb976133b51e104e4c720060d494`
- `AGENTS.md`: `e4f78aeeeea60f61d6c52a51a67c00cd30b1435397114540b061134561f1852b`
- `README.md`: `712c0ac28a5ceea7ccff08e74715bcc456b9c60e868d548b7d2026912a24cadb`
- `docs/configuration.md`: `b3f4ef794960d70238ad74ffbce5df64ff47af930375c7db7f63ccae7aaf51c1`
- `docs/implementation-contract.md`: `68072d2db9a40a8818833e1f118206d2fba9e999273698d8061ae7ebbd4b2a08`
- `docs/manuscript/claims.json`: `5b9f546091c0fa3e7a8d5917d1df1586cfe1d33a56580918bb14767f0df7edcb`
- `docs/manuscript/manuscript.md`: `3f24e7d97a33ce7871d84525291e6f84cb4855f3979bf3ffa2f25167a90c44a2`
- `docs/manuscript/template.md`: `2f1a58b7a2f0e355864e6f4fda1fa749e2382e0fd09ef4eca6cd0a60d2210fcd`
- `docs/reproducibility.md`: `0e782414618bbd6a9a683c835ad3d2ca1fce9ca74e6ea6552aded6d7e38de864`
- `docs/sources-related.md`: `f0c60bb2024213a21b1fa4d453cc0e010c1c9a4569a95e57b8be261a4bb2d7c6`
- `docs/template-adaptation.md`: `fc4ff5c2c0269b385f6affaab0ca8e74141e00179f849411a5f5b1cfebfd4ffe`
- `domain_profile.yaml`: `61f800b1729f45af092945f776ae9d3060ae8576e95dda3cb1c179e8a9ddae0e`
- `experiment_plan.yaml`: `23b82aabbbbfa4dbbc1c3362dbff95d9f3d9f081f7f678a92091736938fe078e`
- `pyproject.toml`: `93b91e9010d051c98d97439c881609a507ce101798bf606f52e59257c8af728a`
- `scripts/__init__.py`: `29d59ad3721c0b8aeae506a1fe081af727107eeee04effa6a477256e14ff56a1`
- `scripts/artifact_io.py`: `765d3251031e30247dd1bd4ecc064fb9f8a01972eb6278f412b9ad4dcfba301b`
- `scripts/artifact_models.py`: `8c292ed5a0609c0f0519bed9bb965a9ff9c0b636505cc193810a136b15451cb5`
- `scripts/build_manuscript.py`: `7a980f46522710f8e601500b8ea82da75049089d3fc805322899dfce7fcb5233`
- `scripts/check_installed_wheel.py`: `acdcfe2c2efd221d4df68702db9b93ff0ab750344caa47f9f82b72e1e754a175`
- `scripts/plot_experiments.py`: `2fc5ae787198db71026a6050434362b196256738a0c697322e4c898f94a837c8`
- `scripts/render_manuscript.py`: `986eb5b43456649a8deee4cc93f883f5b226296f295eb9ec21b2b4900782aa51`
- `scripts/run_experiments.py`: `fec7a284989a6ca1b2df84bce6d31ecc5d0767f8d09f430ffa4ec10bbb4f6e7a`
- `scripts/validate_artifacts.py`: `124a2604346ef815584f09f397dce6e204ecebdff35347a2fd8202eb54693d2c`
- `src/antropy_hd/__init__.py`: `0e8a18e0b262b318689900ee83b6be23580d761e74204ebe3acc8747828831ff`
- `src/antropy_hd/_information.py`: `e736b3d602437e0c63d2ff305b07f5ba5512f37257a8487d560eb80f3eefdcad`
- `src/antropy_hd/cli.py`: `a3a18af908dd3be7275f33c7e84fca4f4d2eafb1ddcd0d76ceec22d3d512cea9`
- `src/antropy_hd/distribution.py`: `eec35022be9c3899f72003e9cc6966d2c905b23f05687dcac6fbe3fb1cde3c9e`
- `src/antropy_hd/embedding.py`: `efbf0577a94e05307c9b36489f5417beed9bf89ad2921f0871576a186432cc59`
- `src/antropy_hd/errors.py`: `ade6011198cac7686baab6c6ed037b0adfdc63516123e146a7e97b21a396ed30`
- `src/antropy_hd/fuzzy.py`: `9d6e3c2c5760d3844492f4734215a42df3bd09d5c825ff1d607f7794b557a4a2`
- `src/antropy_hd/information.py`: `7c0bf50e3a1640d1002745c72474f3ea7ae84e2f4523f00cde81016af7dba6d6`
- `src/antropy_hd/models.py`: `f362a6b986875ab39f3c123ac679bb38f8f0543f472c0a07d13a53c7d6bd9587`
- `src/antropy_hd/multiscale.py`: `7d69b9c44f38e7660298497027fa72e9c4520823e43c4cb69c9d370e2f039e95`
- `src/antropy_hd/orchestration.py`: `4268abc9adc9cbd3614165b6b723a09f20b4d5a60d7d770dc5d73a29aeb9a249`
- `src/antropy_hd/ordinal.py`: `aad40673c0048e623e8d2cfe2cbdd461834bedf7ef7547c4708c24c9a24decdd`
- `src/antropy_hd/pairs.py`: `b17ad2c1468c407338016843efab3c80782486ac7f7837f95e602beadf05e7f3`
- `src/antropy_hd/spectral.py`: `09ada6722b7ae4b8d8767a91d595262c0ed1f091645318f6407e416f8eb566ae`
- `src/antropy_hd/template_entropy.py`: `73593b7e56cbeb7c011450e8e7cf721154ca78df5ab43326bc32d2888c55163d`
- `src/antropy_hd/validation.py`: `1c276f661c3b5ec43c35c3b64519061bc37ff5c4960d4f9fec7040c7e4b3f91f`
- `tests/__init__.py`: `ddfe7f429ad17c67aa0415c4b93cf4e5170fb277800aa0f03d8a2f67e781b088`
- `tests/artifact_fixtures.py`: `3667b6bab849f4d9f6fb397edcf52e73850de442826c22f38ddea38710360408`
- `tests/test_artifacts.py`: `13a0391810b2f86b430ce1cf6c9ef19999b143533ede9d072baf3b6874e27899`
- `tests/test_cli.py`: `240bab930598b2460fcfcb7c74ff605ffd93a5b5b744af434215fbc51a5779b0`
- `tests/test_hdse.py`: `6653939b79b4bc9dcb5fafb23aaef18071fbe8ae8c280354720cc3fc1c08503b`
- `tests/test_information.py`: `7bb1fe0db6313dcc92f299872cd8852443202b0118e63dfcccf519f64e179ff8`
- `tests/test_multiscale.py`: `6be99bdc4f2dd9b3baf5ff31d43aab1f1b4a6b2b8021d5a830293b01eabd7dbe`
- `tests/test_orchestration.py`: `ffdb72738d108c1a19c7e1fd062dbbc319c0dcb62428b7294fadc42685f66ee8`
- `tests/test_ordinal.py`: `d6d305f2fcd6373966842a480b2e6f104e5d9bddaddfd0934a4f1050c7c3d59d`
- `tests/test_spectral.py`: `56ac835daf60dff3c8fd0b107520ed26507d3c24f6672e970fe26c380df4493e`
- `tests/test_template_variants.py`: `ec7206f5b9be381e240e67f68ad67a5650409482d3d5a9ada5428a85470474b0`
- `uv.lock`: `0b9898e50ebc1c310c845e68555cf041ad87023301bd068aef2a253820e995de`

## Acceptance limits

This is local technical and bounded manuscript acceptance for the exact bytes above. Exact pair counting remains quadratic; high dimension and low tolerance can make estimates undefined or infinite. These outputs must retain their counts and statuses. The float64 implementation explicitly rejects documented unrepresentable numerical intermediates. No remote push, hosted CI result, package-index publication or application-specific scientific validation is claimed by this report. Changes to reviewed source or generated artifacts require an appropriately scoped recheck.

## Prepublication transport and packaging amendment

Scoped amendment independently approved. Numerical source, tests, scientific results and PDF are unchanged; their prior acceptance remains applicable.

Git attributes preserve CSV bytes without newline conversion and mark PDF/PNG/NPY/NPZ artifacts binary, while ordinary source files retain LF normalization. CSV's standard whitespace checks remain enabled with an explicit carriage-return-at-line-end allowance. Only terminal blank lines changed in `AGENTS.md` and `.python-version`; comparison against the retained earlier archive confirmed identical content after stripping terminal newline bytes.

The source archive now excludes review reports, verification receipts and the pipeline acceptance receipt. Those receipts authenticate the archive externally; including them would create circular or stale archive attestations. The rebuilt source archive contains 81 files, includes the current attributes, project configuration, scientific manifest and all 16 exact reviewed source modules, and excludes private work/cache/receipt directories. The wheel's bytes are unchanged. Focused installed-wheel CLI and artifact validation passed again. A numerical-suite rerun was unnecessary because all 16 reviewed source hashes are unchanged.

The staged Git manifest and all **48** files it names were independently read with `git show :<path>`: every staged byte count and SHA-256 matches the manifest and working file. `git diff --cached --check` passed. This verifies the publication transport bytes, including original CSV line endings and binary artifacts. The archive/configuration/manifest hashes above were updated to the amended accepted artifacts; earlier identities remain in private chronological review receipts.

Additional reviewed transport files:
- `.gitattributes`: `5339ef13d49d5ea022947733cde0a18508136a4d64a6f97d06a91a4570b9a30f`
- `.python-version`: `a876e0b10411037a012498b9fe18d9bc1df32ed8b722a13564dc944ddcfd9135`
