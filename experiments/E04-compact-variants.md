# E04: Compact variants: comma code block vs compact pipe table

**Date:** 2026-10-07 · **Session:** 1 · **Status:** decided; the compact pipe table became v0.2

## Question

Can Sheetmark be made smaller without losing accuracy, while still rendering on GitHub?

## Variants

Both variants round formula results to 6 significant figures, trim the front matter, and keep the formulas, formats and names blocks ([`encoders.py`](../benchmarks/encoders.py), `enc_lean`).

| Variant | Grid written as | Renders on GitHub? |
| --- | --- | --- |
| `sheetmark_lean` | Comma-separated rows inside a fenced code block | No (shows as code) |
| `sheetmark_lean_gfm` | Pipe table with no padding spaces: `\|2\|Units\|1200\|` | Yes |

## Size

| Workbook | CSV | v0.1 padded | Comma block | Compact pipe |
| --- | --- | --- | --- | --- |
| 01 sales log (characters) | 8,154 | 11,999 | 8,856 | 9,170 |
| 03 quarterly P&L | 525 | 1,282 | 903 | 941 |
| 08 loan schedule | 1,742 | 2,672 | 1,599 | 1,665 |

The compact pipe table is ~4% larger than the comma block and 24–38% smaller than v0.1.

## Results (session 1, all 14 workbooks, cost uncached, vs CSV in the same session)

| Model | Variant | Accuracy | Cost per correct answer |
| --- | --- | --- | --- |
| Haiku | Comma block | 95.1% | −28% |
| Haiku | Compact pipe | 98.7% | −36% |
| Sonnet | Comma block | 100% | −5% |
| Sonnet | Compact pipe | 99.1% | −7% |

These runs used a draft that wrote sheet headings as `# Report` rather than `# Sheet: Report`. That turned out to be a bug ([E07](E07-sheet-prefix-bug.md)). The runs are archived in `benchmarks/results/archive_v1/` and were re-run with the fix in [E09](E09-same-session-repeats.md).

## Conclusion

- **Choose the compact pipe table.** It renders on GitHub, which serves the accessibility goal, costs ~4% more text than commas, and was as accurate or better.
- **Rounding formula results is safe.** Lookups stayed at 100%.
