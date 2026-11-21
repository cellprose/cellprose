# The format in ten minutes

This page walks through a real file: the forecast workbook from the benchmark, as the writer produces it. The [specification](/reference/spec) is the full definition.

## File layout

Front matter declares the version. Each sheet gets a `# Sheet:` heading, and each rectangular region of the sheet a `##` heading with its range. A `# Names` section closes the file.

```markdown
---
cellprose: 0.3
---

# Sheet: Forecast

## A1:N5
…grid, then formulas and formats…

## A7:B10
…

# Names
…
```

::: tip Keep the `Sheet:` prefix
Without it, Haiku read `# Report` as a document title and invented a sheet named Sheet1.
:::

## Regions and tables

Each region is a compact table without outer pipes. The first column holds row numbers and the header row holds column letters, so every value has an address a model can cite.

```markdown
#|A|B|C|D|E|F|G|H|I|J|K|L|M|N
-|-|-|-|-|-|-|-|-|-|-|-|-|-|-
1|Line|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|FY
2|Bookings|100000|104000|108160|112486|117000|121680|126547|131609|140000|145600|151424|157481|1515990
4|Headcount|40|42|44|46|48|50|52|54|56|58|60|62
```

## The formulas block

Formulas live in a fenced `formulas` block after the table, never inline. Identical formulas shifted across cells collapse into one fill range, written with the formula of its top-left cell.

````markdown
```formulas
C2:E2 = B2*(1+$B$7)
G2:I2 = F2*(1+$B$7)
K2:M2 = J2*(1+$B$7)
N2:N3 = SUM(B2:M2)
C4:G4 = B4+$B$10
I4:M4 = H4+$B$10
```
````

`C2:E2 = B2*(1+$B$7)` means C2 is `B2*(1+$B$7)`, D2 is `C2*(1+$B$7)`, E2 is `D2*(1+$B$7)`: relative references move with the cell, `$` references stay put.

::: tip A gap is a typed-in number
`C2:E2` then `G2:I2` means F2 is not a formula. Here it holds 117,000 where the formula would give 116,986. `C4:G4` then `I4:M4` means H4 is typed in too, even though it holds exactly the value its formula would give, which no values-only format can show.
:::

## Numbers and rounding

- Formula results are rounded to 6 significant figures. They are recomputed from the formulas on decode, so nothing is lost.
- Typed-in values are written exactly. They are the source data.
- Text that would read as something else gets a `'` prefix: `'2026-10-07 plan`, `'TRUE`.
- The serialization is canonical: the same workbook always produces the same bytes.

## Formats and names

Number formats follow the formulas block, as ranges. Defined names go in a `names` block at the end.

````markdown
```formats
B4:F4 = $#,##0
```

# Names

```names
Growth = Assumptions!$B$2
```
````

## Design decisions

| Question | Decision | Evidence |
|---|---|---|
| Formulas inline or in a block? | A block, with fill ranges | Inline cost Sonnet +47% tokens and dropped its accuracy to 94% |
| Column letters or the sheet's own labels? | Column letters | Labels added 20% tokens on Sonnet and gained no accuracy |
| Table style | Compact table, no outer pipes | Renders on GitHub; 24–38% fewer characters than v0.1, and E19 found no accuracy loss without the outer pipes |
| Formula result precision | 6 significant figures | Lookups stayed at 100% |
| Records like TOON? | Rejected | Address accuracy fell to 43–50% on Haiku |

The evidence for each is in the [design notes](/reference/design).

## Cheatsheet

| Write | Means |
|---|---|
| `cellprose: 0.3` | Format version, in the front matter |
| `# Sheet: Name` | Start of a sheet |
| `## A1:F9` | A rectangular region |
| `\|2\|Units\|1200\|` | Row 2: A2 = Units, B2 = 1200 |
| `B4:E4 = B2*B3` | B4 = B2*B3, C4 = C2*C3, … (filled right) |
| `B4:F4 = $#,##0` | Number format for a range |
| `# Names` | Defined names, at the end |
