# E16: CSV vs Sheetmark across seven models, 14 workbooks, 2 repeats

**Date:** 2026-10-09 · **Type:** benchmark (first multi-model, multi-repeat run through the direct-API runner) · **Status:** done. 392 of 392 calls succeeded.

## Question

Across vendors and model tiers, does `sheetmark_lean_gfm` reach correct answers for fewer total tokens and lower cost than CSV? (CLAUDE.md goal 1.)

## Setup

| Item | Value |
| --- | --- |
| Models | `haiku45` (`claude-haiku-4-5-20251001`, thinking budget 16,000), `haiku55`, `sonnet55`, `opus55` (adaptive thinking; effort `medium`, `high` for Sonnet; exact settings in [models.py](../benchmarks/runner/models.py)), `gpt6luna`, `gpt61sol`, `gpt6astra` (Responses API, effort `medium`). `fable51` was left out on request |
| Workbooks | all 14 in `benchmarks/questions/` |
| Encodings | `csv`, `sheetmark_lean_gfm` (the other nine encodings and `none` were not run) |
| Repeats | 2 (`r0`, `r1`), in one invocation, run id in the raw files |
| Calls | 392 = 7 models × 14 workbooks × 2 encodings × 2 repeats |
| Cost | estimated $11.58 expected (cap $10 per vendor, enforced by `--vendor-cap-usd`); actual $5.29 (Anthropic $3.36, OpenAI $1.93) |
| Pricing | uncached list price. GPT prices were supplied by the owner and are **unverified**; OpenAI caching cannot be disabled and some calls reported cached input (priced at the full input rate here) |

Questions, ground truth and workbooks are unchanged, so these runs are comparable with each other (same invocation) but not with E09 (Claude CLI), E13 or E15 (different invocations).

## Results

Per-repeat means over all 14 workbooks. Accuracy is the mean question score; the two repeats are in brackets. Tokens and cost are summed over the 14 workbooks for one repeat (mean of the two). Output tokens include reasoning.

| Model | Encoding | Accuracy % (r0 / r1) | Input tokens | Output tokens | Cost (r0 / r1) |
| --- | --- | --- | --- | --- | --- |
| haiku45 | csv | 88.5 (87.0 / 89.9) | 19,928 | 92,983 | $0.4848 ($0.5009 / $0.4688) |
| haiku45 | sheetmark_lean_gfm | 97.3 (96.9 / 97.7) | 25,344 | 67,758 | $0.3641 ($0.3685 / $0.3598) |
| haiku55 | csv | 90.4 (85.9 / 94.9) | 23,681 | 21,084 | $0.0129 ($0.0129 / $0.0129) |
| haiku55 | sheetmark_lean_gfm | 99.3 (98.9 / 99.8) | 29,463 | 14,628 | $0.0103 ($0.0102 / $0.0103) |
| sonnet55 | csv | 98.8 (98.7 / 98.9) | 23,681 | 10,550 | $0.1529 ($0.1493 / $0.1564) |
| sonnet55 | sheetmark_lean_gfm | 99.4 (98.9 / 100.0) | 29,463 | 8,872 | $0.1477 ($0.1491 / $0.1462) |
| opus55 | csv | 98.1 (98.9 / 97.2) | 23,681 | 8,082 | $0.2564 ($0.2593 / $0.2535) |
| opus55 | sheetmark_lean_gfm | 100.0 (100.0 / 100.0) | 29,463 | 6,630 | $0.2504 ($0.2436 / $0.2572) |
| gpt6luna | csv | 95.5 (95.9 / 95.1) | 17,911 | 12,798 | $0.0082 ($0.0082 / $0.0082) |
| gpt6luna | sheetmark_lean_gfm | 98.9 (98.9 / 98.9) | 22,525 | 10,160 | $0.0073 ($0.0073 / $0.0073) |
| gpt61sol | csv | 98.4 (97.8 / 98.9) | 17,911 | 4,192 | $0.0777 ($0.0790 / $0.0764) |
| gpt61sol | sheetmark_lean_gfm | 98.9 (98.9 / 98.9) | 22,525 | 3,344 | $0.0785 ($0.0782 / $0.0788) |
| gpt6astra | csv | 97.8 (97.8 / 97.8) | 17,911 | 4,230 | $0.3906 ($0.3860 / $0.3952) |
| gpt6astra | sheetmark_lean_gfm | 100.0 (100.0 / 100.0) | 22,525 | 3,553 | $0.4029 ($0.4023 / $0.4035) |

### Sheetmark versus CSV, per model

| Model | Accuracy (points) | Input tokens | Output tokens | Input + output | Cost |
| --- | --- | --- | --- | --- | --- |
| haiku45 | +8.8 | +27% | -27% | -18% | -25% |
| haiku55 | +8.9 | +24% | -31% | -1% | -20% |
| sonnet55 | +0.6 | +24% | -16% | +12% | -3% |
| opus55 | +1.9 | +24% | -18% | +14% | -2% |
| gpt6luna | +3.4 | +26% | -21% | +6% | -11% |
| gpt61sol | +0.5 | +26% | -20% | +17% | +1% |
| gpt6astra | +2.2 | +26% | -16% | +18% | +3% |

## Reading

- **Accuracy:** sheetmark was equal or higher on every model in both repeats on average, and higher in both repeats for 6 of 7 models. The largest gains are on the two Haiku models (about 9 points). The small models' CSV scores also vary most between repeats (`haiku55` CSV 85.9 vs 94.9), so those gains are the least certain in size, though both repeats point the same way for Sheetmark. The gaps for `sonnet55` and `gpt61sol` (0.5-0.6 points) are within the repeat-to-repeat spread.
- **Input tokens:** sheetmark uses about 24-27% more input than CSV on every model (row numbers, column letters, formula and format blocks).
- **Output tokens:** lower on every model (16-31%), mostly because reasoning shrinks.
- **Total tokens (input + output):** lower for Haiku 4.5 (-18%) and about even for Haiku 5.5, higher for the rest (+6% to +18%). So on tokens alone the goal is met only where reasoning dominates.
- **Cost:** lower for 5 of 7 models (-2% to -25%) and slightly higher for the two GPT models with the highest input share (`gpt61sol` +1%, `gpt6astra` +3%), both within spread. The cost gap follows the output-to-input price ratio and how much the model reasons.
- **Cost per correct answer** (cost divided by accuracy) is lower for sheetmark on the other five models and about 0.5-1% higher for `gpt61sol` and `gpt6astra`, i.e. level within spread.

## Limits (to state next to any number from this run)

Two repeats (so "spread" is two values, not a confidence interval); two encodings only; 14 workbooks that the format was designed around; effort and thinking settings fixed at one level per model, so a different effort could change both reasoning tokens and the winner; GPT prices unverified and the Sol alias (`gpt-6.1-sol`) assumed; OpenAI cached input present in some calls (priced uncached); token counts are not comparable across vendors (different tokenizers). Accuracy is the repo scorer's partial-credit mean, not exact-match. `fable51` not run. Not comparable with E09, E13 or E15.

## Reproduce

```bash
cd benchmarks
python3 api_run.py --models haiku45,haiku55,sonnet55,opus55,gpt6luna,gpt61sol,gpt6astra \
  --encs csv,sheetmark_lean_gfm --reps 2 --out results/e16-grid --vendor-cap-usd 10
RESULTS_DIR=results/e16-grid python3 score.py
RESULTS_DIR=results/e16-grid python3 analyze.py
```
