# E30: Tier 1 pilot

> **Ids (renamed 9 Nov 2026).** This file was written with the ids `sheetmark_v03` (v0.3 text without the row-number legend) and `sheetmark_v031` (with it). They are now `cellprose_v03_nolegend` and `cellprose_v03`; `agent_` variants likewise. Raw results keep the old ids and score unchanged. "v0.3.1" below means the text with the legend.

**Status:** done (2026-11-07). Pre-run note written before any call; results below. **Gate: not passed** (criterion 3).

## Question
docs/PROTOCOL.md section 0: per model, is Cellprose 0.3 (`sheetmark_v03`, one-shot) cheaper per correct answer than
MarkItDown (one-shot) and an agent reading the `.xlsx` (`agent_xlsx`), and does the harness hold up well enough for
Tier 2? The gate in section 0.1 decides whether Tier 2 runs. This is a **pilot on data already seen** (the 17 `rw_`
workbooks were run in E26 and E27), so its numbers are exploratory.

## Frozen before the run
- Protocol: `docs/PROTOCOL.md` at `13f2495` (PR #56). Tier 2 set frozen in PR #57, digest
  `75cd9074f5eb8f9a161a9b70429102699017cc0708aad7c4e75f79cbcb777be2`, posted publicly on 2026-11-07
  (https://gist.github.com/Utkarsh-Gaikwad/c4b9640699628275531123cbe93987b2), before this run started.
- Harness check: E29 (24 agent calls, 0 failures, both vendors).

## Setup
- Data: 17 `rw_` workbooks, 67 questions (`benchmarks/external/realworld/`), all of them (no subset).
- Models: `haiku55` (claude-haiku-5-5), `sonnet55` (claude-sonnet-5-5), `gpt6luna` (gpt-6-luna), `gpt61sol`
  (gpt-6.1-sol). Settings as pinned in `runner/models.py`.
- Prices re-checked on the vendors' pages on 2026-11-07, all match the registry: Haiku 5.5 $0.10/$0.50 per 1M
  ($0.50/$2.50 above 100k prompt tokens), Sonnet 5.5 $2/$10, GPT-6 Luna $0.10/$0.50, GPT-6.1 Sol $2/$10.
- Arms: one-shot `sheetmark_v03`, `markitdown`, `csv`, `none`; agent `agent_xlsx`, `agent_sheetmark_v03`.
  Agent limits: 40 turns, $1 per call. 2 repeats.
- Two invocations started the same day (PROTOCOL section 5.2): one `api_run.py` for every one-shot arm, one
  `api_agent.py` for both agent arms.

```
export CELLPROSE_CORPUS=external/realworld
W=$(ls external/realworld/questions | sed 's/.json//' | paste -sd,)
python3 api_run.py   --models haiku55,sonnet55,gpt6luna,gpt61sol --workbooks $W \
  --encs sheetmark_v03,markitdown,csv,none --reps 2 --final --out results/e30_tier1 --max-usd 24 --vendor-cap-usd 20
python3 api_agent.py --models haiku55,sonnet55,gpt6luna,gpt61sol --workbooks $W \
  --variants agent_xlsx,agent_sheetmark_v03 --reps 2 --final --out results/e30_tier1 --max-usd 10 --vendor-cap-usd 15
```

## Cost
- Estimate (`--estimate-only`, 2026-11-07): one-shot $20.28 (worst case $87.28), `none` $0.40, agent $8.11 (worst
  case $272, bounded by the caps). Expected total about $29.
- Caps: $20 per vendor for the one-shot run and $15 per vendor for the agent run, so at most $70 in all, the owner's
  approved cap. A run stopped by a cap is incomplete and is not reported as a result.
- The agent estimate uses per-call averages from the small dev workbooks; the `rw_` files are larger, so the agent
  spend is the least certain number here.

## Deviations known before the run
- `none` runs at 2 repeats, not once (section 5.3), so that every one-shot arm is in the same invocation. It adds about
  $0.40 and changes nothing else.

## Results

Run ids: one-shot `api_run.py` and agent `api_agent.py`, both started 2026-11-07 08:58 UTC (manifests in
`benchmarks/results/e30_tier1/runs/`). 816 calls, **0 failures** (no turn-limit, cost-cap, refusal or cache errors).
Spend **$30.98** (Anthropic about $18, OpenAI about $13), against an estimate of $29 and a cap of $70.
Reproduce the tables: `CELLPROSE_CORPUS=external/realworld RESULTS_DIR=results/e30_tier1 python3 score.py && python3 analyze.py`.

### Per arm (2 repeats averaged; 17 workbooks, 67 questions)

| Model | Arm | Accuracy | Mean cost per call | Cost per call / accuracy | Agent turns per call |
| --- | --- | --- | --- | --- | --- |
| Haiku 5.5 | sheetmark_v03 | 91.4 | $0.0123 | $0.0134 |  |
| Haiku 5.5 | markitdown | 83.6 | $0.0166 | $0.0198 |  |
| Haiku 5.5 | csv | 80.0 | $0.0087 | $0.0109 |  |
| Haiku 5.5 | agent_xlsx | 98.9 | $0.0050 | $0.0051 | 3.9 |
| Haiku 5.5 | agent_sheetmark_v03 | 91.6 | $0.0043 | $0.0047 | 4.0 |
| Haiku 5.5 | none | 4.5 | $0.0002 | n/a |  |
| Sonnet 5.5 | sheetmark_v03 | 99.7 | $0.1000 | $0.1002 |  |
| Sonnet 5.5 | markitdown | 93.1 | $0.1245 | $0.1337 |  |
| Sonnet 5.5 | csv | 94.9 | $0.1016 | $0.1070 |  |
| Sonnet 5.5 | agent_xlsx | 97.6 | $0.1137 | $0.1165 | 4.6 |
| Sonnet 5.5 | agent_sheetmark_v03 | 98.8 | $0.1144 | $0.1157 | 4.7 |
| Sonnet 5.5 | none | 8.6 | $0.0025 | $0.0292 |  |
| GPT-6 Luna | sheetmark_v03 | 98.9 | $0.0042 | $0.0042 |  |
| GPT-6 Luna | markitdown | 84.4 | $0.0049 | $0.0058 |  |
| GPT-6 Luna | csv | 82.3 | $0.0041 | $0.0050 |  |
| GPT-6 Luna | agent_xlsx | 98.4 | $0.0031 | $0.0031 | 3.9 |
| GPT-6 Luna | agent_sheetmark_v03 | 97.5 | $0.0036 | $0.0037 | 4.8 |
| GPT-6 Luna | none | 2.2 | $0.0006 | n/a |  |
| GPT-6.1 Sol | sheetmark_v03 | 98.6 | $0.0773 | $0.0784 |  |
| GPT-6.1 Sol | markitdown | 99.3 | $0.0825 | $0.0831 |  |
| GPT-6.1 Sol | csv | 98.7 | $0.0678 | $0.0687 |  |
| GPT-6.1 Sol | agent_xlsx | 98.6 | $0.0246 | $0.0250 | 2.7 |
| GPT-6.1 Sol | agent_sheetmark_v03 | 98.6 | $0.0331 | $0.0336 | 3.6 |
| GPT-6.1 Sol | none | 0.0 | $0.0016 | n/a |  |

"Cost per call / accuracy" is the protocol's cost per correct answer (section 2), all tokens priced uncached.

### v0.3 against each baseline (cost-per-correct ratio, 95% paired bootstrap over workbooks)

Ratio below 1 means v0.3 is cheaper per correct answer.

| Model | vs MarkItDown | vs agent_xlsx | vs CSV |
| --- | --- | --- | --- |
| GPT-6 Luna | **0.75 (0.62–0.90) win** | 1.37 (0.80–3.26) no difference | 0.88 (0.70–1.05) no difference |
| GPT-6.1 Sol | 0.94 (0.81–1.09) no difference | **3.14 (2.21–4.72) loss** | 1.14 (1.02–1.27) loss |
| Haiku 5.5 | **0.70 (0.38–0.99) win** | 2.68 (0.72–8.65) no difference | 1.28 (0.78–2.63) no difference |
| Sonnet 5.5 | **0.76 (0.67–0.85) win** | 0.85 (0.54–2.25) no difference | 0.94 (0.84–1.04) no difference |

Accuracy differences (v0.3 minus baseline, points): Luna +13.0 vs MarkItDown, -0.1 vs agent; Sol -0.4, 0.0;
Haiku +4.9, **-8.8**; Sonnet +6.0, +2.9.

### Gate (PROTOCOL section 0.1)

1. **Harness works: passed.** 0 agent failures of 272; no scoring bug found.
2. **Promising: passed.** Against MarkItDown, Luna 0.75 (upper bound 0.90), Haiku 0.70 (0.99) and Sonnet 0.76 (0.85) all meet
   "point estimate 0.85 or lower, upper bound under 1.05".
3. **No accuracy damage: failed.** On Haiku 5.5, v0.3 is 8.8 points less accurate than the best baseline (`agent_xlsx`,
   99.2 against 90.4); the limit is 3.

So, as fixed before the run, **Tier 2 does not run on this plan**; the owner decides what happens next. The gate is not
changed.

### What the numbers say (exploratory, data already seen)

- **Against the converter people use (MarkItDown), Cellprose wins on three of four models**, cheaper per correct answer by
  about a quarter and more accurate (Luna +13 points). Sol is a tie.
- **Against an agent reading the .xlsx, one-shot Cellprose is not cheaper.** The agent looks at only the cells it needs, so
  on these files it costs less per call on Haiku, Luna and Sol (Sol about 3x less, 2.7 turns per call). Only on
  Sonnet is v0.3 cheaper on the point estimate (0.85), and the interval is wide. This is the main caveat of section 1
  showing up in the data.
- **Haiku's accuracy gap is address questions in wide tables** (v0.3 76.5% against 100% for the agent). The wrong answers are
  one column to the right (H418 for G418, F241 for E241, F38 for E38, BQ114 for BP114),
  plus one answer that kept the `Sheet:` prefix of the heading. Haiku miscounts columns across a row of the compact table.
  MarkItDown's errors on the same questions are one *row* off instead. The same gap shows with the Cellprose file inside
  the agent (`agent_sheetmark_v03`, 76.5%), so it is about reading the format, not about one-shot versus agent.
- `none` (no workbook) scores 0 to 9%, so the answers are not guessable or remembered; Sonnet's 14.5% on lookups is the
  highest and worth noting for the public files.

### Deviations
- `none` ran at 2 repeats instead of 1 (stated before the run).
- The run used the OpenAI key present when the session started; the owner had saved a new key a few minutes later. Same
  models and prices, so no effect on results.

### Limitations
Pilot on 17 workbooks that were already run in E26 and E27; one prompt; prices of 2026-11-07; the one-shot against
agent-loop caveat of PROTOCOL section 1; savings differ by tokenizer (Anthropic counts v0.3 at 1.18x CSV, OpenAI at 1.23x).
