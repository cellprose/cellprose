# E26: first run on the real-world set, CSV vs Sheetmark v0.2 (Haiku 5.5, Sonnet 5.5)

**Date:** 2026-10-12 · **Type:** held-out run, exploratory first look · **Status:** done. Cost $3.65 (approved scope about $3.18, expected $3.30, hard cap $5).

## Question

On 17 real workbooks (E24), does v0.2 let Haiku 5.5 and Sonnet 5.5 answer correctly for less money than CSV?

## Setup

- Corpus: `benchmarks/external/realworld` (E24), 17 workbooks, 67 questions, held-out `rw_` prefix, run with `--final` on a clean tree at integration commit eb07a30.
- Encodings: `csv` and `sheetmark_lean_gfm`, one-shot. Models: `haiku55`, `sonnet55`, pinned settings from `runner/models.py`. One repeat, one invocation (68 calls, 0 failures), list prices, uncached, long-prompt tiers applied per request (E25).
- Run: `SHEETMARK_CORPUS=external/realworld api_run.py --models haiku55,sonnet55 --encs csv,sheetmark_lean_gfm --final --out results/realworld --vendor-cap-usd 5`. Raw files, run manifest and scores are in `benchmarks/results/realworld/`.

## Results

Per-question accuracy (67 questions):

| Model | Encoding | All | Lookup | Address | Trace | Impact |
|---|---|---|---|---|---|---|
| Haiku 5.5 | CSV | 80.7 | 97.4 | 70.6 | 55.8 | 15.2 |
| Haiku 5.5 | v0.2 | 91.4 | 100.0 | 76.5 | 100.0 | 56.3 |
| Sonnet 5.5 | CSV | 98.7 | 100.0 | 100.0 | 95.8 | 86.4 |
| Sonnet 5.5 | v0.2 | 98.5 | 100.0 | 100.0 | 100.0 | 75.6 |

Cost per correct answer, v0.2 relative to CSV (per-workbook mean accuracy, 95% paired bootstrap over 17 workbooks):

| Model | Ratio | 95% interval | Verdict |
|---|---|---|---|
| Haiku 5.5 | 0.86 | 0.69 to 1.03 | no difference |
| Sonnet 5.5 | 0.92 | 0.83 to 0.995 | v0.2 cheaper |

- v0.2 sent 1.11 times CSV's input tokens (Anthropic's counter), yet cost 7 to 8% less per call, because output tokens fell (analyze.py reports a large drop in output tokens; the cause was not investigated).
- Trace questions: v0.2 got 100% for both models. Haiku on CSV got 55.8%.
- Impact questions (4, very hard: 68 to 102 cells for the Damodaran models) are low for everyone; v0.2 and CSV differ there but with 4 questions that is not a finding.
- Total spend by encoding and model: Haiku CSV $0.16, v0.2 $0.15; Sonnet CSV $1.75, v0.2 $1.60. The `worldbank_gdp` v0.2 prompt (144,580 Anthropic tokens) was above Haiku's 100K tier and was priced at the long rate.

## Limitations (read before quoting)

- **One repeat, no spread.** One wrong answer moves a workbook by 17 to 33 points. The bootstrap resamples workbooks, not model noise.
- **Only 17 workbooks, 4 of them Damodaran models**, which dominate the cost, and 67 questions of which 38 are lookups on tidy tables. 4 impact questions.
- **Questions were written by Claude and checked by one reviewer (Claude)** before any model ran (E24). Real workbooks are public Damodaran, government and open-data files, not a random sample of what users have.
- Two models and two encodings only. No MarkItDown, no agent baseline, no OpenAI model, so this is not the protocol's primary comparison.
- Accuracy in the first table is per question; the ratio table uses per-workbook means, so Haiku reads 91.4 versus 90.9.
- `analyze.py` printed its limitations text for the synthetic set ("All synthetic ..."); that text does not describe this run and should not be quoted with these numbers.
- Intended as an exploratory first look. Because this used the held-out `rw_` set, no format or prompt change may follow from it without a new held-out set (PROTOCOL section 3).

## Conclusion

On real workbooks, v0.2 was cheaper per correct answer than CSV for Sonnet 5.5 (a small win, interval just under 1) and did not differ detectably for Haiku 5.5, where accuracy was higher but the interval spans 1. With one repeat and 17 workbooks this is a first signal, not the publishable result.
