# Independent antropy 0.2.0 publication review

**codeQualityStatus: CLEAR**  
**recommendation: APPROVE — local final gate**  
**blockers: none**

The reviewer authored none of the implementation, tests, scientific records, figures or manuscript. This review covers the expanded methods, replicated study, computational planning and benchmarks, actual template rendering, final PDF/figures, and distribution artifacts. No commit or push was performed by the reviewer. Hosted CI for this new revision remains pending; local acceptance does not assert hosted success or external scientific validation.

## Findings and resolved defects

CRITICAL: none remaining. HIGH: none remaining. MEDIUM: none remaining. LOW: no required correction.

Earlier candidates failed this review for touching numeric table columns, overlapping figure-axis labels, a clipped verification hash, and a documented standalone validator with an omitted dependency. Those failures were retained in the private audit chain. The current artifacts resolve them. The actual clipped candidate's native compiler log is rejected by the new overflow guard; final compiler diagnostics contain no Overfull records. The standalone PEP723 environment now includes the pinned template dependency, and both its help command and complete validation pass.

## Scientific and source review

The study implements the declared Bernoulli-replacement MIX construction with explicit one-based phase, independent generated trials and shared random masks/replacement values across mixing probabilities within a trial. Eighteen independent coordinate-wise math.sin and nested-mask checks passed across the three configured shapes. It preserves all 1,650 outcomes from 150 fields: 1,528 finite, 105 undefined and 17 infinite. Means and sample SD condition on finite trials while retaining every outcome count; no pair-level independence or universal monotonicity claim is inferred. The retained 54-result baseline is separate.

The expanded numerical review included 192 focused tests; 60 high-precision Decimal weighted Jensen-Shannon oracle cases; fixed-alphabet endpoint and normalization checks; and 34 actual memory-boundary executions across the nine planned estimators, plus invalid-DDOF controls. The five previously approved numerical-module hashes remain unchanged. Planning separates scheduled distance work, eligible pairs and conservative controlled workspace from timings and process RSS. The 18 measured shape/block cases retain actual inputs, repeated timings and platform identity.

The pipeline review independently ran 122 tests using real numerical arrays, files, subprocesses, and native-renderer fixtures. Negative controls include missing/duplicate trials, changed estimates, transformed-input corruption, boolean/integer confusion, duplicate CSV headers, rehashed manuscript text and altered renderer provenance. Discrete evidence/configuration remains exact; declared finite floating replay tolerances do not relax byte custody. Programming and remove-ai-slops skill perspectives were consulted: no remaining tautological/removal-only test or unnecessary production parsing finding. Parsing at configuration and artifact boundaries is appropriate here. No mocking was introduced or relied upon.

## Final executable evidence

The complete producer receipts were inspected on disk: **613 tests passed**, source branch-inclusive coverage **95.64917127071823%**; the separate infrastructure run reports **196 tests passed**, coverage **88.49591916051303%**. Coverage inventories/counts were independently recomputed using the validating consumer and satisfy the 90%/60% floors. Ruff, formatting, strict type and programming-check receipts pass. These full-suite counts are producer receipts; the independent 122-test execution and oracle checks above are separately attributable.

The actual installed template is `docxology/template` revision `d39f2478da2512b42ad961e98a5f3b854723f92e`. Authentication independently checked 830 installed Python/Lua files and the renderer receipt. Pandoc, pandoc-crossref, XeLaTeX and BibTeX were invoked. The manuscript uses the native PDFRenderer and substitution pipeline, with resolved sections, bibliography, TeX, TOC, compiler diagnostics and provenance retained.

`TMPDIR="$PWD/work/test-tmp" uv run scripts/validate_artifacts.py` completed successfully in its standalone dependency environment: **297 authenticated files, 54 baseline rows, 23 PDF pages**. Its publication validation also replays the complete study and benchmark records.

## Physical manuscript and figure QA

