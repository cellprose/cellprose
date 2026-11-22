# E29: first live run of the API agent loop (smoke test)

> **Ids (renamed 9 Nov 2026).** This file was written with the ids `sheetmark_v03` (v0.3 text without the row-number legend) and `sheetmark_v031` (with it). They are now `cellprose_v03_nolegend` and `cellprose_v03`; `agent_` variants likewise. Raw results keep the old ids and score unchanged. "v0.3.1" below means the text with the legend.

**Status:** done (2026-11-07). The agent loop works on both vendors; Tier 1 can run.

## Question
Does the API agent loop (`benchmarks/api_agent.py`, `runner/agent.py`) work against the live APIs before Tier 1 depends
on it (docs/PROTOCOL.md section 0, to-build item 4)? This is a harness check, not a result: three development
workbooks, one repeat, no claim.

## Setup
- Workbooks: the `--sample` set (`01_sales_log`, `04_saas_model`, `11_forecast_overrides`), 20 questions.
- Variants: `agent_xlsx` and `agent_sheetmark_v03`. Limits: 40 turns, $1 per call, $2 per vendor.
- Models: `haiku55`, `sonnet55`, `gpt6luna`, `gpt61sol`, all in one invocation (run `20261107T085402Z-a9f169`).
- Estimate before the run (`--estimate-only`): $0.72 for 24 calls. Covered by the owner's Tier 1 approval ($70 cap).

```
python3 api_agent.py --sample --models haiku55,sonnet55,gpt6luna,gpt61sol \
  --variants agent_xlsx,agent_sheetmark_v03 --out results/e29_smoke_all --vendor-cap-usd 2 --allow-dirty --workers 4
RESULTS_DIR=results/e29_smoke_all python3 score.py
```

## Result
24 calls, 0 failures, $0.26 in all (Anthropic $0.16, OpenAI $0.10). Every call ended with an answer in 2 to 5 turns.
No Anthropic call read or wrote the prompt cache.

| Model | Variant | Calls | Turns per call | Input tokens per call | Output tokens per call | Cost | Accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Haiku 5.5 | agent_sheetmark_v03 | 3 | 2.3 | 6,758 | 1,222 | $0.0039 | 99.8 |
| Haiku 5.5 | agent_xlsx | 3 | 2.7 | 13,931 | 1,479 | $0.0064 | 94.9 |
| Sonnet 5.5 | agent_sheetmark_v03 | 3 | 2.3 | 4,651 | 707 | $0.0491 | 99.9 |
| Sonnet 5.5 | agent_xlsx | 3 | 2.7 | 13,972 | 653 | $0.1034 | 99.9 |
| GPT-6 Luna | agent_sheetmark_v03 | 3 | 2.0 | 2,785 | 633 | $0.0018 | 94.8 |
| GPT-6 Luna | agent_xlsx | 3 | 3.3 | 15,094 | 1,012 | $0.0060 | 99.9 |
| GPT-6.1 Sol | agent_sheetmark_v03 | 3 | 2.3 | 3,659 | 268 | $0.0300 | 99.9 |
| GPT-6.1 Sol | agent_xlsx | 3 | 2.7 | 7,850 | 388 | $0.0587 | 99.9 |

Input tokens include the ones OpenAI served from its automatic cache, priced as uncached (PROTOCOL section 2).
Three workbooks and one repeat say nothing about which variant is better; the accuracy column is only there to show that
answers are parsed and scored.

## Problems found
1. **SDKs not installed** in this environment (`pip install -e ".[bench]"` had not been run). The first attempt failed
   before any call. Fixed by installing them; not a code change.
2. **Key name.** The environment holds the Anthropic key as `SHEETMARK_ANTHROPIC_KEY`, the name from before the rename;
   the runner read only `ANTHROPIC_API_KEY` and `CELLPROSE_ANTHROPIC_KEY`. Fixed: `runner/providers.py` accepts the
   old name last, with a test.
3. **Anthropic credit balance too low** on 2026-11-06: all Haiku and Sonnet calls returned HTTP 400, nothing billed.
   The owner added credit and updated the keys on 2026-11-07, and the whole test was rerun in one invocation.
   The partial runs of 2026-11-06 and the Anthropic-only retry are kept in `results/e29_smoke/` as a record and are not
   used.

## Conclusion
The agent loop works end to end on both vendors. On these small workbooks it used fewer tokens than the CLI-based
averages the estimator assumes (about 12,600 and 26,500 input tokens per call), so the Tier 1 agent estimate is, if
anything, high.
