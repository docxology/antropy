# antropy 0.3 physical publication QA

**Verdict: PASS — bounded to the physical PDF and structural checks below.**

Audit date: 2026-10-09. Independent read-only QA executor; no production source, tests, figures or PDF were edited. The caller assigned this review separately from construction. No ulw-loop plan exists (`ULW_LOOP_PLAN_MISSING`); the caller evidence directory `.omo/evidence` is used.

Authenticated bytes:

- PDF `output/pdf/antropy-methods.pdf`: SHA-256 `eef54c520ec2f7ba67835fa6dee6748532b4ff089857338e5924d73ce774b4a0`, 1,817,939 bytes, 48 A4 physical pages.
- Manifest `output/provenance/manifest.json`: SHA-256 `84e22e9327cfd956de223082b2c79c313b6fba405e33c8a0febcaf5420be050b`, 1,498 artifact records.
- Metadata title and author agree with the visible title page. Native outline has 11 top-level sections, 32 linked TOC destinations resolve to the observed section pages. Printed body numbering is physical page minus one; title page is unnumbered.

## manualQa

Criteria: C1 complete physical rendering; C2 native TOC/metadata/section structure; C3 complete configured figures/captions/units; C4 dense tables and nonfinite states legible; C5 resolved equations/citations/provenance; C6 real malformed-input rejection and byte identity.

### surfaceEvidence

All commands ran from the antropy repository root. Each surface and invocation was declared before execution. `view_image` below means the actual filesystem image tool, not text extraction.

| Scenario | Criterion | Surface | Exact invocation | Verdict | artifactRefs |
|---|---|---|---|---|---|
| PDF-ALL | C1 | Actual PDF raster pixels, all physical pages | `pdftoppm -r 115 -png output/pdf/antropy-methods.pdf .omo/evidence/power-pdf-qa-r1/page`; `view_image(path=ABS_ROOT/.omo/evidence/power-pdf-qa-r1/page-NN.png)` individually for every NN=01..48 | PASS | R01..R48, HASHES |
| PDF-STRUCTURE | C2,C5,C6 | PDF metadata, native outline and link objects, LaTeX diagnostic data | `uv run python .omo/evidence/power-pdf-qa-r1/inspect_pdf.py > .omo/evidence/power-pdf-qa-r1/inspection.log 2>&1` | PASS | PROBE, STRUCTURE, LOG |
| PDF-FIGURES | C3 | Physical figure pages | Same exact raster/view invocations for NN=10,13,16,17,18,22,33,40 | PASS | R10,R13,R16,R17,R18,R22,R33,R40 |
| PDF-POWER-TABLES | C4 | All prospective tables, physical pages 23..45 | Same exact raster/view invocations for NN=23..45; enlarged crops below | PASS | R23..R45, Z-EFFECT, Z-AVAIL |
| PDF-DENSE-ZOOM | C3,C4 | Enlarged physical table/annotation pixels | `pdftoppm -f 45 -l 45 -r 180 -x 230 -y 220 -W 1900 -H 560 -png output/pdf/antropy-methods.pdf .omo/evidence/power-pdf-qa-r1/zoom-effect`; corresponding `view_image` | PASS | Z-EFFECT |
| PDF-INTERVAL-ZOOM | C4 | Enlarged availability intervals | `pdftoppm -f 35 -l 35 -r 180 -x 650 -y 220 -W 1450 -H 700 -png output/pdf/antropy-methods.pdf .omo/evidence/power-pdf-qa-r1/zoom-availability`; corresponding `view_image` | PASS | Z-AVAIL |
| PDF-STATUS-ZOOM | C3,C4 | Baseline figure status labels | `pdftoppm -f 16 -l 16 -r 210 -x 800 -y 370 -W 1600 -H 170 -png output/pdf/antropy-methods.pdf .omo/evidence/power-pdf-qa-r1/zoom-status-labels`; corresponding `view_image` | PASS | Z-STATUS |

### adversarialCases