All 23 final physical PDF pages are accepted. Every page was independently rasterized. Thirteen changed pages (2, 11–19, 21–23) were visually inspected again; the other ten raster files match individually inspected candidate-2 PASS pages byte for byte. The repaired page-21 receipt block is fully readable. Tables, equations, captions, figure labels, references and TOC are legible without clipping. Twenty-six native outline destinations were inspected, including the changed related-results section and reproducibility/conclusion pages.

All eight PNG figures were physically inspected and their final bytes match those approved images. The cost and entropy-complexity axis labels have clear separation. Degeneracy explicitly identifies native HDSE; mean/SD plots retain missing outcomes and correct trial-level interpretation.

## Package authentication

The wheel contains 19 Python modules plus `py.typed`, all identical to current source. The source archive contains 392 members and every one of the 297 manifest records with exact length and SHA-256. It retains the configured test/coverage producers needed to reproduce the quantified manuscript, as well as examples, typings, plans and manuscript sources. It excludes private work, virtual environments, reviews and circular archive/wheel attestations.

An independent unpacked-source validation imported the extracted scripts and extracted `antropy_hd` (import location asserted), using the authenticated installed dependency environment. It passed with 297 authenticated files, 54 baseline rows and 23 pages, including full study/benchmark replay. The isolated installed-wheel receipt also reports successful 0.2.0 CLI and analytical checks. Archive hashes below bind this acceptance; rebuilding requires checking new archive bytes.

## Exact final artifact hashes

| File | SHA-256 |
| --- | --- |
| `output/pdf/antropy-methods.pdf` | `f224e5ac55db0ca69f7a58ba5e85c4015db5d1f46a6de9e8446ee2d76f82759b` |
| `output/provenance/manifest.json` | `64bd5fbe80830237f732b283fff9342efa0a8e33275e2c2a85d1016080cd7af3` |
| `output/provenance/manuscript-template.json` | `e389b3f4aac9ac58081381bd2560e04fbdb60417a402cd43dfab9b206badce73` |
| `output/study/report.json` | `e77af9a7e5a55ddca73d9f779e55cf5e715d60e77b0fadd7c93f91f409f425be` |
| `output/study/results.csv` | `493fd105d2410a1ac66c3bcf75e2a0313dc69e7b6ccd58625508454cc3ae57ce` |
| `output/study/summary.json` | `606c4438bd282bb4cb29036486e957fcc70063c8851d7ec3629f4564b919436b` |
| `output/study/complexity.json` | `bef41c11e6b57f7a867e39cd00728a8182ea1ce84b071a4dd2c5859dc4d10972` |
| `output/study/benchmark.json` | `71df577cef9d2bc18872fdc3a408a770f696ad56e251f83374c2799c63c6d1b2` |
| `output/manuscript/rendered.log` | `dbb996c0fa8f622bb76aa2c4a0b9c40a8a44f7bb952ceaa0540d37d43e4b557f` |
| `output/figures/hdse-tolerance.png` | `0a50e08c3971a0f35e4a78cc70d86451cb2a4ec9d0465edb34da1de5994760bf` |
| `output/study/figures/cost-scaling.png` | `44b0ffca629e8edb8901cb8c30a6338e25d9c9f96af62dbc3dab9e69508d2fde` |
| `output/study/figures/degeneracy.png` | `b6480c88f29536fa331d270c2aa5a350c75537fa0d3e849f8747700aab873ad7` |
| `output/study/figures/entropy-complexity.png` | `36ce9eff11d9a69e5accda8ad2b680655e534232a0dd948f644ba317cc856e96` |
| `output/study/figures/input-fields.png` | `e675d45bc690c8dca14befa6fe14ab8269104cdf14207b67ee42d68f277f6374` |
| `output/study/figures/match-probability.png` | `3c729892c715d24c6f29ea3be4aedf8a61ff8861ce3a67ef8e7f2e8023e611db` |
| `output/study/figures/mix-entropy.png` | `e162d69b6e8c5997a2752fdb38174c580f235de5cd1ede133f1508aa3de1ae30` |
| `output/study/figures/native-v-flattened.png` | `51ec02ba8b2869dd559e933f6f357de63cb0d331a03f43893ab0ba2ec43d1d90` |
| `dist/.gitignore` | `684888c0ebb17f374298b65ee2807526c066094c701bcc7ebbe1c1095f494fc1` |
| `dist/antropy_hd-0.2.0-py3-none-any.whl` | `3d624c7543a993e301a2728dac5c649d7bd6a1c96abc991257c004fe8fec3690` |
| `dist/antropy_hd-0.2.0.tar.gz` | `fc391bad2b671d7f55d2ac6fa3a4049cc6754e5ae688f67b5bacd7211f33c3ab` |

