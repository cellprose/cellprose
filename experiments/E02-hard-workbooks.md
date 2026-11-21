# E02: Hard workbooks and the typed-in-vs-formula task

**Date:** 2026-10-07 · **Session:** 1 (repeat `r0`) · **Status:** superseded by [E09](E09-same-session-repeats.md) for headline numbers; the workbooks and task are still in use

## Question

[E01](E01-format-comparison-standard.md) saturated because models guess formulas from labels. When the logic can't be guessed from values, do formats that carry formulas pull ahead?

## Setup

Four new workbooks ([`gen_hard.py`](../benchmarks/gen_hard.py)):

| Workbook | What makes it hard |
| --- | --- |
| `11_forecast_overrides` | Typed-in numbers inside formula rows (May and Sep bookings, July headcount, October payroll). Some overrides equal what the formula would give |
| `12_lookalike_drivers` | Five drivers share the value 3% or 5%, so you can't tell from values which line uses which |
| `13_scenario_switch` | `CHOOSE` picks Base, Upside or Downside. Changing an inactive scenario changes nothing |
| `14_cost_allocation` | Shared costs allocated by drivers on another sheet; two allocations typed in |

There is a new task type, **hardcode**: list the cells in a range that hold typed-in numbers rather than formulas. Everything else is the same as E01: same encodings, models, scorer and one repeat.

## Results

Rescored with the fixed parser ([E06](E06-answer-parser-fix.md)); cost is uncached ([E10](E10-cache-neutral-cost.md)). Changes are relative to CSV.

| Model | Format | Accuracy | Cost per correct answer |
| --- | --- | --- | --- |
| Haiku | CSV | 83.3% | — |
| Haiku | Markdown | 93.5% | −11% |
| Haiku | TOON | 61.6% | +18% |
| Haiku | Sheetmark v0.1 | 100% | −16% |
| Haiku | Sheetmark, formulas inline | 99.7% | −49% |
| Sonnet | CSV | 95.9% | — |
| Sonnet | Markdown | 95.9% | −9% |
| Sonnet | TOON | 95.9% | −5% |
| Sonnet | Sheetmark v0.1 | 100% | −23% |
| Sonnet | Sheetmark, formulas inline | 79.2% | +3% |

**Hardcode task across all 14 workbooks:**
- every Sheetmark variant with a formulas block scored 100% on both models
- CSV and Markdown scored 78%
- TOON scored 56% (Haiku) and 78% (Sonnet)
- the Sheetmark grid without formulas scored 56%
- Sonnet with formulas inline scored 33%

## Conclusion

- **With logic that can't be guessed, the formulas block decides the result.** Sheetmark was the only format at 100% on both models.
- **Inline formulas are unreliable.** Sonnet's hard-set accuracy fell to 79%, the deciding evidence for a separate block.

## Reproduce

```bash
cd benchmarks
python3 gen_workbooks.py && python3 gen_hard.py && python3 ground_truth.py && python3 encoders.py
python3 run.py haiku,sonnet && python3 score.py
```

Raw results: `benchmarks/results/raw/<model>/1[1-4]_*.<encoding>.json`.