| Scenario | Criterion | Adversarial class | Expected behavior | Verdict | artifactRefs |
|---|---|---|---|---|---|
| PDF-TRUNCATED | C6 | Malformed/truncated real file | Actual first 512 PDF bytes saved to a separate `.bin`; `PdfReader(..., strict=True)` must reject. Executed by exact PROBE invocation above; observed `PdfReadError: EOF marker not found`. | PASS | NEGATIVE, BROKEN, PROBE, LOG |
| PDF-NONFINITE | C4 | Zero availability and undefined result presentation | Sparse native HDSE 3D cells must retain unavailable counts, undefined conditional rates and [0,1] missing-decision bounds. Visually observed on physical pages 26..39; effect rows preserve dashes on 41..44. | PASS | R26..R39,R41..R44 |
| PDF-BOUNDARY | C4 | Rates at zero/one | Wilson bounds remain nonzero-width at 0 and 1; observed 0 [0,0.0566241] and 1 [0.943376,1], with complete digits in enlarged crop. | PASS | R27,R29,Z-AVAIL |
| PDF-NETWORK | C1 | Network/authentication/session failure | not_applicable: this is a frozen local PDF surface with no network or authenticated interaction. | not_applicable | PROBE |

### Page-by-page disposition

Every row below is an actual visual inspection, not an inference from the log. Raster hashes and non-empty byte counts are in HASHES.

| Physical page | Verdict | Observed content/disposition | artifactRefs |
|---|---|---|---|
| 1 | PASS | Title, subtitle, author, affiliation and email centered with clear margins. | R01 |
| 2 | PASS | Native contents: all 11 top-level sections and 32 linked entries; page labels agree with body pagination. | R02 |
| 3 | PASS | Abstract and introduction: version and experimental totals visible; citations resolved. | R03 |
| 4 | PASS | Scope and registry table start: citations legible, columns aligned. | R04 |
| 5 | PASS | Registry continuation and native HDSE equations (1)-(3): symbols and numbered equations intact. | R05 |
| 6 | PASS | HDSE conventions, executable procedure and related estimators: equation (4) and prose intact. | R06 |
| 7 | PASS | Probability identities and statistical complexity equations (5)-(8): no clipping. | R07 |
| 8 | PASS | Experimental design and full control table: wrapped values and equation (9) readable. | R08 |
| 9 | PASS | Generator explanation complete; deliberate whitespace precedes a full figure page. | R09 |
| 10 | PASS | Figure 1: all 18 illustrative field panels, dimensions and caption visible. | R10 |
| 11 | PASS | Geometry/resources discussion and scheduled-work table: small numeric font legible, all columns separated. | R11 |
| 12 | PASS | Work-table continuation, byte limitation and timing table: scientific notation and units readable. | R12 |
| 13 | PASS | Figure 2: work, memory and timing panels; log ticks, legend, uncertainty bars and caption visible. | R13 |
| 14 | PASS | Baseline table: undefined/infinite statuses explicit; replicated table begins clearly. | R14 |
| 15 | PASS | Replicated HDSE table continued: finite fractions, U/I counts and dash values visible. | R15 |
| 16 | PASS | Figures 3 and 4: baseline status annotations verified in enlarged crop; axes and captions intact. | R16 |
| 17 | PASS | Figure 5: all finite/undefined/infinite count cells legible; no status silently blank. | R17 |
| 18 | PASS | Figure 6: base/extended matching panels and conditional denominator labels legible. | R18 |
| 19 | PASS | Structured control table: all rows, undefined dashes, finite fractions and U/I columns visible. | R19 |
| 20 | PASS | Related-estimator results: dimensionless interpretation and numeric columns clear. | R20 |
| 21 | PASS | Related-estimator table continuation and interpretation: all values and closing rule visible. | R21 |
| 22 | PASS | Figures 7 and 8: geometry caveat, normalized axes, complete legend and both captions visible. | R22 |
| 23 | PASS | Prospective design: scenarios, full control table and inference controls begin with clear labels. | R23 |
| 24 | PASS | Inference controls continue; individual estimator configurations typeset without clipping. | R24 |
| 25 | PASS | Final configuration, totals, allocation schedule, two-sided floor, resource counts and hashes visible. | R25 |
| 26 | PASS | Multiplicity/availability/Wilson equations and unconditional results start: denominators and units clear. | R26 |
| 27 | PASS | Null unconditional table continued: method labels, counts and intervals readable. | R27 |
| 28 | PASS | Null table concludes and moderate alternative begins: repeated headers and complete rows. | R28 |
| 29 | PASS | Moderate alternative unconditional table continued: intervals wrap within their own cells. | R29 |
| 30 | PASS | Moderate table concludes, strong alternative begins: all column content complete. | R30 |
| 31 | PASS | Strong alternative unconditional table continued: counts and endpoints legible. | R31 |
| 32 | PASS | Strong alternative table concludes: all rows and closing rule retained. | R32 |
| 33 | PASS | Figure 9: all 12 method-by-shape panels, alpha/target references, legend and full caption readable. | R33 |
| 34 | PASS | Null availability table: explicit undefined conditional values and [0,1] missing-decision bounds visible. | R34 |
| 35 | PASS | Null availability continuation: enlarged crop confirms separate interval columns and all digits. | R35 |
| 36 | PASS | Moderate availability table: complete rows, undefined entries and interval bounds visible. | R36 |
| 37 | PASS | Moderate availability continuation: all intervals and final row inside page margins. | R37 |
| 38 | PASS | Strong availability table: conditional and missing-decision columns readable. | R38 |
| 39 | PASS | Strong availability continuation: complete rows and bottom rule visible. | R39 |
| 40 | PASS | Figure 10: availability and null calibration panels; raw versus adjusted markers, legend and caption clear. | R40 |
| 41 | PASS | Effect summaries: estimator units explained; mean/SD, raw and adjusted columns separated. | R41 |
| 42 | PASS | Null effect continuation and moderate effect start: negative signs and undefined dashes visible. | R42 |
| 43 | PASS | Moderate effects continue; strong contrast starts with readable complete rows. | R43 |
| 44 | PASS | Strong effect table continuation: no numeric collisions, methods remain identifiable. | R44 |
| 45 | PASS | Final effect rows verified enlarged; bootstrap explanation and numerical verification receipts readable. | R45 |
| 46 | PASS | Template pin, provenance hashes and discussion: monospaced paths wrap; no clipping. | R46 |
| 47 | PASS | Discussion concludes; references begin with readable titles, journals, DOIs and URL. | R47 |
| 48 | PASS | References finish: all final entries including Xia and Wang present with full DOI. | R48 |