## Verification receipt hashes

| File | SHA-256 |
| --- | --- |
| `output/reports/verification/source-tests-improved.log` | `22b78552a93712b0018ed744b6519438fab29689ca6750dfb4a9186ae7cfee4c` |
| `output/reports/verification/source-coverage-improved.json` | `482700cb812cba4b713afe1e47d1cadec4474b26c3ba8a9cc0631ba283e9987f` |
| `output/reports/verification/infrastructure-tests-improved.log` | `fe83d975d5a7ee06ed5647e3c7699532e95775c21da382cbd12cb445e960d365` |
| `output/reports/verification/infrastructure-coverage-improved.json` | `c3febbc9fb7a4ef63c2eda9cda2e8704f959960802a1597b5dad59cffcc352a5` |
| `output/reports/verification/lint-improved.log` | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| `output/reports/verification/format-improved.log` | `b1589e558de12a68704dd4a8223f2d36ac6a88906f2ee6989c0778b550734808` |
| `output/reports/verification/types-improved.log` | `56882e01cb80173ef053c4096e4ee43e3123a15f5c0a06715f96988d48fbd91c` |
| `output/reports/verification/types-last-changed-improved.log` | `56882e01cb80173ef053c4096e4ee43e3123a15f5c0a06715f96988d48fbd91c` |
| `output/reports/verification/programming-improved.log` | `1befffedebba6b5276be2335c7db1be5a53a1b50a23706ff295c5d118399522d` |
| `output/reports/verification/wheel-improved.log` | `d523818c654bd87e18cf93048d3ad4942d648885366568d6511e9c0d1a95bfc8` |

## Reviewed source and configuration hashes

