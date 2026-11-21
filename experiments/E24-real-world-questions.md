# E24: real-world question set (B9)

Date: 2026-10-11. Cost: $0 in model calls. One free token-counting request per prompt (see Size) was sent to Anthropic's count endpoint.

## Question

PROTOCOL section 3 needs 10-20 public workbooks with checked questions for the held-out run. Everything run so far uses 14 workbooks built alongside the format. Is there a real-world set whose questions and answers do not come from a model, and what does it cost to run?

## What was built

`benchmarks/external/realworld.py` and `benchmarks/external/realworld/`:

| Workbook set | Files | Why |
| --- | --- | --- |
| Damodaran valuation models (NYU Stern), native .xlsx | `fcffginzu`, `fcffsimpleginzu`, `fcffsimpleginzuCorona`, `capstru` | real, formula-heavy (894-1,231 formulas), labels and values in separate regions, cross-sheet formulas, circular references |
| Government statistics | IRS Table 1.1, Census new residential construction, BEA GDP table 1, World Bank GDP | year headers in a row above, footnote markers (`[2]`, `S`), a repeated block ("$10,000,000 or more" appears twice), 270 x 70 sparse grid |
| Open-data transaction lists | `ogl00`, `01`, `04`, `05`, `06`, `07`, `12`, `13`, `14` | long tables, text-heavy; `ogl13` has 78 VLOOKUPs into an external workbook |

17 workbooks, 67 questions: 4 + 13 workbooks, by type 38 lookup, 17 address, 8 trace, 4 impact. Per workbook it is a hand-written list (8 workbooks) or a rule over a table (9): rows at 20%, 50% and 80% of the data rows, a unique key, two lookups and one address question.

Ground truth is computed, never typed: lookup from the cached value, address is the cell, trace is the formula's direct precedents, impact is the set of cells that differ between two LibreOffice recalculations of the workbook, one with the input multiplied by 1.1 (both copies saved by openpyxl, and any cell that changes between two recalculations of the same file is dropped as noise; none was). `python3 benchmarks/external/realworld.py check` recomputes everything and compares it with the committed questions; `tests/test_realworld_corpus.py` does the same for every source file that is available and skips the Damodaran files elsewhere.

## The hand check

One reviewer (Claude), one pass, after the builder's checks: each question was read against the row and column labels around its answer, listed in `external/realworld/review.md`. The builder also refuses a question whose key matches more than one row. That caught one real ambiguity before any model saw it: in the IRS table "$10,000,000 or more" appears in both the first block and the "accumulated from largest" block (rows 29 and 52), so the question now names the block and the key is checked within rows 10-29. It also found a mistake of mine: the shares-outstanding cell of `fcffsimpleginzu` is B21, not B18 (B18 is cash). **A second reviewer, ideally someone who knows the Damodaran models, should read `review.md` before the final run.** Nobody has checked the answers against Excel, only against the cached values in the files and a LibreOffice recalculation.

## Size and cost

Token counts for the whole set (OpenAI o200k): CSV 513K, Sheetmark v0.2 586K across 17 workbooks, range 1.6K to 130K per workbook. One prompt is over 100,000 tokens (`worldbank_gdp`, 130K; `fcffsimpleginzu` is next at 82K), where Haiku 5.5 charges 5 times the rate (E25). A dry-run estimate for haiku55 and sonnet55, CSV and v0.2, one repeat, final run guard on: 68 calls, 2.82M input tokens counted by Anthropic, expected $3.18, worst case $14.39. For three repeats, four encodings and seven models, scale that estimate; the set is much larger per call than the synthetic one, so it dominates the cost of the final run.

## Problems found on the way

- `benchmarks/encoders.py` crashed on any workbook with an empty sheet or a chart sheet (`IndexError`), so the CSV, Markdown, Markdown-KV and TOON baselines failed on 7 of the 42 real workbooks and on 1 of the 4 used here. Fixed (`grid` returns one empty row); synthetic encodings are unchanged.
- openpyxl cannot save a workbook that contains images twice; the impact code reloads for each copy.
- A recalculation of the original and of an openpyxl-saved copy differ in a few cells (`Option Value` sheets), so impact compares two copies saved the same way.
- The impact answers for the three Damodaran models are 68, 102 and 98 cells, because changing shares changes the market-value weights in the cost of capital. They are real dependencies and very hard to list; expect low F1 for every format.

## Limits

Questions are Claude-written (the type, the cells and the wording), so "designed for the format" is not fully answered; the selection rule (above, and `spec.json`) was fixed before any model run and the table questions come from fixed row positions. Many questions are lookups on tidy tables, where all formats should do well. Only 4 impact questions. Five files came from `.xls` conversions made with LibreOffice, so their cached values are LibreOffice's. Units, units suffixes and footnote markers are left as the sheet has them.

## Reproduce

`cd benchmarks && npm ci && python3 external/realworld.py build` (needs LibreOffice, and `--files DIR` or `SHEETMARK_FETCH_REAL=1` for the Damodaran files), then `SHEETMARK_CORPUS=external/realworld python3 api_run.py --models haiku55 --encs csv,sheetmark_lean_gfm --final --estimate-only`. Estimates call Anthropic's free token-counting endpoint when a key is set.
