# E15: Sample run for Opus 5.5 and three GPT models

**Date:** 2026-10-09 · **Type:** benchmark tooling · **Status:** done. 24 of 24 calls succeeded; this is a plumbing check for the new models, not a headline result.

## Question

Do `opus55` and the OpenAI provider (`gpt6luna`, `gpt61sol`, `gpt6astra`) run through the same runner, `score.py` and `analyze.py` as E13, with usage recorded and uncached list-price cost computed? ([E13](E13-api-runner-sample.md) did the same for the Anthropic 4.5/5.5 models.)

## Setup

| Item | Value |
| --- | --- |
| Models | `opus55` = `claude-opus-5-5` (adaptive thinking, effort `medium`); `gpt6luna` = `gpt-6-luna`, `gpt61sol` = `gpt-6.1-sol`, `gpt6astra` = `gpt-6-astra` (Responses API, reasoning effort `medium`). `max_tokens` 32,000 for all |
| Prices (list, $/M in / out) | Opus 5.5 $4 / $20. GPT: Luna $0.10 / $0.50, Sol $2 / $10, Astra $10 / $50. **The GPT prices were supplied by the owner and not checked against OpenAI's pages** (the container cannot reach them). "GPT-6 Sol (6.1)" was taken to mean `gpt-6.1-sol` |
| Caching | Anthropic: off. OpenAI: automatic caching cannot be disabled; no call reported cached input, and every input token is priced uncached either way |
| Workbooks / encodings | `01_sales_log`, `04_saas_model`, `11_forecast_overrides` × `csv`, `sheetmark_lean_gfm` (the E13 sample) |
| Calls | 24 (4 models × 3 × 2), one repeat, one invocation, run id `20261009T100925Z-507269` |
| Cost | $0.94 expected, $15.67 theoretical worst case; actual $0.42 |

## Results

Raw files: [`benchmarks/results/e15-sample/`](../benchmarks/results/e15-sample/). Totals over the 3 workbooks (20 questions), uncached list price. Output tokens include reasoning tokens, shown in brackets.

| Model | Encoding | Accuracy (%) | Input tokens | Output tokens (reasoning) | Cost |
| --- | --- | --- | --- | --- | --- |
| opus55 | csv | 94.5 | 7,460 | 1,780 (1,271) | $0.0654 |
| opus55 | sheetmark_lean_gfm | 99.9 | 8,959 | 1,714 (1,147) | $0.0701 |
| gpt6luna | csv | 93.0 | 5,707 | 3,327 (3,024) | $0.0022 |
| gpt6luna | sheetmark_lean_gfm | 94.7 | 6,983 | 2,376 (2,042) | $0.0019 |
| gpt61sol | csv | 98.0 | 5,707 | 900 (546) | $0.0204 |
| gpt61sol | sheetmark_lean_gfm | 95.0 | 6,983 | 977 (637) | $0.0237 |
| gpt6astra | csv | 98.0 | 5,707 | 1,029 (639) | $0.1085 |
| gpt6astra | sheetmark_lean_gfm | 100.0 | 6,983 | 1,214 (847) | $0.1305 |

Total $0.42. Observations about the plumbing:

- `score.py` ran unchanged. `analyze.py` needed one more change: it picked the usage row by the family names "haiku"/"sonnet" and crashed with `StopIteration` on `opus55` and the GPT files. It now takes the only model in a runner file. Re-running it on the E13 sample still works.
- Every GPT call returned reasoning-token counts, as did Opus 5.5. The OpenAI tokenizer count (`o200k_base`) of system plus user text was 5,674 / 6,950 tokens per three-workbook total against 5,707 / 6,983 billed, i.e. about 11 tokens per call of request overhead.
- Opus 5.5 and Sonnet 5.5 (E13) billed identical input tokens (7,460 and 8,959), so they share a tokenizer.
- Accuracy rests on 20 questions per cell with one call each, so a single wrong answer moves a cell by 5 points or more. No spread is available. The sheetmark-versus-CSV differences, including the cells where sheetmark scored lower (`gpt61sol`), are within that noise.

## Limits (to state next to any number from this run)

Three workbooks, one repeat, two encodings, one invocation. A plumbing check, not a headline result. This run was a separate invocation from E13, so its numbers are not comparable with E13's or E09's; no cross-experiment ranking is made. GPT prices are unverified, the Sol alias is an assumption, and OpenAI input tokens are counted by the vendor's own tokenizer, so token totals are not comparable between vendors.

## Reproduce

```bash
cd benchmarks
export ANTHROPIC_API_KEY=...   # or SHEETMARK_ANTHROPIC_KEY; never commit or print keys
export OPENAI_API_KEY=...
python3 api_run.py --sample --models opus55,gpt6luna,gpt61sol,gpt6astra --out results/e15-sample
RESULTS_DIR=results/e15-sample python3 score.py
RESULTS_DIR=results/e15-sample python3 analyze.py
```
