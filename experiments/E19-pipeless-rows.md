# E19: Grid rows without outer pipes

**Date:** 2026-10-10 · **Type:** benchmark (format variant) · **Status:** done. 252 of 252 calls succeeded, $0.99.

## Question

GFM makes a table's outer pipes optional and pads short rows with empty cells. If the grid drops them (`|2|Units|1200||` becomes `2|Units|1200`), GitHub renders the same table with fewer tokens. Does accuracy hold?

Research before the run, with no model calls: token counts for this and other layout ideas on the 14 workbooks and on 71 SpreadsheetBench workbooks, plus a render check with `cmark-gfm` (GitHub's parser). That work is in the project's `sheetmark-report/format-research.md` and is not repeated here.

## Setup

| Item | Value |
| --- | --- |
| Models | `haiku55`, `sonnet55`, `gpt6luna` (settings as in E16) |
| Workbooks | all 14 |
| Encodings | `sheetmark_lean_gfm` (v0.2 as benchmarked) and `sheetmark_lean_gfm_nopipe` |
| Repeats | 3 (`r0`, `r1`, `r2`), one invocation, run id `20261010T051113Z-1cce47` |
| Calls | 252 = 3 models × 14 workbooks × 2 encodings × 3 repeats |
| Cost | $0.98 expected; $0.99 actual (Anthropic $0.95, OpenAI $0.04); cap $3 per vendor |

`sheetmark_lean_gfm_nopipe` is produced by `encoders.drop_outer_pipes` applied to the **committed** `encoded/*.sheetmark_lean_gfm.txt` files. The two texts differ only in pipes:
- outer pipes are dropped on every grid line;
- trailing empty cells are dropped;
- an empty row keeps one pipe (`5|`).

`cmark-gfm` renders identical tables for all 14 workbooks. The files are 3.8% smaller in characters (35,694 to 34,349).

Questions, ground truth and workbooks are unchanged. The two encodings ran in the same invocation and are comparable with each other. They are not comparable with E16 or E17.

## Results

Totals are summed over the 14 workbooks for one repeat and then averaged over the three repeats. Output includes reasoning. Cost prices every input token as uncached.

| Model | Encoding | Accuracy % (r0 / r1 / r2) | Input | Output | Cost (r0 / r1 / r2) |
| --- | --- | --- | --- | --- | --- |
| haiku55 | v0.2 | 98.9 (99.0 / 98.9 / 98.7) | 29,463 | 14,485 | $0.0102 ($0.0102 / $0.0103 / $0.0100) |
| haiku55 | no outer pipes | 99.2 (98.9 / 98.6 / 100.0) | 28,132 | 15,246 | $0.0104 ($0.0102 / $0.0104 / $0.0107) |
| sonnet55 | v0.2 | 99.6 (100.0 / 99.0 / 99.8) | 29,463 | 9,223 | $0.1512 ($0.1459 / $0.1573 / $0.1503) |
| sonnet55 | no outer pipes | 99.8 (100.0 / 99.7 / 99.7) | 28,132 | 8,937 | $0.1456 ($0.1545 / $0.1395 / $0.1429) |
| gpt6luna | v0.2 | 98.4 (98.8 / 97.8 / 98.8) | 22,525 | 10,071 | $0.0073 ($0.0069 / $0.0079 / $0.0071) |
| gpt6luna | no outer pipes | 98.3 (99.8 / 98.8 / 96.5) | 21,883 | 10,381 | $0.0074 ($0.0069 / $0.0076 / $0.0076) |

### No outer pipes vs v0.2

The paired bootstrap resamples workbooks (10,000 resamples, fixed seed; PROTOCOL.md section 7). A ratio below 1 means the pipe-less layout is cheaper per correct answer.

| Model | Accuracy (points) [95% interval] | Input | Output | Cost | Cost per correct, ratio [95% interval] | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| haiku55 | +0.3 [+0.0, +0.9] | −4.5% | +5.2% | +2.4% | 1.021 [0.967, 1.090] | no difference |
| sonnet55 | +0.2 [−0.3, +1.0] | −4.5% | −3.1% | −3.7% | 0.961 [0.860, 1.056] | no difference |
| gpt6luna | −0.1 [−1.4, +1.1] | −2.9% | +3.1% | +1.3% | 1.013 [0.942, 1.096] | no difference |

Accuracy by task (%), all repeats:

| Model | Encoding | Lookup | Address | Trace | Impact | Typed-in vs formula |
| --- | --- | --- | --- | --- | --- | --- |
| haiku55 | v0.2 | 100.0 | 100.0 | 100.0 | 95.3 | 100.0 |
| haiku55 | no outer pipes | 100.0 | 97.6 | 100.0 | 98.1 | 100.0 |
| sonnet55 | v0.2 | 100.0 | 100.0 | 100.0 | 98.3 | 100.0 |
| sonnet55 | no outer pipes | 100.0 | 100.0 | 100.0 | 99.4 | 100.0 |
| gpt6luna | v0.2 | 100.0 | 100.0 | 93.7 | 99.9 | 100.0 |
| gpt6luna | no outer pipes | 100.0 | 100.0 | 95.2 | 98.1 | 100.0 |

## Reading

- **Accuracy holds.** The change is −0.1 to +0.3 points, and every interval includes zero. That is within the spread between repeats: `gpt6luna` without pipes ranges from 96.5% to 99.8%. Typed-in vs formula stays at 100% on all three models.
- **The one address miss was not a misread position.** Haiku answered `Sheet BvA!F8` for `BvA!F8` in one of three repeats. The cell was right; the sheet name carried a stray `Sheet ` prefix, the slip E07 describes. The row and column, which are what the pipes delimit, were correct.
- **Input falls as the token counts predicted.** Billed input, prompt included, is −4.5% on Claude and −2.9% on GPT.
- **Output and cost moved within noise.** Output changed by −3% to +5% depending on the model, with no consistent direction. Cost per correct answer is "no difference" on all three. The input saving is real but too small next to reasoning variance to show as a cost win in a run of this size.

## Conclusion

Dropping the outer pipes and trailing empty cells is safe for accuracy and saves 3–5% of input. On these 14 workbooks that is not enough to move cost per correct answer measurably. It renders the same on GitHub. Whether v0.3 adopts it is a spec decision; the writer, reader, viewer, JS writer and conformance kit would all change. This experiment does not change DESIGN.md.

## Problems found

- **Four committed `encoded/*.sheetmark_lean_gfm.txt` files differ from what `encoders.py` writes today**: workbooks 06, 11, 12 and 13.
  - 11, 12 and 13 still contain the scientific notation that E11 fixed, for example `1.51599e+06`.
  - 06 has small results with extra digits, for example `-0.0206046` where the encoder now writes `-0.020605`.
  - Every API run so far (E13–E19) read these committed files. They were left as they are so the runs stay comparable, and E19's pipe-less files were built from them.
  - Regenerating them would change the benchmarked text. That should be a separate, stated change.

## Limits

Three repeats, three cheaper models, 14 workbooks built alongside the format, and one invocation. GPT prices are unverified.

## Reproduce

```bash
cd benchmarks
python3 api_run.py --models haiku55,sonnet55,gpt6luna --encs sheetmark_lean_gfm,sheetmark_lean_gfm_nopipe \
  --reps 3 --out results/e19-nopipe --vendor-cap-usd 3
RESULTS_DIR=results/e19-nopipe python3 score.py
RESULTS_DIR=results/e19-nopipe python3 compare_encodings.py sheetmark_lean_gfm_nopipe sheetmark_lean_gfm
```

`analyze.py` needs a `csv` baseline in the run, so `compare_encodings.py` does the head-to-head instead. Raw results are in [`benchmarks/results/e19-nopipe/`](../benchmarks/results/e19-nopipe/).