| File | SHA-256 |
| --- | --- |
| `src/antropy_hd/__init__.py` | `b8a85d9d70060d861ea9523a513b6eeef11445cbebc45ca7e25b55b9fcef9fa4` |
| `src/antropy_hd/_complexity.py` | `a34751f872cab671b101143a08672678d6bdd7861e7c8bb4af0743b8a33479e4` |
| `src/antropy_hd/_information.py` | `1afb6b4c93dacff30f4a99fee29b845be973ce2cbfa727ce8e90e29af37d5a30` |
| `src/antropy_hd/cli.py` | `df29d3c9f4aea2c787f37af9bcf0afce10f8b46b21643f9b67ad85373fda5553` |
| `src/antropy_hd/complexity.py` | `bc4a08559369a01869d4b79d3bb70442aeb5b76e5551bced9d043fe5809d0032` |
| `src/antropy_hd/distribution.py` | `eec35022be9c3899f72003e9cc6966d2c905b23f05687dcac6fbe3fb1cde3c9e` |
| `src/antropy_hd/embedding.py` | `efbf0577a94e05307c9b36489f5417beed9bf89ad2921f0871576a186432cc59` |
| `src/antropy_hd/errors.py` | `ade6011198cac7686baab6c6ed037b0adfdc63516123e146a7e97b21a396ed30` |
| `src/antropy_hd/fuzzy.py` | `9d6e3c2c5760d3844492f4734215a42df3bd09d5c825ff1d607f7794b557a4a2` |
| `src/antropy_hd/information.py` | `38001718c534dbe9e46e1bd106957f776a7f0f0266e0ae2cd0a36c4ceb9a5a9e` |
| `src/antropy_hd/models.py` | `f362a6b986875ab39f3c123ac679bb38f8f0543f472c0a07d13a53c7d6bd9587` |
| `src/antropy_hd/multiscale.py` | `7d69b9c44f38e7660298497027fa72e9c4520823e43c4cb69c9d370e2f039e95` |
| `src/antropy_hd/orchestration.py` | `858d9932d07f728981400f52365be43ffaf42e49d8490206687084d20a819d2d` |
| `src/antropy_hd/ordinal.py` | `aad40673c0048e623e8d2cfe2cbdd461834bedf7ef7547c4708c24c9a24decdd` |
| `src/antropy_hd/pairs.py` | `b17ad2c1468c407338016843efab3c80782486ac7f7837f95e602beadf05e7f3` |
| `src/antropy_hd/spectral.py` | `09ada6722b7ae4b8d8767a91d595262c0ed1f091645318f6407e416f8eb566ae` |
| `src/antropy_hd/statistical.py` | `9f6229c61bfaa7e303a3486203e484dfb539dcd64aac3d62cd92c5f3369a02b9` |
| `src/antropy_hd/template_entropy.py` | `73593b7e56cbeb7c011450e8e7cf721154ca78df5ab43326bc32d2888c55163d` |
| `src/antropy_hd/validation.py` | `1c276f661c3b5ec43c35c3b64519061bc37ff5c4960d4f9fec7040c7e4b3f91f` |
| `scripts/__init__.py` | `29d59ad3721c0b8aeae506a1fe081af727107eeee04effa6a477256e14ff56a1` |
| `scripts/artifact_io.py` | `51c09da958b986b395eaeb57bdc592315599b8fff481b728abe34aa92afbed98` |
| `scripts/artifact_models.py` | `8c292ed5a0609c0f0519bed9bb965a9ff9c0b636505cc193810a136b15451cb5` |
| `scripts/benchmark_complexity.py` | `f3587c979d1526c67378d81f4a9bbb4018d45b81326f43de497b88100ce6f4e9` |
| `scripts/benchmark_models.py` | `7d11d00cf19f1eeb0c657b0b3e7e8bd1016a54ddf1cdb3310e7a89cc61c43d03` |
| `scripts/benchmark_plots.py` | `d6be0a07303e73bae37161e8103bb60a40af2190fcfd08426b9aec7ecc624d7f` |
| `scripts/build_manuscript.py` | `888e9abb6cde9f877c7f7d34e269c48c4f129441ea88078aea77c4eb2b832168` |
| `scripts/check_installed_wheel.py` | `3ad5662e6bfdae9735a803a6e6c5982670d4e73363270896bd4968555d93043a` |
| `scripts/manuscript_claims.py` | `ff9759e8179a44aef5f153c3967ea61e0e430b4c1123177b84810416231a9915` |
| `scripts/manuscript_data.py` | `e0b559bae45cb4638b1674d88f9c0e00923705337fd34fb2aab6029ffecb4f7c` |
| `scripts/manuscript_hydration.py` | `e218b723c08c995c716c821597f23100a3a816bebb6eeaf476fb849f8ac12778` |
| `scripts/manuscript_profile.py` | `ceb2882e28f3d13845eebacfdde996b2a4a2bd31035cfba45fa5ab075236ae17` |
| `scripts/manuscript_tables.py` | `31287d969336895ef6790ac4a703d5b65e16f9c952c52918251f9cb0fb1e38b1` |
| `scripts/manuscript_variables.py` | `14cf361db3743c42cc7b933857a4396b2c1314eac52a136ae7786b975d56dac3` |
| `scripts/manuscript_verification.py` | `f6bbe6e16d0352e8e400bf68100c1fb0b2a9f2739b584594941cd0b8f90d8c1b` |
| `scripts/plot_experiments.py` | `2fc5ae787198db71026a6050434362b196256738a0c697322e4c898f94a837c8` |
| `scripts/render_manuscript.py` | `86462e33b9524665c48529cba78b4363152f1e30aadc01b07f743a1f2c42eb14` |
| `scripts/result_replay.py` | `125ac571f7ce9dd6be0533ee7cdae6bffe56fd0bf2faa1d4adcb44b1573a8e5f` |
| `scripts/run_experiments.py` | `fec7a284989a6ca1b2df84bce6d31ecc5d0767f8d09f430ffa4ec10bbb4f6e7a` |
| `scripts/run_study.py` | `17f9a2ca6f5dfbc33ef124bb40d29a13f4ea92a54dcf5d1d6eec0fcc7ab9fa09` |
| `scripts/study_analysis.py` | `8c142c6a54695288fd5f6003efe28b44087f584d5397910a609a483b2cc3b20d` |
| `scripts/study_diagnostics.py` | `9d60486504d737317ad5a105e2956ab07128609c49582d213cd1a528a5e4b54f` |
| `scripts/study_fields.py` | `6998a1eca5b88eaf397474c01f4e26028357f73a2583a67998283bb0efe8a648` |
| `scripts/study_models.py` | `96ee51dddd24230d8ed2b2a6d5fff336bbc72b02817219dac7f9a62c34dd7aea` |
| `scripts/study_plot_helpers.py` | `a834ab4f82d8518c39d04aec9c669981d8909caf9e060ca50fb584ab9ce59adb` |
| `scripts/study_plots.py` | `63872acff0b12db4dc7f8aa0d7f703c1a1e29d2f1c94ef091123f8fa8414a740` |
| `scripts/template_provenance.py` | `42e27931dc23648ba3ea3e5d9cacef489ae4fc5d2ae1b467a191d1f12f47ce42` |
| `scripts/validate_artifacts.py` | `760ee7a65af9c3122e3f97d1c951eefacfe941cd56d3287bf0cb3dcb4673e7a0` |
| `scripts/validate_benchmarks.py` | `9d8ea9b6222636a32c56c564c22cf111ddc5350e43c9a81916d167a920d6844f` |
| `scripts/validate_publication.py` | `8ae4536e71fbab3a1f565261eb6036127794413b029a3a058144f2c32c203233` |
| `scripts/validate_study.py` | `25a900fdd34c8c50e417a9f0217f64f8954ac03bc8ff152799c468027dcbe23a` |
| `pyproject.toml` | `4d0f37671e3873bdf69744a8a57e7c7d07d83fa6668b2fe00fa9b02b1a3574a3` |
| `.github/workflows/verify.yml` | `359c6dd213c656c2a4c01c228e015af60ebbcbb217c45e657ec1445e15d41228` |
| `study_plan.yaml` | `ab255a25cd468a4753889b1e2d522299e5e81933b7b9cc58a7243bc0d61cd1a6` |
| `benchmark_plan.yaml` | `0bd923ce5f704e3d01bff96e7671e97d1226cfe44656973c9146b8423697403f` |

## Final archive transport amendment

The source archive was rebuilt after narrowly scoped Git attributes preserved raw verification-log padding and Markdown hard breaks. Independent inspection verified all297 manifested records against archive bytes, current files and the real Git index. The final archive has392 members; private work/virtual environments/reviews remain excluded. Relative to the previously accepted archive, changed bytes are limited to `.gitattributes` and completion of `artifacts-improved.log`; the additional member is `standalone-validator-improved.log`. These two logs record the successful297-file/54-row/23-page validation and do not alter scientific inputs or selected manuscript verification producers.

The final `.gitattributes` SHA-256 is `e85b58ebe31a3d9ab0dc15791db75cfcad8609ec7f7144bb8710b4930a7521f5`. The PDF, manifest, wheel, source modules, figures and scientific records are byte-identical to the accepted candidate. Local approval therefore remains CLEAR / APPROVE for the rebound archive `fc391bad2b671d7f55d2ac6fa3a4049cc6754e5ae688f67b5bacd7211f33c3ab`; hosted CI remains pending.
