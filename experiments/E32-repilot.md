# E32: re-pilot after the Tier 1 gate failure (v0.3.1 legend, fresh Enron set)

> **Ids (renamed 9 Nov 2026).** This file was written with the ids `sheetmark_v03` (v0.3 text without the row-number legend) and `sheetmark_v031` (with it). They are now `cellprose_v03_nolegend` and `cellprose_v03`; `agent_` variants likewise. Raw results keep the old ids and score unchanged. "v0.3.1" below means the text with the legend.

**Status:** done (2026-11-07). Pre-run note written before any call on this set; results below. **Gate: passed** (all three criteria), with the deviations listed.

## Question
E30 failed gate criterion 3 on Haiku 5.5 (address questions one column too far right). E31 found that a one-line row-number
legend (SPEC §3.1, `sheetmark_v031`) lifts Haiku's address accuracy on development data. Does the PROTOCOL section 0.1 gate pass
with `sheetmark_v031` on data nobody has run: the `rw3_` set?

## Frozen before the run
- Protocol: `docs/PROTOCOL.md` unchanged (freeze/tier2.json digest unchanged). Gate unchanged.
- Data: `benchmarks/external/realworld3/` (15 Enron workbooks, one per author, none selected or screened by rw2_; 90 questions drawn by
  the rules of `realworld2.py`, seed 20261107). Freeze manifest `benchmarks/freeze/pilot2.json`, digest
  `4f3f302ab7cff3345aaaa61f67432ae4eb086307a27d1326288523b262b2a588`.
- Format: writer revision 0.3.1 (legend), commit of this branch. `sheetmark_v03` (v0.3.0 bytes) is not run in this set.
- Arms: one-shot `sheetmark_v031`, `markitdown`, `csv`, `none`; agent `agent_xlsx`, `agent_sheetmark_v031`. Models `haiku55`,
  `sonnet55`, `gpt6luna`, `gpt61sol`, 2 repeats, caching off, uncached pricing. Agent limits 40 turns, $1 per call.

## Cost
Estimate: one-shot $14.80 (Anthropic $7.96, OpenAI $6.85), agent $7.16, about $22. Hard caps: one-shot
`--max-usd 20 --vendor-cap-usd 12`, agent `--max-usd 12 --vendor-cap-usd 8`. A run stopped by a cap is incomplete and not reported as a result.

## Commands
```
export CELLPROSE_CORPUS=external/realworld3
W=$(ls external/realworld3/questions | sed 's/.json//' | paste -sd,)
python3 api_run.py   --models haiku55,sonnet55,gpt6luna,gpt61sol --workbooks $W --encs sheetmark_v031,markitdown,csv,none --reps 2 --final --out results/e32_repilot --max-usd 20 --vendor-cap-usd 12
python3 api_agent.py --models haiku55,sonnet55,gpt6luna,gpt61sol --workbooks $W --variants agent_xlsx,agent_sheetmark_v031 --reps 2 --final --out results/e32_repilot --max-usd 12 --vendor-cap-usd 8
```

## Deviations known before the run
- The digest was posted publicly after the runs had started: https://gist.github.com/Utkarsh-Gaikwad/ac1c91da72ac8e41355026dc4f48a53e (seen by the thread at 2026-11-07 12:11 UTC; the runs began about 11:50 UTC). The set and manifest were pushed to the repository first (commits f872f5b and e3e0eb8), so the hashes can be checked against the history, but the posting order of PROTOCOL section 0 was not followed.
- `none` runs at 2 repeats in the one-shot invocation, as in E30.
- The set is Enron only, 15 workbooks (no unused Damodaran file is left), unlike the 30-workbook Tier 2 set.

## Limitations
One set of 15 workbooks and 90 questions; one prompt; prices of 2026-11-07; the one-shot against agent-loop caveat of PROTOCOL section 1;
the second legend text (for tables not starting at column A) was not in the E31 A/B and is used by some of these files.

## Results

Run ids (manifests in `benchmarks/results/e32_repilot/runs/`): one-shot `20261107T114821Z-6b64f6`, agent `20261107T114909Z-9d399b`,
resume of Sonnet repeat 1 `20261107T122306Z-d53e1d`, one skipped agent call `20261107T122825Z-468708`. 720 scored calls, **0 failures in
the scored files, 0 agent failures**. Spend **$28.5** (Anthropic about $18.8, OpenAI about $9.7) against an estimate of $22 and caps of $32.
Reproduce: `CELLPROSE_CORPUS=external/realworld3 RESULTS_DIR=results/e32_repilot COMPARE_ENC=sheetmark_v031 python3 score.py && python3 analyze.py`.

### Accuracy and cost per call (2 repeats averaged; 15 workbooks, 90 questions)