## Figure binding observed in physical pixels

1 inputs p10; 2 cost scaling p13; 3 baseline p16; 4 replicated MIX p16; 5 degeneracy p17; 6 match probabilities p18; 7 native/flattened geometry p22; 8 entropy-complexity p22; 9 prospective rejection p33; 10 availability/null calibration p40. These cover all ten configured figure entries in `docs/manuscript/project.yaml`.

## Observations and limits

- No clipped text, collisions, missing plot panels, unresolved variable tokens, missing glyphs, unresolved citations or references were found. The authenticated renderer log has zero Overfull and zero Missing character occurrences. The PDF text has no unresolved `{{...}}`, `[?]`, or `??` tokens.
- An existing monospaced bold font substitution warning occurs in the renderer log. Actual inspected configuration/path text is legible; this is nonblocking and is not reported as a warning-free compilation.
- The document uses extensive full result tables and float pages. Physical page 9 has considerable whitespace before a dedicated figure page, and some headings precede floated material. These are nonblocking pagination choices; all content is present. Baseline figure status notes are small at page scale but remain legible when enlarged, with the same statuses explicitly retained in the adjacent table.
- Initial inline metadata probe hit `TypeError` while counting an indirect annotation object; no acceptance result was produced by that failed probe. The persisted corrected PROBE dereferences actual PDF objects and completed with exit 0. The failure is preserved here rather than treated as a successful check.
- This PASS covers physical publication layout, structural navigation, visible completeness and fixed artifact identity. It does not independently certify numerical source correctness, full replay, statistical claims, archive installation, hosted CI, publication/release readiness or accessibility tagging. The PDF is not tagged; no accessibility conformance claim is made. Other independent gates remain the caller's responsibility.

### artifactRefs

Paths are repository-relative; ABS_ROOT in invocations resolves to `/Volumes/GitVault/Username/docxology/Public/antropy`.

