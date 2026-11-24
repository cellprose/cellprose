# Why Cellprose

Models read spreadsheets badly when they only see values. CSV hides which numbers are formulas. The raw `.xlsx` buries them in XML spread over a dozen files. Record formats like TOON drop row and column positions, so a model can no longer say *which* cell it means.

Cellprose keeps the grid with its addresses, and puts the logic in a short block of fill ranges after it. A model reads what the sheet does instead of reverse-engineering it from numbers, and in the benchmark that showed up as accuracy: on 30 real-world workbooks, one call with Cellprose answered 93.8–99.3% of questions correctly, against 65.9–84.1% with CSV, mostly on questions that need a formula. See [the benchmarks](/benchmarks) for the verdicts, intervals and limitations.

Every Cellprose file is valid GitHub-Flavored Markdown, so a workbook renders as tables on GitHub and a change to one cell is a one-line diff.

````markdown
# Sheet: Forecast

## A1:N5

|#|A|B|C|D|E|F|…
|-|-|-|-|-|-|-|…
|2|Bookings|100000|104000|108160|112486|117000|…

```formulas
C2:E2 = B2*(1+$B$7)
G2:I2 = F2*(1+$B$7)
```
````

`F2` is in neither range: it holds a typed number where a formula belongs. That gap is visible in two lines of text; in CSV it is invisible.

## Two ways to use it

Neither is the default. Choose by the size of the workbook and the question.

<div class="two-ways">

| | In the prompt | With its own tools (index first, pick sections) |
| --- | --- | --- |
| **How** | `cellprose encode book.xlsx` or `cellprose.dumps(...)` writes the workbook as text, and you put it in the message. | `cellprose-mcp` gives an agent tools: `index_workbook` for an outline, then `read_ranges`, `find_cells`, `trace_cell`, `whatif`. The model asks for the cells it needs. |
| **Calls** | One. | Several turns. |
| **Use it when** | The workbook fits comfortably in the model's context and you want a one-shot answer, as in a pipeline. | The workbook is large or has many sheets; the question touches a few ranges; you need to trace a formula, try a what-if or edit; or you want to avoid sending cells the question never needs. |
| **Avoid it when** | The text would crowd out the rest of the prompt, or most of it is irrelevant to the question. | A tiny workbook, where one call is simpler than several turns. |
| **Measured, 11 Nov 2026 run** | 93.8–99.3% correct on 30 real-world workbooks, against 65.9–84.1% for CSV and 70.0–85.7% for MarkItDown. Cost per correct answer 0.32–0.60 times MarkItDown's. | Cost per correct answer 0.29–0.79 times that of agents with a shell (Addendum A, 14 of 24 comparisons, three overlapping views). That addendum was decided after the main results were seen. |

</div>

Both read the same text. The first sends it all at once; the second lets the model look things up. The when-to-use advice is guidance: the benchmark did not test where the crossover in workbook size lies. See [the benchmarks](/benchmarks) for the numbers and their limits.

## Quick start

Install from PyPI (from a checkout, use `pip install -e ".[dev]"` instead):

```bash
pip install cellprose
cellprose encode model.xlsx          # writes model.sheet.md
cellprose decode model.sheet.md      # back to .xlsx: values, formulas, formats, merges, names
cellprose check model.sheet.md       # validate without writing anything
cellprose stats model.xlsx           # size as Cellprose vs CSV and Markdown
```

For agents, there is an MCP server and an agent skill:

```bash
pip install "cellprose[mcp]"
claude mcp add cellprose -- cellprose-mcp
```

Or try it without installing anything: the [playground](/playground) converts an `.xlsx` in your browser.

## What it keeps and what it drops

Cellprose keeps values, formulas, number formats, merges, defined names and sheet structure, and converts back to `.xlsx` without losing them. It drops styling (fonts, fills, borders), charts, pivot tables, conditional formatting, data validation, macros, comments and images. The [specification](/reference/spec) lists the limits.
