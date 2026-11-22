# Experiments

Every experiment run on Cellprose (called Sheetmark at the time) so far, one file each, in order. Each file covers the question, setup, results, what went wrong and what was concluded. Each links to the code in [`../benchmarks/`](../benchmarks/) or [`../src/`](../src/) and to its raw results. Decisions drawn from these experiments live in [`../docs/DESIGN.md`](../docs/DESIGN.md).

| ID | Experiment | Date | Type | Status | Headline |
| --- | --- | --- | --- | --- | --- |
| [E01](E01-format-comparison-standard.md) | Format comparison, standard workbooks | 2026-10-07 | Benchmark | Superseded by E09 | Formats saturate at 94–100%; key-value and TOON lose cell positions |
| [E02](E02-hard-workbooks.md) | Hard workbooks and the typed-in-vs-formula task | 2026-10-07 | Benchmark | Superseded by E09 | Only Sheetmark scores 100% at telling typed-in numbers from formulas |
| [E03](E03-token-accounting.md) | Where the tokens go: input vs reasoning | 2026-10-07 | Analysis | Method adopted | Sheetmark costs more input but saves reasoning; headline metric becomes cost per correct answer |
| [E04](E04-compact-variants.md) | Compact variants: comma block vs compact pipe table | 2026-10-07 | Benchmark | Decided | Compact pipe table chosen: renders on GitHub, ~4% bigger than commas |
| [E05](E05-agent-mode-v1.md) | Agent mode, first run | 2026-10-07 | Benchmark | Superseded by E09 | Exploring raw .xlsx is the most expensive path |
| [E06](E06-answer-parser-fix.md) | Answer-parser fix and rescoring | 2026-10-07 | Scoring bug | Fixed | Models' self-corrections were scored as zero |
| [E07](E07-sheet-prefix-bug.md) | Missing `Sheet:` prefix | 2026-10-07 | Format bug | Fixed | Dropping two words made Haiku invent a sheet name |
| [E08](E08-usage-limit-interruption.md) | Usage-limit interruption | 2026-10-07 | Run failure | Handled | 33 error responses removed; runner now rejects errors |
| [E09](E09-same-session-repeats.md) | Same-session repeats; session drift | 2026-10-08 | Benchmark | **Current** | v0.2 vs CSV: −17% (Haiku) and −5% (Sonnet) cost per correct answer; −26% / −16% on hard workbooks |
| [E10](E10-cache-neutral-cost.md) | Cache-neutral cost | 2026-10-08 | Measurement fix | Adopted | Prompt cache made repeats look 90% cheaper |
| [E11](E11-scientific-notation-bug.md) | Scientific notation in rounded values | 2026-10-08 | Format bug | Fixed | `1.51599e+06` now prints as `1515990` |
| [E12](E12-integration-smoke-tests.md) | MCP server and skill in Claude Code | 2026-10-08 | Integration | Passed | Both gave correct answers; $0.02 and $0.08 |
| [E13](E13-api-runner-sample.md) | Direct-API runner, sample run | 2026-10-09 | Benchmark tooling | Done | Sample run: 18 calls, $0.29, `score.py` ran unchanged; `analyze.py` crashed without agent data (now fixed). Plumbing check only |
| [E14](E14-decoder-roundtrip.md) | Decoder and round trip on the corpus | 2026-10-09 | Round-trip test | Passing | encode → decode → recalculate → encode is byte-identical on 15 workbooks; 7 escaping gaps found and fixed |
| [E15](E15-opus-gpt-sample.md) | Sample run: Opus 5.5 and three GPT models | 2026-10-09 | Benchmark tooling | Done | 24 calls, $0.42; plumbing check only, GPT prices unverified |
| [E16](E16-grid-csv-vs-sheetmark.md) | CSV vs Sheetmark, 7 models, 14 workbooks, 2 repeats | 2026-10-09 | Benchmark | Done | 392 calls, $5.29. Sheetmark more accurate on all 7; input +24-27%, output -16-31%, cost -25% to +3% |
| [E17](E17-all-encodings.md) | All 11 encodings on 3 cheap models | 2026-10-09 | Benchmark | Done | 462 calls, $1.91. `sheetmark_lean` has the least overhead (+18% input) and best cost per correct; `none` scores 1-5% |
| [E18](../benchmarks/external/README.md) | SpreadsheetBench held-out run | not run | Benchmark | Planned, held | No result file yet. Priced at about $89 expected (2 encodings × 7 models × 1 repeat); held until the [protocol](../docs/PROTOCOL.md) "To build" list is done and the owner approves the spend. Dataset notes and selection rules: `benchmarks/external/` |
| [E19](E19-pipeless-rows.md) | Grid rows without outer pipes | 2026-10-10 | Benchmark | Done | 252 calls, $0.99. Same rendering on GitHub; accuracy −0.1 to +0.3 points (no difference), input −4.5% Claude / −2.9% GPT, cost per correct no difference. E18 is reserved for the SpreadsheetBench run |
| [E20](E20-markitdown-formulas.md) | Does MarkItDown keep formulas? xlgit and xltrail status | 2026-10-11 | Baseline check | Done | No model calls. MarkItDown 0.1.7 drops all formula text (0 of 3,288 formula cells across 6 real workbooks) |
| [E21](E21-format-checks.md) | Format checks: live GitHub, format gaps, agent-mode gap, model ids | 2026-10-11 | Analysis | Done; live GitHub check open | Agent gap is 9 of 558 question-repeats, two on fill ranges; snapshot ids do not exist; live render needs a public repo |
| [E22](E22-fill-range-hint.md) | Would a fill-range hint fix agent-mode trace errors? | 2026-10-11 | B20 | Variant built, run not recommended | No model calls. +5.8% tokens; the 3 trace misses are not shift errors. Reader rejects the comment today. |
| [E23](E23-excel-parser.md) | excel-parser vs v0.2 on shared workbooks: tokens and formula recovery | 2026-10-11 | Baseline check | Done | No model calls. excel-parser text 3.0x CSV and no formula text; JSON 20.8x CSV; v0.2 1.14x CSV, all formulas |
| [E24](E24-real-world-questions.md) | 67 hand-checked questions on 17 real workbooks, ground truth computed | 2026-10-11 | Benchmark corpus | Built, not yet run | No model calls. Held-out `rw_` fence; one reviewer; v0.2 586K tokens vs CSV 513K |
| [E25](E25-price-check.md) | Do registry prices match the vendors' pages? | 2026-10-11 | B24 | Done | No model calls. Base prices all match; long-prompt tiers (Haiku 5.5 over 100K, GPT-6 over 272K) were missing and are added. |
| [E26](E26-real-world-run.md) | First run on the real-world set: CSV vs v0.2, Haiku 5.5 and Sonnet 5.5 | 2026-10-12 | Held-out run | Done | $3.65, one repeat. Cost per correct: Sonnet 0.92x CSV (win), Haiku 0.86x (no difference, interval spans 1) |
| [E27](E27-real-world-openai.md) | Real-world set on GPT-6 Luna and Sol: CSV vs MarkItDown vs v0.2 | 2026-10-12 | Held-out run | Done | $3.99, one repeat. Cost per correct: Luna 0.77x CSV and 0.75x MarkItDown (wins); Sol 1.05x CSV (no difference), 0.84x MarkItDown (win) |
| [E28](E28-v03-encoding.md) | v0.3 writer as a benchmark encoding: token cost vs v0.2 | 2026-10-18 | Dev set | Done | $0.79, 3 repeats, GPT-6 Luna and Sol. v0.3 sends 2.8% fewer input tokens than v0.2; accuracy within noise (Luna 98.4 vs 98.8, Sol 100 vs 99.8); cost per correct vs CSV: Luna 0.84x (win), Sol 0.98x (no difference) |
| [E29](E29-agent-smoke-test.md) | First live run of the API agent loop (smoke test before Tier 1) | 2026-11-07 | Dev sample | Done | $0.26, 24 calls on four models, 0 failures, 2 to 5 turns per call; harness check only |
| [E30](E30-tier1-pilot.md) | Tier 1 pilot: v0.3 vs MarkItDown, CSV and the xlsx agent on the 17 `rw_` workbooks | 2026-11-07 | Real-world (seen) | Done; gate not passed | $30.98, 816 calls, 0 failures. Win vs MarkItDown on Luna, Haiku, Sonnet (ratios 0.70-0.76); vs the xlsx agent no difference on 3 models, loss on Sol (3.1x); Haiku 8.8 points below the agent (column-off-by-one on addresses), so gate criterion 3 fails |
| [E31](E31-address-fault-ab.md) | A/B of row-label layouts and notes for the Haiku address fault (9 variants, 65 address questions) | 2026-11-07 | Real-world (seen), dev only | Done | about $3.4. Layout changes do not help; a front-matter note helps (72.3% to 90.0% best, 75-83% for other wordings), noisy |
| [E32](E32-repilot.md) | Re-pilot after the Tier 1 gate failure: v0.3.1 legend, 15 fresh Enron workbooks (`rw3_`), 4 models | 2026-11-07 | Fresh, rule-built | Done; gate passed | $28.5, 720 scored calls. v0.3.1 wins vs MarkItDown on all 4 models (0.16-0.58), no difference vs the xlsx agent, accuracy within 2 points of the best baseline; Haiku addresses 100%. Credit ran out mid-run; resumed (deviation) |
| [E33](E33-agent-tools-dev.md) | Cellprose agent tools (outline, read_range, find, trace) vs the openpyxl agent on 10 large dev workbooks (`dev_`), Haiku 5.5 and GPT-6.1 Sol | 2026-11-07 | Dev, rule-built | Done | $2.69, 80 calls. Tools arm level with agent_xlsx (0.97, 0.98); fewer turns but the ~10k-token outline costs what the turns save. One-shot v0.3.1 vs agent: Haiku 0.57 win, Sol 0.98. Follow-up ($2.30): index-only outline; on a fresh data-heavy Enron dev set (`dev_d_`) the index tools are 0.61 vs agent_xlsx on Haiku (win), 0.96 on Sol (tie) |
| [E34](E34-lean-tools.md) | Lean Cellprose tools (index in the prompt, multi-range reads, compact trace, what-if, no shell) vs the openpyxl agent, GPT-6.1 Sol, 20 fresh data-heavy Enron dev workbooks (`dev_e_`), 2 repeats | 2026-11-07 | Dev, rule-built | Done | $3.15. Lean 0.44 (0.35-0.57) cost per correct vs agent_xlsx, accuracy 94.2 vs 92.0; 0.45 with impact questions excluded |
| [E35](E35-second-review.md) | Second review of the Tier 2 set: 9 `rw2_` questions dropped, two scorer bugs fixed, PROTOCOL errors fixed, one more freeze | 2026-11-10 | 171 of 180 questions scored; two E32 `none`-arm scores change; no compared arm changes |
| [E36](E36-benchmark-run.md) | The benchmark run: 4 models, 7 arms, 3 repeats, real-world and SpreadsheetBench sets, under the frozen protocol | 2026-11-11 | Cellprose beats MarkItDown in 7 of 8 model-and-corpus pairs; vs CSV and agent arms, mostly no difference, Sonnet wins on the real-world set; no losses |
| [E37](E37-addendum-lean-tools.md) | Addendum A: Cellprose's own agent tools against the `.xlsx` agents, frozen and posted separately | 2026-11-11 | 14 of 24 wins, no losses; 0.29–0.79× cost per correct; remaining ties are accuracy (address, impact) |
| [E38](E38-replay-v03.md) | Home page replay re-recorded on v0.3: one call per format, Haiku 5.5, development workbook 11 | 2026-11-21 | CSV misses `Forecast!H4` (0.67), Cellprose v0.3 gets both (1.0); illustrative, not a rate |

## How the pieces connect

```
experiments/E0N-*.md  ── what was asked, found and decided
        │ links to
        ▼
benchmarks/           ── generators, encoders, runners, scorer, raw results
        │ results feed
        ▼
docs/DESIGN.md        ── format decisions and current numbers
        │ implemented in
        ▼
src/sheetmark/        ── the writer, CLI and MCP server
```

## Adding an experiment

Copy the shape of an existing file and number it next (E28, …). Fill in:
- question, setup, results, problems found, conclusion, and how to reproduce
- links to the code and the raw results
- a row in the table above

If it changes a decision, update `docs/DESIGN.md` in the same commit.
