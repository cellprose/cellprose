---
name: cellprose
description: Read, explain, audit or edit Excel workbooks (.xlsx, .xlsm) by converting them to Cellprose, a compact text form with cell addresses, formulas and number formats. Use whenever a task involves understanding a spreadsheet's numbers or logic, tracing formulas, finding typed-in overrides, or checking what a change would affect.
---

# Cellprose

Cellprose (`.sheet.md`) is a Markdown text form of a workbook. It shows values with their cell addresses and lists every formula, so you can reason about a spreadsheet without guessing its logic from numbers. It usually takes fewer tokens to get right than CSV or a screenshot of the sheet.

## 1. Convert the workbook

If the `cellprose` MCP tools are available, use them: `index_workbook`, then `read_ranges` for only the cells you need (`find_cells` and `trace_cell` help locate and follow them; `read_workbook` for a small file in one go), then `whatif` to try a change or `write_cells` to make one. Otherwise run the bundled script:

```bash
python3 scripts/cellprose_encode.py book.xlsx              # whole workbook to stdout
python3 scripts/cellprose_encode.py book.xlsx --sheet P&L  # one sheet
python3 scripts/cellprose_encode.py book.xlsx --range A1:H40 --max-rows 100
```

The script needs `openpyxl`. If the file was written by code and its formulas have no cached values, the script computes them with LibreOffice when it is installed; otherwise those cells show `?`.

For large workbooks, read one sheet or range at a time rather than the whole file.

## 2. Read it

````markdown
# Sheet: P&L                 <- a sheet

## A1:F4                     <- a block of cells on that sheet

#|A|B|C|D|E|F               <- column letters; rows have no outer pipes, and trailing empty cells are left out
-|-|-|-|-|-|-
1||Q1|Q2|Q3|Q4|Total
2|Units|1200|1296|1399.68|1511.65|5407.33   <- row 2; B2 = 1200
4|Revenue|54000|58320|62985.6|68024.4|243330

```formulas
C2:E2 = B2*(1+Growth)        <- C2 = B2*(1+Growth), D2 = C2*(1+Growth), E2 = D2*(1+Growth)
B4:E4 = B2*B3                <- fill range: references shift like Excel's fill handle
F4 = SUM(B4:E4)
```

```formats
B4:F4 = $#,##0
```

# Names

```names
Growth = Assumptions!$B$2    <- named ranges used in formulas
```
````

Rules that matter:

- **Address cells as `Sheet!C4`.** The column letter comes from the header, the row number from the first column. Don't count rows yourself.
- **Fill ranges shift.** In `B4:E4 = B2*B3`, the formula is written for B4 and shifts across. `$B$7` stays fixed and `B$7` keeps its row.
- **Every cell in a fill range is a formula, the first one included.** `G2:I2 = F2*(1+$B$7)` means G2, H2 and I2 are formulas. G2 reads `F2*(1+$B$7)`, so its precedents are F2 and B7. It is never empty and never an input. To read a cell's formula, find the line whose range contains it and shift the references by the cell's distance from the first cell.
- **Typed-in versus calculated.** A cell with a value that is in no formula range is a typed-in input. A gap inside a run of fill ranges marks a typed-in override: `C2:E2` then `G2:I2` means F2 was typed over. Each range stands alone: `G2:I2` is not a continuation of `C2:E2`.
- **Values of formula cells are rounded to 6 significant figures.** For exact figures, recompute from the formulas.
- **Text that looks like a number is prefixed with `'`.** For example, `'00123` is text. Errors appear as `#DIV/0!` and so on.
- **`?` means a formula with no computed value.**
- **```elided means rows were left out** to save space. The formulas block still covers every row.

## 3. Common tasks

- **Explain a number:** find its cell, read its formula, then follow each referenced cell back to typed-in inputs. Cite cells as `Sheet!A1`.
- **Audit:**
  - look for gaps in fill ranges (overrides)
  - look for formulas that break a row's pattern
  - look for hard-coded numbers inside formulas (`=B4*1.18`)
  - look for references to empty cells, and `#REF!` or other errors
- **What-if:** with the MCP server, call `whatif` (cell plus `value` or `factor`). It changes nothing on disk, recalculates with LibreOffice, and lists every other cell whose value would change. If LibreOffice is missing it says so; `write_cells` does the same on a saved copy. Without it, trace dependents by hand from the formulas block.
- **Edit:** prefer `write_cells`, which writes a new file by default. If you edit with openpyxl yourself, change formulas as strings starting with `=`, and say that charts, images and pivot tables may be dropped on save.

## 4. Commit-friendly copies

`.sheet.md` files render as tables on GitHub and diff line by line. To keep a readable twin of a workbook in a repo:

```bash
python3 scripts/cellprose_encode.py model.xlsx -o model.sheet.md
```
