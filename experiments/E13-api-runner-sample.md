# E13: Direct-API runner, sample run

**Date:** 2026-10-09 · **Type:** benchmark tooling · **Status:** done. The sample ran end to end (18 of 18 calls, 0 failed) and `score.py` ran unchanged; `analyze.py` crashed in its agent section; fixed afterwards (see Problems).

## Question

Does the direct-API runner ([`benchmarks/api_run.py`](../benchmarks/api_run.py)) produce raw files that `score.py` and `analyze.py` read, with the exact model ID, settings and usage of every call recorded and prompt caching off?

## Setup

| Item | Value |
| --- | --- |
| Models | `haiku45` = `claude-haiku-4-5-20251001`, `haiku55` = `claude-haiku-5-5`, `sonnet55` = `claude-sonnet-5-5` (the Models API lists `claude-haiku-5-5` and `claude-sonnet-5-5` with no dated snapshot IDs, so the aliases are the only pin available) |
| Settings | Haiku 4.5: thinking budget 16,000. Haiku 5.5: adaptive thinking, effort `medium`. Sonnet 5.5: adaptive thinking, effort `high`. `max_tokens` 32,000. No `cache_control`; any cache activity is an error |
| Workbooks | `01_sales_log`, `04_saas_model`, `11_forecast_overrides` (small, mid-size, hard) |
| Encodings | `csv`, `sheetmark_lean_gfm` |
| Calls | 18 (3 models × 3 workbooks × 2 encodings), one repeat, one invocation, one run id |
| Expected cost | $0.38 expected, $3.02 worst case (input tokens counted by the API, output from E09 means); actual $0.29 |
| Endpoint | `api.anthropic.com`, passed explicitly; the key is read from `ANTHROPIC_API_KEY` or else `SHEETMARK_ANTHROPIC_KEY`, with an `anthropic-workspace-id` header from `SHEETMARK_ANTHROPIC_WORKSPACE_ID` |

## Results

Run id `20261009T071817Z-5abf8a`, one invocation, 18 calls, 0 failed, no cache activity. Raw files are in [`benchmarks/results/sample/`](../benchmarks/results/sample/). Totals are over the 3 workbooks (20 questions each set of 3), priced at list price with no caching.

| Model | Encoding | Accuracy (%) | Input tokens | Output tokens | Cost |
| --- | --- | --- | --- | --- | --- |
| haiku45 | csv | 61.8 | 6,294 | 19,789 | $0.1052 |
| haiku45 | sheetmark_lean_gfm | 94.9 | 7,721 | 16,675 | $0.0911 |
| haiku55 | csv | 98.0 | 7,460 | 5,658 | $0.0036 |
| haiku55 | sheetmark_lean_gfm | 99.9 | 8,959 | 3,559 | $0.0027 |
| sonnet55 | csv | 98.0 | 7,460 | 2,595 | $0.0409 |
| sonnet55 | sheetmark_lean_gfm | 100.0 | 8,959 | 2,408 | $0.0420 |

Total cost $0.29. The API did not report a separate reasoning-token count, so output tokens include thinking.

**Pipeline checks.**
- `score.py` ran unchanged on the runner's raw files (`RESULTS_DIR=results/sample`) and wrote `scores.csv` and `summary.csv` there; the committed `results/scores.csv` and `headline.json` were not touched.
- `analyze.py` printed its one-shot tables, then crashed at `analyze.py:73` with `ValueError: No objects to concatenate`, because the sample has no `agent_xlsx` runs. So it did **not** run unchanged. A later commit skips the agent table when there are no agent runs; the sample's `headline.json` was written by that fixed version and is committed beside the raw files. The fix leaves the other tables as they were.

## Problems

- `analyze.py` needed agent data (fixed, above). Separately, re-running `analyze.py` on the committed `results/` rewrites `headline.json` with 111 changed lines, before and after the fix, so the committed file was not produced by the current scripts and data. Not investigated; the file was left as committed.
- The Models API shows no dated snapshots for the 5.5 models, so nothing was pinned.
- The sandbox sets `ANTHROPIC_BASE_URL`, and the key is not tied to a workspace. The runner ignores the variable and sends the workspace header instead.

## Limits (to state next to any number from this run)

Three workbooks, one repeat, two encodings (one invocation, 18 calls): a plumbing check, not a headline result. Every figure above is a mean over a handful of answers with no spread, and the haiku45 csv gap in particular rests on single calls. Nothing here is comparable with the E09 numbers, which came from the Claude CLI.

## Reproduce

```bash
cd benchmarks
export ANTHROPIC_API_KEY=...        # or SHEETMARK_ANTHROPIC_KEY; never commit or print it
export SHEETMARK_ANTHROPIC_WORKSPACE_ID=...   # only if the key needs a workspace header
python3 api_run.py --sample --models haiku45,haiku55,sonnet55
RESULTS_DIR=results/sample python3 score.py
RESULTS_DIR=results/sample python3 analyze.py
```
