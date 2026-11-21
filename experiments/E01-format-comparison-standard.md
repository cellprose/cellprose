# E01: Format comparison on standard workbooks

**Date:** 2026-10-07 · **Session:** 1 (repeat `r0`) · **Status:** superseded by [E09](E09-same-session-repeats.md) for headline numbers; its format findings still hold

## Question

Do models answer spreadsheet questions more accurately, and for fewer tokens, from Sheetmark than from CSV, Markdown, Markdown key-value or TOON?

## Setup

| Item | Value |
| --- | --- |
| Workbooks | 10 standard, generated in code: sales log, employees, quarterly P&L, SaaS model, multi-sheet model, budget vs actual, messy report, loan schedule, orders with lookups, gradebook ([`gen_workbooks.py`](../benchmarks/gen_workbooks.py)) |
| Ground truth | Recalculated with LibreOffice; impact answers found by perturbing an input and diffing every cell ([`ground_truth.py`](../benchmarks/ground_truth.py)) |
| Tasks | lookup, address, trace (direct precedents), impact (all dependents); 6–8 questions per workbook |
| Encodings | `csv`, `markdown`, `markdown_kv`, `toon`, `grid_values` (Sheetmark grid, no formulas), `sheetmark` (v0.1 padded), `sheetmark_inline`, `sheetmark_labels`, `none` (no workbook, control) ([`encoders.py`](../benchmarks/encoders.py)) |
| Models | Claude Haiku 4.5, Claude Sonnet, via the Claude CLI, no tools ([`run.py`](../benchmarks/run.py)) |
| Repeats | 1 |
| Scoring | Numeric match within 0.5%; exact address; F1 on cell sets ([`score.py`](../benchmarks/score.py)) |

## Results

All numbers are rescored with the fixed parser ([E06](E06-answer-parser-fix.md)). Cost uses uncached prices ([E10](E10-cache-neutral-cost.md)). Changes are relative to CSV.

| Model | Format | Accuracy | Output tokens | Cost per correct answer |
| --- | --- | --- | --- | --- |
| Haiku | CSV | 93.6% | — | — |
| Haiku | Markdown | 99.4% | −12% | −15% |
| Haiku | Markdown key-value | 70.4% | +9% | +51% |
| Haiku | TOON | 71.9% | +2% | +33% |
| Haiku | Sheetmark v0.1 | 99.4% | −56% | −51% |
| Haiku | Sheetmark, formulas inline | 99.2% | −43% | −36% |
| Haiku | Sheetmark, label headers | 99.4% | −34% | −33% |
| Sonnet | CSV | 99.8% | — | — |
| Sonnet | Markdown | 99.6% | −2% | +10% |
| Sonnet | Markdown key-value | 92.6% | +15% | +54% |
| Sonnet | TOON | 97.9% | +10% | +8% |
| Sonnet | Sheetmark v0.1 | 99.6% | −38% | +2% |
| Sonnet | Sheetmark, formulas inline | 99.6% | −31% | +28% |
| Sonnet | Sheetmark, label headers | 100% | −13% | +12% |

The no-workbook control scored 0.4–3.7%, so the questions can't be answered by guessing.

## Problems found

- **The standard set saturated.** Nearly every format scored 94–100%, because models infer formulas like "Revenue = Units × Price" from labels and values. This set can't separate formats on logic questions, which led to [E02](E02-hard-workbooks.md).
- **Key-value and TOON lose positions.** On Haiku, address accuracy fell to 43–50% and trace to 37–52%.
- **The Haiku savings here are inflated.** In this session Haiku spent ~12,000 output tokens per CSV task, about 5× the later sessions ([E09](E09-same-session-repeats.md)).

## Conclusion

- Formats that keep row and column positions beat record-style formats.
- Putting formulas inline costs Sonnet far more input than it saves, which supports the separate formulas block.
- Label headers add tokens without gaining accuracy, which supports letter headers.

## Reproduce

```bash
cd benchmarks
python3 gen_workbooks.py && python3 ground_truth.py && python3 encoders.py
python3 run.py haiku,sonnet
python3 score.py
```

Raw results: `benchmarks/results/raw/<model>/<workbook>.<encoding>.json` (files without a `.rN` suffix).