| id | kind | description | path |
|---|---|---|---|
| R01 | PNG raster | Inspected physical page 1, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-01.png |
| R02 | PNG raster | Inspected physical page 2, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-02.png |
| R03 | PNG raster | Inspected physical page 3, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-03.png |
| R04 | PNG raster | Inspected physical page 4, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-04.png |
| R05 | PNG raster | Inspected physical page 5, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-05.png |
| R06 | PNG raster | Inspected physical page 6, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-06.png |
| R07 | PNG raster | Inspected physical page 7, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-07.png |
| R08 | PNG raster | Inspected physical page 8, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-08.png |
| R09 | PNG raster | Inspected physical page 9, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-09.png |
| R10 | PNG raster | Inspected physical page 10, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-10.png |
| R11 | PNG raster | Inspected physical page 11, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-11.png |
| R12 | PNG raster | Inspected physical page 12, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-12.png |
| R13 | PNG raster | Inspected physical page 13, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-13.png |
| R14 | PNG raster | Inspected physical page 14, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-14.png |
| R15 | PNG raster | Inspected physical page 15, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-15.png |
| R16 | PNG raster | Inspected physical page 16, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-16.png |
| R17 | PNG raster | Inspected physical page 17, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-17.png |
| R18 | PNG raster | Inspected physical page 18, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-18.png |
| R19 | PNG raster | Inspected physical page 19, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-19.png |
| R20 | PNG raster | Inspected physical page 20, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-20.png |
| R21 | PNG raster | Inspected physical page 21, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-21.png |
| R22 | PNG raster | Inspected physical page 22, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-22.png |
| R23 | PNG raster | Inspected physical page 23, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-23.png |
| R24 | PNG raster | Inspected physical page 24, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-24.png |
| R25 | PNG raster | Inspected physical page 25, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-25.png |
| R26 | PNG raster | Inspected physical page 26, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-26.png |
| R27 | PNG raster | Inspected physical page 27, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-27.png |
| R28 | PNG raster | Inspected physical page 28, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-28.png |
| R29 | PNG raster | Inspected physical page 29, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-29.png |
| R30 | PNG raster | Inspected physical page 30, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-30.png |
| R31 | PNG raster | Inspected physical page 31, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-31.png |
| R32 | PNG raster | Inspected physical page 32, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-32.png |
| R33 | PNG raster | Inspected physical page 33, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-33.png |
| R34 | PNG raster | Inspected physical page 34, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-34.png |
| R35 | PNG raster | Inspected physical page 35, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-35.png |
| R36 | PNG raster | Inspected physical page 36, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-36.png |
| R37 | PNG raster | Inspected physical page 37, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-37.png |
| R38 | PNG raster | Inspected physical page 38, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-38.png |
| R39 | PNG raster | Inspected physical page 39, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-39.png |
| R40 | PNG raster | Inspected physical page 40, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-40.png |
| R41 | PNG raster | Inspected physical page 41, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-41.png |
| R42 | PNG raster | Inspected physical page 42, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-42.png |
| R43 | PNG raster | Inspected physical page 43, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-43.png |
| R44 | PNG raster | Inspected physical page 44, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-44.png |
| R45 | PNG raster | Inspected physical page 45, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-45.png |
| R46 | PNG raster | Inspected physical page 46, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-46.png |
| R47 | PNG raster | Inspected physical page 47, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-47.png |
| R48 | PNG raster | Inspected physical page 48, 115 dpi | .omo/evidence/power-pdf-qa-r1/page-48.png |
| HASHES | JSON | SHA-256 and byte size of every raster | .omo/evidence/power-pdf-qa-r1/raster-sha256.json |
| PROBE | Python | Executed read-only structure and negative-control probe | .omo/evidence/power-pdf-qa-r1/inspect_pdf.py |
| STRUCTURE | JSON | Metadata, TOC destinations, outline, figure map, hashes and diagnostics | .omo/evidence/power-pdf-qa-r1/structure.json |
| LOG | log | Successful real probe invocation output | .omo/evidence/power-pdf-qa-r1/inspection.log |
| NEGATIVE | JSON | Actual malformed-input rejection receipt | .omo/evidence/power-pdf-qa-r1/negative-control.json |
| BROKEN | binary | Truncated real PDF negative input, distinct from production PDF | .omo/evidence/power-pdf-qa-r1/truncated-negative-control.bin |
| Z-EFFECT | PNG crop | 180 dpi final effect table numeric spacing | .omo/evidence/power-pdf-qa-r1/zoom-effect-45.png |
| Z-AVAIL | PNG crop | 180 dpi availability/conditional/missing intervals | .omo/evidence/power-pdf-qa-r1/zoom-availability-35.png |
| Z-STATUS | PNG crop | 210 dpi baseline nonfinite annotations | .omo/evidence/power-pdf-qa-r1/zoom-status-labels-16.png |
| TEXT | text | Supplementary full PDF layout text extraction, not a visual substitute | .omo/evidence/power-pdf-qa-r1/pdf-text.txt |
