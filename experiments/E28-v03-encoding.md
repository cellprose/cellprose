# E28: v0.3 writer as a benchmark encoding

> **Ids (renamed 9 Nov 2026).** This file was written with the ids `sheetmark_v03` (v0.3 text without the row-number legend) and `sheetmark_v031` (with it). They are now `cellprose_v03_nolegend` and `cellprose_v03`; `agent_` variants likewise. Raw results keep the old ids and score unchanged. "v0.3.1" below means the text with the legend.

**Status:** done. Token cost measured offline; accuracy and cost run on GPT-6 Luna and Sol.

## What changed
`benchmarks/encoders.py` has a new encoding `sheetmark_v03`. Unlike the older Sheetmark variants it is not a benchmark-local
encoder: it calls the shipped writer (`src/sheetmark/writer.py`, spec v0.3). Encoded files for the 14 benchmark workbooks
are in `benchmarks/encoded/*.sheetmark_v03.txt`. The workbooks, questions and ground truth are unchanged.

## Result (tokens only, free, no model calls)
tiktoken `o200k_base`, all 14 benchmark workbooks, `sheetmark_lean_gfm` (v0.2) against `sheetmark_v03`:

| Encoding | Tokens |
|---|---|
| sheetmark_lean_gfm (v0.2) | 18,382 |
| sheetmark_v03 | 17,779 (-3.3%) |

Limitations: OpenAI tokenizer, not Claude's; says nothing about accuracy. The two texts also differ in more than the
pipes (blank lines between blocks, extras such as comments and the `not carried` note), so the saving is not only from the pipe-less rows.

## Accuracy and cost run (2026-10-20)
Models: GPT-6 Luna and GPT-6 Sol only (no Anthropic models). One invocation, so every call shares a run id: CSV, v0.2
(`sheetmark_lean_gfm`) and v0.3 (`sheetmark_v03`), 14 workbooks, 93 questions, 3 repeats, 252 calls, 0 failures.
Spend $0.79 (cap $5). Raw results: `benchmarks/results/e28-v03/`. Reproduce:
`python benchmarks/api_run.py --models gpt6luna,gpt61sol --encs csv,sheetmark_lean_gfm,sheetmark_v03 --reps 3 --max-usd 5 --out results/e28-v03 --allow-dirty`,
then `RESULTS_DIR=results/e28-v03 python benchmarks/score.py` and `analyze.py`.

| Model | Encoding | Accuracy | Mean cost per question | Billed input tokens |
|---|---|---|---|---|
| Luna | CSV | 96.3 | $0.000610 | 1,279 |
| Luna | v0.2 | 98.8 | $0.000499 | 1,609 |
| Luna | v0.3 | 98.4 | $0.000525 | 1,564 |
| Sol | CSV | 98.4 | $0.005687 | 1,279 |
| Sol | v0.2 | 99.8 | $0.005740 | 1,609 |
| Sol | v0.3 | 100.0 | $0.005664 | 1,564 |

Cost per correct answer against CSV (paired bootstrap over workbooks, 95% interval):

| Model | v0.2 vs CSV | v0.3 vs CSV |
|---|---|---|
| Luna | 0.80x (0.69 to 0.90), win | 0.84x (0.72 to 0.97), win |
| Sol | 1.00x (0.89 to 1.08), no difference | 0.98x (0.88 to 1.06), no difference |

v0.3 sends 2.8% fewer input tokens than v0.2 (1,564 vs 1,609 billed per call) and is 22% more than CSV (v0.2: 26%).

## Limitations
- Same 14 synthetic workbooks as the earlier runs, so a single wrong answer moves a workbook by 12 to 17 points. Luna's v0.2 and v0.3 accuracy (98.8 vs 98.4) are not distinguishable at this size, and Luna's per-repeat accuracy ranged 93.8 to 97.9 for CSV.
- Hard-coded-cell questions on Luna: v0.3 scored 96.3 against 100 for v0.2 (few questions, 3 repeats); not conclusive.
- Two GPT-6 models only; no Claude model. The prices are list prices as in `runner/models.py`, all input tokens priced as uncached.
- The v0.3 text differs from v0.2 in more than the pipes (blank lines, extras such as comments and the `not carried` note), so the difference is not only the pipe-less rows.
- The prompt for the v0.3 run uses the same system and question text as v0.2.

## Conclusion
v0.3 keeps the v0.2 accuracy result within noise on both models and costs slightly less in input. It does not change the headline: a cost win over CSV on Luna, no difference on Sol.

## Note on the rename
The run used the text with `sheetmark: 0.3` front matter, as committed in `benchmarks/encoded/*.sheetmark_v03.txt`. After the Cellprose rename the writer emits `cellprose: 0.3`, so re-encoding now gives different bytes (only the front-matter key and the note wording). The committed files and the raw results are what the models saw; they are not regenerated.
