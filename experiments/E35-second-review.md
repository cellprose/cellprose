# E35: second review of the Tier 2 set, before any Tier 2 call

**Status:** done (2026-11-10). A model reviewer (Opus) read PR #64 at commit 2e9789a. No paid call was made. The owner approved the drops and one more freeze (decision card, 10 Nov 2026).

**What was checked.** All 130 frozen files and the digest; the 180 `rw2_` questions rebuilt from source (no mismatch); lookup, trace, hardcode and impact truths recomputed independently; the SpreadsheetBench subset (30 workbooks, 122 questions; it keeps 0 tasks without `npm ci` in `benchmarks/`, with no warning); PROTOCOL.md section 0.2, the runner and the scorer.

**Findings and what was done**

| Finding | Action |
|---|---|
| 9 `rw2_` questions with a header that is not a header, an ambiguous label, or a wrong stated answer | Removed from the question files (owner, 10 Nov 2026); `realworld2.py` applies the removal at build and renumbers ids q1..qN, so the set is 171 questions |
| `score.py` scored 1.0 for a missing or failed answer when the truth is empty (5 hardcode questions) | Fixed; test added |
| `score.py` scored 0 for `'Original OBA''s'!X` | Fixed; test added |
| PROTOCOL.md named ids that do not exist, had two sections 0.2, a stale sentence, and a conflict between 0.2 item 3 and section 5 rule 2 | Fixed (sections 0.2, 0.3, 5, 6) |
| `score.py`, runners, `package-lock.json` outside the freeze | Added to the manifest |

**Effect on the pilot.** Re-scoring E32 with the fixed scorer changes two scores, both in the `none` arm (hardcode, answer `null`, 1.0 to 0.0). No compared arm changes. E30 was not re-scored here because its corpus is not in this environment; its hardcode answers should be checked the same way before any pilot figure is quoted again.

**Not done.** The 171 questions still need a human reader (0 ticked in `review.md`); the model review is the second reader the protocol asks for.

**Clean freeze (owner, 10 Nov 2026).** The owner asked for the run to stand as the first benchmark: `docs/PROTOCOL.md` was rewritten as a single protocol (no tiers, revisions or pilot history), the earlier manifests `tier2.json`, `tier2_v2.json` and `tier2_v3.json` were removed, and `benchmarks/freeze.py` writes the one manifest, `freeze/benchmark.json`. The earlier protocol text stays in git history.

**Pre-run review (owner, 11 Nov 2026).** A dry run of the exact run commands on both held-out corpora with a fake client that answers with the ground truth (every question scored 1; runner, score.py and analyze.py ran end to end), then a check of the data and the protocol against the code. Fixed before the run, with the owner's approval:
- The 15 Damodaran workbooks could not be recomputed by anyone else: Damodaran serves `.xls`, the frozen files are LibreOffice conversions, and a conversion never gives the same bytes. All 15 were downloaded again on 11 Nov 2026 and converted: every formula, value and cached value matched, and the encoded text was identical, but no file hash did. `selection.json` now records each `.xls` SHA-256 (`source_sha256`) and a content hash (`cell_sha256`, `freeze.py`); the freeze lists these workbooks by content; `realworld2.py fetch` downloads, converts and checks them.
- PROTOCOL.md 5.2 said results from different invocations are never compared, but the headline compares the one-shot and agent invocations. The four invocations of the run are now one run (same day, commit and settings); `none` runs at three repeats inside the one-shot invocation instead of once.
- `limitations.py` described the earlier synthetic headline only; it now has the run's limitations, which `analyze.py` prints for a `--final` run, filled from the results. The price-check date is passed with `--prices-checked` (required with `--final`) and recorded in the run manifest, instead of living in a frozen file.
- The cost estimate used old CLI averages for agent calls and placeholder output counts; it now uses the API pilot's per-model, per-arm averages (`runner/pilot.py`).
- The local held-out encodings still had pre-rename file names (generated files, not in git); regenerated, byte-identical to the old ones.
Left for the owner: the review wording (the owner will read the questions).

**Third review (Fable 5.2 thread, 11 Nov 2026; applied with the owner's approval).** Report: `question-review-drop-list.md` in the project files. Dropped by rule, never reworded: 8 `rw2_` questions (2 wrong or ambiguous, 6 whose "header" is not a header of the cell; `DROPPED` in `realworld2.py`) and 16 `sb_` questions in 5 tasks (`DROPPED` in `spreadsheetbench.py`; three tasks lose every question, so the set is 27 workbooks). Left: 163 `rw2_` questions on 30 workbooks and 106 `sb_` questions on 27. Also: a whole-number answer must now match within 0.01 (the 0.5% tolerance let any 7-digit employee number pass), `analyze.py` prints the `none` accuracy beside every arm's, `realworld2.py check` fails when a question is missing, and `freeze.cell_sha256` hashes array formulas by their range and text instead of an object address. No `rw2_` question other than the dropped ones changed; the rebuilt `sb_` files are byte-identical apart from the drops.

**sb_54925 restored (owner, 11 Nov 2026).** Its five questions were dropped only because the 0.5% tolerance let any employee number pass; with whole-number answers now matched exactly, that reason is gone, and the re-review found nothing else wrong with them. Final sets: 163 `rw2_` questions on 30 workbooks and 111 `sb_` questions on 28 (11 of 122 dropped).