| Model | Arm | Accuracy | Mean cost per call | Agent turns |
| --- | --- | --- | --- | --- |
| Haiku 5.5 | sheetmark_v031 | 92.2 | $0.0041 | |
| Haiku 5.5 | markitdown | 65.7 | $0.0183 | |
| Haiku 5.5 | csv | 64.7 | $0.0048 | |
| Haiku 5.5 | agent_xlsx | 93.7 | $0.0092 | 5.8 |
| Haiku 5.5 | agent_sheetmark_v031 | 91.8 | $0.0149 | 6.6 |
| Sonnet 5.5 | sheetmark_v031 | 94.7 | $0.0750 | |
| Sonnet 5.5 | markitdown | 86.3 | $0.1379 | |
| Sonnet 5.5 | csv | 83.3 | $0.1010 | |
| Sonnet 5.5 | agent_xlsx | 94.9 | $0.1243 | 5.0 |
| Sonnet 5.5 | agent_sheetmark_v031 | 93.8 | $0.1359 | 4.9 |
| GPT-6 Luna | sheetmark_v031 | 93.1 | $0.0032 | |
| GPT-6 Luna | markitdown | 68.6 | $0.0058 | |
| GPT-6 Luna | csv | 66.4 | $0.0042 | |
| GPT-6 Luna | agent_xlsx | 95.0 | $0.0086 | 6.0 |
| GPT-6 Luna | agent_sheetmark_v031 | 88.2 | $0.0055 | 5.3 |
| GPT-6.1 Sol | sheetmark_v031 | 95.0 | $0.0532 | |
| GPT-6.1 Sol | markitdown | 86.2 | $0.0839 | |
| GPT-6.1 Sol | csv | 88.1 | $0.0438 | |
| GPT-6.1 Sol | agent_xlsx | 96.0 | $0.0409 | 4.0 |
| GPT-6.1 Sol | agent_sheetmark_v031 | 94.4 | $0.0709 | 4.8 |

(`none` scores 7.8% to 18.5% on these files; Sonnet's 18.5% comes from trace and hardcode questions answered by chance.)

### v0.3.1 against each baseline (cost-per-correct ratio, 95% paired bootstrap over 15 workbooks)

| Model | vs MarkItDown | vs agent_xlsx | vs CSV |
| --- | --- | --- | --- |
| Haiku 5.5 | **0.16 (0.11-0.36) win** | 0.45 (0.27-0.95) no difference | **0.60 (0.50-0.69) win** |
| Sonnet 5.5 | **0.50 (0.39-0.61) win** | 0.61 (0.40-1.16) no difference | **0.65 (0.50-0.80) win** |
| GPT-6 Luna | **0.41 (0.32-0.49) win** | 0.38 (0.22-0.92) no difference | **0.55 (0.41-0.66) win** |
| GPT-6.1 Sol | **0.58 (0.47-0.66) win** | 1.32 (0.84-2.25) no difference | 1.13 (0.91-1.31) no difference |

Accuracy difference, v0.3.1 minus the best baseline (points): Haiku -1.5, Sonnet -0.2, Luna -1.9, Sol -1.0.

### Gate (PROTOCOL section 0.1, with `sheetmark_v031` in the place of `sheetmark_v03`)
1. Harness works: **passed**. 0 agent failures of 240 calls.
2. Promising: **passed**. Against MarkItDown the ratios are 0.16, 0.50, 0.41 and 0.58 with upper bounds 0.36, 0.61, 0.49 and 0.66.
3. No accuracy damage: **passed**. The worst gap to the best baseline is -1.9 points (Luna against `agent_xlsx`); the limit is 3.

So, as fixed in advance, Tier 2 may go ahead; the owner decides. The gate was not changed.

### What the numbers say (exploratory, one 15-workbook set)
- **The Haiku fault is gone on these files.** Haiku address accuracy with v0.3.1 is 100% (30 of 30 answers), against 93.3% for `agent_xlsx` and 66.7% for CSV. E30 had 76.5%.
- **Cellprose beats MarkItDown by a wide margin on this set**, cheaper per correct answer (0.16 to 0.58) and 8 to 27 points more accurate. CSV is much worse on these Enron files (65-88%).
- **Against an agent reading the .xlsx there is still no difference**: v0.3.1 is cheaper on Haiku, Sonnet and Luna on the point estimate (0.38 to 0.61) but the intervals include 1; on Sol the agent is cheaper (1.32, interval 0.84 to 2.25). The agent reading the Cellprose file (`agent_sheetmark_v031`) is not better than the agent reading the xlsx on any model.
- Caveat on the legend text: these files include tables that do not start at column A (the second legend text), which the E31 A/B did not test; the result suggests it works.

### Deviations
- The runs started before the digest was posted publicly (gist `ac1c91da72ac8e41355026dc4f48a53e`, seen at 12:11 UTC; runs began about 11:50 UTC). Files were pushed first (f872f5b, e3e0eb8).
- **The Anthropic account ran out of credit** during Sonnet repeat 1 of the one-shot run. 49 calls were recorded as failures (score 0) and moved to `results/e32_repilot/failed_credit_out/`, none billed. After the account was topped up, only those 49 calls were rerun in a separate invocation (resume run id above), and one agent call skipped at the Anthropic agent cap ($8) was run in another. These calls are not from the same invocation as the rest; the tables above include them. Sonnet repeat 1 therefore comes from a different invocation than Sonnet repeat 0.
- `none` ran at 2 repeats, as in E30.
- The set is Enron only (15 workbooks), unlike the 30-workbook Tier 2 set.

### Limitations
One set of 15 workbooks and 90 questions, so each wrong answer moves a workbook's score by 17 points; two repeats; one prompt; prices of 2026-11-07; the one-shot against agent-loop caveat of PROTOCOL section 1; Anthropic counts v0.3.1 at 1.13x CSV and OpenAI at 1.53x on these files (the files are number-heavy); the format was changed after Tier 1 and the fix was developed on already-seen data (E31), so this is the first data it was tested on.
