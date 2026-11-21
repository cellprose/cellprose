# E27: real-world set with GPT-6 Luna and GPT-6.1 Sol, CSV vs MarkItDown vs Sheetmark v0.2

**Date:** 2026-10-12 · **Type:** held-out run, exploratory first look · **Status:** done. Cost $3.99 (priced first at $4.49 expected, cap $5; approved by the owner). No Anthropic calls, by the owner's instruction.

## Question

On the 17 real workbooks (E24), does v0.2 let the two cheaper OpenAI models answer correctly for less money than CSV and MarkItDown, the primary one-shot baseline (PROTOCOL section 1)?

## Setup

- Corpus: `benchmarks/external/realworld` (E24), 17 workbooks, 67 questions, held-out `rw_` prefix, `--final` on a clean tree at the integration head. Companion to E26 (Haiku 5.5 and Sonnet 5.5, CSV and v0.2); the two runs are separate invocations and are not pooled or compared.
- Encodings: `csv`, `markitdown`, `sheetmark_lean_gfm`, one-shot. Models: `gpt6luna` and `gpt61sol`, pinned settings from `runner/models.py`. One repeat, 102 calls, 0 failures. List prices, cached tokens priced as uncached.
- Run: `SHEETMARK_CORPUS=external/realworld api_run.py --models gpt6luna,gpt61sol --encs csv,markitdown,sheetmark_lean_gfm --final --out results/realworld_openai --vendor-cap-usd 5`. Raw files, manifest and scores: `benchmarks/results/realworld_openai/`.

## Results

Per-question accuracy (67 questions):

| Model | Encoding | All | Lookup | Address | Trace | Impact |
|---|---|---|---|---|---|---|
| Luna | CSV | 77.2 | 97.4 | 58.8 | 37.5 | 42.7 |
| Luna | MarkItDown | 87.0 | 97.4 | 82.4 | 75.0 | 32.1 |
| Luna | v0.2 | 98.5 | 100.0 | 100.0 | 100.0 | 75.5 |
| Sol | CSV | 95.9 | 100.0 | 100.0 | 83.3 | 65.0 |
| Sol | MarkItDown | 94.8 | 100.0 | 94.1 | 83.3 | 70.4 |
| Sol | v0.2 | 98.6 | 100.0 | 100.0 | 100.0 | 76.3 |

Cost per correct answer, v0.2 relative to each baseline (per-workbook mean accuracy, 95% paired bootstrap over 17 workbooks):

| Model | Baseline | Ratio | 95% interval | Verdict |
|---|---|---|---|---|
| Luna | CSV | 0.77 | 0.61 to 0.92 | v0.2 cheaper |
| Luna | MarkItDown | 0.75 | 0.65 to 0.85 | v0.2 cheaper |
| Sol | CSV | 1.05 | 0.96 to 1.13 | no difference |
| Sol | MarkItDown | 0.84 | 0.74 to 0.94 | v0.2 cheaper |

- Input tokens relative to CSV: v0.2 about 1.10x (Luna) and 1.13x (Sol); MarkItDown 1.22x and 1.25x. Cost per call relative to CSV: v0.2 about -4% (Luna) and +7% (Sol).
- The v0.2 gain is mostly accuracy for Luna (CSV 77, v0.2 98.5) and mostly trace and address questions, where formula text is the answer. Sol is already near the ceiling with CSV, so the saving over CSV disappears there.
- Impact questions (4) remain the weakest for everyone.

## Limitations (read before quoting)

- **One repeat, no spread.** One wrong answer moves a workbook by 17 to 33 points. The bootstrap resamples workbooks, not model noise.
- 17 workbooks, 4 of them Damodaran models; 38 of 67 questions are lookups on tidy tables; 4 impact questions.
- Questions written by Claude and checked by one reviewer (Claude), before any model ran (E24). The workbooks are public Damodaran, government and open-data files, not a random sample of user files.
- Two OpenAI models and three one-shot encodings. No agent baseline, no GPT-6 Astra, no Anthropic model in this run, so it is not the protocol's full comparison.
- Accuracy in the first table is per question; the ratio table uses per-workbook means.
- `analyze.py` prints its limitations text for the synthetic set ("All synthetic ..."); it does not describe this run and should not be quoted with these numbers.
- Used the held-out `rw_` set: exploratory, and no format or prompt change may follow from it without a new held-out set (PROTOCOL section 3).

## Conclusion

For Luna, v0.2 was cheaper per correct answer than both CSV and MarkItDown, because accuracy rose by 11 to 21 points for 10% more input tokens. For Sol it beat MarkItDown and matched CSV. With one repeat and 17 workbooks this is a first signal, not the publishable result.
