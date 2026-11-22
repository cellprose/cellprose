# E03: Where the tokens go: input vs reasoning

**Date:** 2026-10-07 · **Data:** E01 and E02 runs (session 1) · **Status:** method adopted; the specific numbers were inflated (see [E09](E09-same-session-repeats.md))

## Question

Sheetmark files are larger than CSV, so is it really cheaper? The project goal counts the work a model does to make sense of the sheet, not just the file size.

## Method

Each call's tokens are split into input (the prompt, including the workbook) and output (the answer plus the model's reasoning). Output is priced at 5× input on both models. The headline metric became **cost per correct answer**: priced tokens divided by accuracy. This analysis needed no new model calls.

## Results (session 1, mean per call)

| Model | Format | Input tokens | Output tokens |
| --- | --- | --- | --- |
| Haiku | CSV | 4,797 | 12,290 |
| Haiku | Sheetmark v0.1 | 6,553 | 7,554 |
| Sonnet | CSV | 3,152 | 654 |
| Sonnet | Sheetmark v0.1 | 4,066 | 407 |

In this session, Sheetmark had 29–37% more input but 38–39% less output. On Haiku that cut total tokens and roughly halved the cost.

## Problems found

The Haiku output counts in this session were about 5× higher than in later sessions on identical prompts ([E09](E09-same-session-repeats.md)), so the size of the saving here is not reliable. The direction held in every later run: less reasoning with Sheetmark.

## Conclusion

The cost argument for Sheetmark rests on **less reasoning**, not a smaller file. The PRD's headline metric was changed to cost per correct answer, counting input, output and reasoning.

## Reproduce

```bash
cd benchmarks && python3 score.py && python3 analyze.py
```

Usage is read from each raw result's `modelUsage` ([`analyze.py`](../benchmarks/analyze.py)).
