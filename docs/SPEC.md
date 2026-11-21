# Cellprose v0.3 — Specification

*Working name. File extensions: `.sheet.md` (the default a writer uses) and `.cellprose.md`. A reader treats the two identically, and a writer writes whichever name it is given.*

> Status: v0.3. A v0.3 reader also reads v0.2 files (§3). This file defines the format that `src/cellprose/writer.py` writes and `src/cellprose/reader.py` reads. The format decisions and the evidence behind them are in [DESIGN.md](DESIGN.md). Every example below is a test fixture in `tests/golden/spec/`, and `tests/test_spec.py` fails if an example here differs from its fixture or if the writer stops producing it byte for byte.

Cellprose is a plain-text format for spreadsheet workbooks. It is written to be read by language models and humans, diffed with git, and converted back to `.xlsx` without losing values or formulas.

Every Cellprose file is valid GitHub-Flavored Markdown, so it renders anywhere Markdown does.

The key words MUST, SHOULD and MAY are used in the RFC 2119 sense.

---

## 1. Goals

1. **Cheap to get right.** A model reaches a correct answer for fewer total tokens than with CSV, Markdown tables or TOON.
2. **Lossless core.** Values, formulas, number formats, merges, defined names and sheet structure survive `xlsx → cellprose → xlsx` (limits in §12).
3. **Addressable.** Every cell has an A1 address that is visible in the file, so a model can cite `Revenue!C5` and a tool can write back to it.
4. **Diffable.** One workbook has exactly one canonical serialization. Changing one cell changes one line.
5. **Readable.** A person can open the file on GitHub and understand the model without a spreadsheet app.

### Non-goals

Cell styling (fonts, fills, borders), charts, pivot tables, conditional formatting, hyperlinks, macros, Power Query and images. A writer drops them, but counts the ones it can see in the front matter `note` (§3) so a reader knows they existed. Cell comments and data validation are carried (§8).

---

## 2. File layout

```
front matter            (YAML, required)
# Sheet: <name>         (one per sheet, in workbook order)
  meta block            (optional)
  ## <range>            (one per rectangular region)
    grid                (GFM table, no outer pipes: values)
    elided block        (compact profile only)
    formulas block      (optional)
    formats block       (optional)
  cells block           (optional: single cells outside every region)
  formats block         (optional: number formats of those loose cells)
  merges block          (optional)
  arrays block          (optional: array formulas)
  comments block        (optional: cell comments)
  validation block      (optional: data validation rules)
# Names                 (optional: defined names)
  names block
```

Machine-readable metadata lives in fenced code blocks whose info string names the block type: `meta`, `formulas`, `formats`, `cells`, `merges`, `arrays`, `comments`, `validation`, `names`, `elided`. Everything else is the grid. A reader MUST ignore, with a warning, any block type it does not know.

Blocks and headings are separated by exactly one blank line.

### Smallest file

<!-- golden: 01_minimal.sheet.md -->
````markdown
---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Sales

## A1:C3

#|A|B|C
-|-|-|-
1|Region|Units|Price
2|North|120|9.5
3|South|80|10
````

---

## 3. Front matter

```yaml
---
cellprose: 0.3
profile: compact          # only when rows were elided (§9)
source: model.xlsx        # informational; written by the CLI, omitted in the fixtures
note: '...'               # informational, single-quoted
---
```

- `cellprose` — spec version. Required, and always the first key. A writer writes `0.3`. A reader MUST reject a version it does not support; a v0.3 reader supports `0.3` and `0.2`. The format was called Sheetmark before v0.3, and files written then carry the key `sheetmark:` instead of `cellprose:`. A reader MUST accept either key with the same meaning; a writer writes `cellprose`. The two differ only in the grid (§5.2) and in the array-formula block (§8): v0.2 rows have an outer pipe on both sides, and v0.2 has no `arrays` block.
- `profile` — absent means the file is complete (`full`). `compact` means rows were left out (§9); a reader MUST NOT turn a compact file back into a workbook.
- `source`, `note` — informational. `note` explains `?` cells (§5.3), data-table formulas written as values (§12) and dropped features (§12). Readers ignore both.
- A writer that emits a `note` uses these texts, in this order and joined by `; `, so the bytes stay canonical (§10):
  1. `? = formula with no cached value; open and save in Excel or LibreOffice to compute`
  2. `data-table formulas are not supported; their cached values are written as typed values`
  3. `not carried: ` followed by the features the writer dropped, as `N name` joined by `, `, in this order and only when N > 0: `charts`, `images`, `pivot tables`, `conditional formats`, `hyperlinks` (`chart`, `image`, `pivot table`, `conditional format`, `hyperlink` when N is 1). Counts are over the sheets written.

Keys appear in the order above. Front matter is not a full YAML document: one `key: value` per line, no nesting.

### 3.1 Row-number legend

Directly after the front matter, separated by one blank line from it and from the first heading, a writer writes one line of prose when the file has at least one table. It says that the first field of a table row is the row number and not a cell. Two texts, and no others:

- `Note: the first field of each table row is its row number, not a cell; column A is the second field.` when every table starts at column A;
- `Note: the first field of each table row is its row number, not a cell; the second field is the first column letter in the header.` otherwise.

A file with no table has no legend. A reader MUST ignore a line that starts with `Note: the first field of each table row is its row number, not a cell;` without a warning, and MUST accept files that lack it (every v0.3.0 file does). The front matter `cellprose: 0.3` is unchanged, so v0.3.0 readers still read these files, with one "ignored" warning. Why: in E30 Haiku 5.5 counted the row-number field as column A and answered one column too far right on address questions in wide tables; the legend raised its address accuracy from about 72% to 88–90% on two question sets (experiments/E31) for about 28 tokens. Writers MAY offer an option to leave the legend out (the Python and JavaScript writers do) to reproduce v0.3.0 text.

---

## 4. Sheets

```markdown
# Sheet: P&L
```

The sheet heading is `# Sheet: ` followed by the sheet name. A name containing `#` or a line break is written in double quotes: `# Sheet: "Q1 #2"`.

Optional sheet metadata comes right after the heading:

````markdown
```meta
hidden: true
freeze: B2
```
````

`hidden` is `true` for a hidden sheet or `veryHidden` for a very hidden one, and is omitted for a visible sheet. `freeze` is the top-left unfrozen cell. Keys appear in that order.

---

## 5. Regions and the grid

The non-empty cells of a sheet are grouped into rectangular **regions**. Each region has a heading that gives its range, then a grid.

```markdown
## A1:F4
```

Every non-empty cell of the sheet is in exactly one region or in the `cells` block (§8).

### 5.1 Region detection

Because region boundaries decide the bytes, they are normative:

1. Find the connected components of non-empty cells, with 8-connectivity (a cell touches the eight cells around it).
2. Take the bounding box of each component. While two boxes overlap, replace them by their joint bounding box.
3. A box holding exactly one cell is a **loose cell** (§8). Every other box is a region.
4. Regions are written in order of their top-left cell, row first and then column.

Two blocks of cells with at least one empty row or column between them are therefore two regions; an example is `A1:H2` and `A4:B4` in the fixture in §6.3. A merged range is not special: only its top-left cell holds a value.

### 5.2 Grid shape

The grid is a GFM table without outer pipes and without padding. The header row is `#` then the column letters of the region, in order. The separator row is `-` for each column, including the row-number column. Each following row is the row number, then one value per column.

```markdown
#|A|B|C
-|-|-|-
2|North|120|9.5
```

- Columns and rows are contiguous across the region's range. A row with no cells in it is written with empty values.
- Trailing empty cells are left out of a row (`2|North` for a row whose B and C are empty), and a reader pads the row back to the header's width. A row with nothing but its number is written `5|` so it stays a table row.
- No spaces around pipes and no padding. (Padding makes a one-cell edit rewrite a whole column in a diff, and costs tokens.)
- A table ends at the first blank line. A writer always leaves one after it.
- A row label and a column letter together are the cell's address: in the table above, `2|North|120|9.5` puts 120 in `B2`.
- GitHub renders this as the same table as the v0.2 form with outer pipes: GFM makes the outer pipes optional and pads short rows.

### 5.3 Value encoding

| Type | Encoding | Example |
|---|---|---|
| Empty | nothing between the pipes | `\|\|` |
| Integer | decimal digits | `1200`, `-5` |
| Decimal | shortest round-trip decimal (Python `repr`), possibly with an exponent | `0.125`, `-3.2e-07` |
| Boolean | `TRUE` or `FALSE` | `TRUE` |
| Date | ISO 8601 | `2026-10-07` |
| Date-time | ISO 8601 with seconds, no zone | `2026-10-07T14:30:05` |
| Time of day | `HH:MM:SS` | `09:05:00` |
| Error | the Excel error literal | `#DIV/0!`, `#N/A`, `#REF!` |
| Formula with no cached value | `?` | `?` |
| Formula whose result is the empty string | nothing between the pipes (`""` after `# ` in a `cells` block) | `\|\|` |
| Text | as is, after the escaping below | `Revenue` |

- **Typed-in values are exact.** Numbers that are not formula results are written in full.
- **Formula results are rounded to 6 significant figures** (`1515987.648` → `1515990`, `0.2466666667` → `0.246667`). Exponent notation is used only below `1e-4` or from `1e15`. The rounded value is for reading; a reader recomputes formulas, so nothing is lost on a round trip. An integer-valued result is written as an integer.
- **Date-times are ISO whatever the cell's number format.** A date-time at midnight is written as a date. A cell holding a date has its format listed in a `formats` block, so the display format survives.
- **A formula that calculated to the empty string (`""`) is written as an empty cell**, not `?`. It has a cached value, so it adds no `note:` and needs no recalculation. The `formulas` block still lists the formula, which is what tells it from an empty cell.
- **`?` means the workbook had no cached value for that formula.** This is normal for files written by code. Opening and saving the workbook in a spreadsheet app fills them in (`cellprose encode` can do it with LibreOffice).

#### Escaping text

Text that would otherwise read as another type is prefixed with `'`, as Excel does. That covers a number, a date or date-time, a time of day, `TRUE`/`FALSE`, `?`, an error literal, anything that starts with `=`, and anything that already starts with `'`. A leading `'` in the text is kept after the prefix, so `'quoted` is written `''quoted`.

After that, in order:

1. `\` becomes `\\`, `|` becomes `\|`, and a literal `<br>` becomes `\<br>`.
2. Every line break (LF, CRLF or CR) becomes `<br>`.
3. Text with leading or trailing whitespace, or that starts with `"`, is wrapped in double quotes with inner `"` doubled. A quoted cell is always text.

<!-- golden: 04_values.sheet.md -->
````markdown
---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Types

## A1:B21

#|A|B
-|-|-
1|Kind|Value
2|Integer|1200
3|Decimal|0.125
4|Small|-3.2e-07
5|Boolean|TRUE
6|Date|2026-10-07
7|Date-time|2026-10-07T14:30:05
8|Time|09:05:00
9|Error|#DIV/0!
10|Empty
11|Text|Revenue
12|Looks numeric|'00123
13|Looks like a formula|'=not a formula
14|Looks boolean|'TRUE
15|Pipe|a\|b
16|Backslash|C:\\dir\\
17|Line break|line1<br>line2
18|Literal tag|1 \<br> 2
19|Padded|" padded "
20|Quoted|"""hello"""
21|Leading apostrophe|''quoted

```formats
B6 = yyyy-mm-dd
B7 = yyyy-mm-dd hh:mm:ss
B8 = hh:mm:ss
```
````

#### Reading a cell

A reader splits the row on `|` that is not preceded by an escaping `\` (a v0.2 row also has an empty piece before its first pipe and after its last, which is dropped), then reads each cell as follows:

1. Empty text is an empty cell.
2. If the cell starts and ends with `"`, strip them, turn `""` into `"`, resolve the escapes (step 3), drop one leading `'`, and the result is text.
3. Otherwise, if it starts with `'`, drop that character and resolve the escapes: `\\` → `\`, `\|` → `|`, `\<` → `<`, and `<br>` → LF. The result is text.
4. Otherwise it is typed by its text: `TRUE`/`FALSE`, an error literal, a number, an ISO date or date-time, a time of day, or else text with the escapes resolved.

Line breaks therefore read back as LF.

---

## 6. Formulas

Formulas follow their region's grid in a `formulas` block. The grid shows each formula cell's rounded result; the block shows how it is computed.

````markdown
```formulas
C2:E2 = B2*(1+Growth)
F2 = SUM(B2:E2)
```
````

- **Single cell:** `F2 = SUM(B2:E2)`.
- **Fill range:** `C2:E2 = B2*(1+Growth)`. The formula is written as it reads in the range's top-left cell (the **anchor**, `C2`) and is filled over the rectangle, shifting relative references as Excel's fill handle does: `D2 = C2*(1+Growth)`, `E2 = D2*(1+Growth)`. `$` locks a column, a row or both, as in Excel.
- The text after ` = ` is the formula as the workbook stores it, without its leading `=`: A1 syntax, English function names, `,` between arguments. A formula is never wrapped in quotes.
- Cross-sheet references use Excel syntax: `Assumptions!$B$3`, `'P&L'!C5`. Defined names are written by name (`Growth`).
- Entries are sorted by anchor, row first and then column.

### 6.1 Writing fill ranges

Within a region, take the formula cells in row-major order. For each one not yet covered, extend a run to the right while the next cell's formula equals the anchor's formula shifted to that cell; then extend the run downward while every cell of the next row's span matches the same way. The resulting rectangle is one entry. Fill ranges therefore never cover a typed-in cell or a formula that differs, and the same workbook always yields the same entries.

### 6.2 Reading fill ranges

These rules are for people and models reading the file. A fill range is a list of cells, not a pointer to the cell before it.

1. **Every cell inside the range holds a formula, and that includes the anchor.** `G2:H2 = F2*(1+$B$4)` means G2 and H2 are both formulas. G2 is not an input and not an empty cell.
2. **To get the formula of a cell**, find the entry whose range contains it. Take the entry's formula and move every relative reference by the cell's offset from the anchor: one column right for each column right of the anchor, one row down for each row below. The anchor itself is the formula as written.
3. **Each range stands alone.** A range after a gap starts a new chain. It is not a continuation of the range before it, and its anchor is written with its own precedents.
4. **A cell with a value and no entry is typed in**, whatever its neighbours are. A cell that sits between two ranges of the same row and is in neither is a typed-in override of a pattern.
5. **Precedents are the cells a formula refers to**, not the cells around it. A range such as `B4:E4` in `SUM(B4:E4)` means all four cells.

### 6.3 Example: a typed-in override

`F2` is typed in (117000). The formulas on either side of it are two separate ranges. G2, the anchor of the second one, reads `F2*(1+$B$4)`: it is a formula, and its precedents are the typed-in `F2` and the growth rate `B4`.

<!-- golden: 03_override_gap.sheet.md -->
````markdown
---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Forecast

## A1:H2

#|A|B|C|D|E|F|G|H
-|-|-|-|-|-|-|-|-
1|Line|Jan|Feb|Mar|Apr|May|Jun|Jul
2|Bookings|100000|104000|108160|112486|117000|121680|126547

```formulas
C2:E2 = B2*(1+$B$4)
G2:H2 = F2*(1+$B$4)
```

## A4:B4

#|A|B
-|-|-
4|Monthly growth|0.04

```formats
B4 = 0%
```
````

| Cell | In the grid | Covered by | Formula | Precedents |
|---|---|---|---|---|
| `B2` | 100000 | nothing | typed in | none |
| `C2` | 104000 | `C2:E2` (anchor) | `B2*(1+$B$4)` | `B2`, `B4` |
| `E2` | 112486 | `C2:E2` | `D2*(1+$B$4)` | `D2`, `B4` |
| `F2` | 117000 | nothing | typed in | none |
| `G2` | 121680 | `G2:H2` (anchor) | `F2*(1+$B$4)` | `F2`, `B4` |
| `H2` | 126547 | `G2:H2` | `G2*(1+$B$4)` | `G2`, `B4` |

### 6.4 Example: a small model

Two sheets, a cross-sheet reference, a defined name, a frozen pane and a currency format.

<!-- golden: 02_model.sheet.md -->
````markdown
---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Assumptions

## A1:B3

#|A|B
-|-|-
1|Driver|Value
2|Growth|0.12
3|Price|45

```formats
B2 = 0%
```

# Sheet: P&L

```meta
freeze: B2
```

## A1:F4

#|A|B|C|D|E|F
-|-|-|-|-|-|-
1||Q1|Q2|Q3|Q4|Total
2|Units|1200|1344|1505.28|1685.91|5735.19
3|Price|45|45|45|45
4|Revenue|54000|60480|67737.6|75866.1|258084

```formulas
C2:E2 = B2*(1+Growth)
F2 = SUM(B2:E2)
B3:E3 = Assumptions!$B$3
B4:E4 = B2*B3
F4 = SUM(B4:E4)
```

```formats
B4:F4 = $#,##0
```

# Names

```names
Growth = Assumptions!$B$2
```
````

---

### 6.5 Array formulas

An array formula fills a block of cells from one formula, `{=A1:A2*2}` over `B1:B2`. The grid shows each cell's result, like any formula cell. An `arrays` block, after `merges`, holds the formulas:

````markdown
```arrays
B1:B2 = A1:A2*2
```
````

- Each line is `RANGE = FORMULA`, one per array, in row-major order of the range's top-left cell. The range is the whole array; a single-cell array is written as one address (`H10 = SUM(A1:A2)`).
- The formula belongs to the top-left cell. A reader gives that cell the array formula and leaves the other cells of the range as the values the grid shows, which is how a workbook stores them. Results are written like other formula results (rounded to 6 significant figures, `?` when there is none).
- Excel's dynamic-array formulas (`FILTER`, `SORT`, spilled ranges) are stored in the workbook as array formulas over the range they filled, so they come through the same way. Writing one back gives an ordinary array formula; Excel shows it with braces and no longer spills it.
- A reader that does not know the block ignores it with a warning (§2) and still sees the results as typed values.

<!-- golden: 08_arrays.sheet.md -->
````markdown
---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Arrays

## A1:C2

#|A|B|C
-|-|-|-
1|1|2|x
2|2|4

```arrays
B1:B2 = A1:A2*2
```
````

---

## 7. Number formats

Number formats matter to meaning (`0.12` against `12%`), so they are part of the core.

````markdown
```formats
B2 = 0%
B4:F4 = $#,##0
```
````

- Each line is `RANGE = FORMAT`. The format is the workbook's format string, written raw to the end of the line, with no quotes.
- Only cells that hold a value and have a format other than `General` are listed. Ranges are built like fill ranges (§6.1), grouping cells with equal formats, and sorted the same way.
- A `formats` block follows its region's `formulas` block. Formats of loose cells go in a second `formats` block after the `cells` block (§8).

---

## 8. Loose cells, merges and names

**Loose cells** are single non-empty cells that touch no other cell. They are listed in a `cells` block in row-major order:

````markdown
```cells
A1: Quarterly report
F4: 2026-12-25
F6 = B6*2  # 8000
```
````

- A value is `ADDRESS: VALUE`, encoded as in §5.3.
- A formula is `ADDRESS = FORMULA`, followed by two spaces, `# ` and its rounded result (`?` if there is none, `""` if it is the empty string). A reader ignores the result.
- Number formats of loose cells are in a `formats` block straight after the `cells` block. A reader applies them to the cells above; a date without a listed format reads back as `yyyy-mm-dd`, a date-time as `yyyy-mm-dd hh:mm:ss` and a time as `hh:mm:ss`.

**Merges** are listed in a `merges` block, one range per line, sorted as text. Only the top-left cell of a merged range holds a value.

````markdown
```merges
A1:C1
```
````

**Comments** are listed in a `comments` block after `arrays`, one per line in row-major order. The text is escaped as in §5.3 (backslash, pipe and `<br>` for line breaks); the author is not kept.

````markdown
```comments
C3: Excludes one-offs.<br>Check with \| finance
```
````

**Data validation** is listed in a `validation` block after `comments`: `RANGE = TYPE[ OPERATOR]: FORMULA1[ ; FORMULA2]`, one line per range, sorted as text. `TYPE` and `OPERATOR` are the workbook's own words (`list`, `whole`, `decimal`, `date`, `time`, `textLength`, `custom`; `between`, `notBetween`, `equal`, `lessThan` and so on). A rule with no operator is written without one. The formulas are written raw. Rules of type `any` are left out.

````markdown
```validation
B2:B3 = list: "Yes,No"
C2 = whole between: 0 ; 100
```
````

<!-- golden: 07_comments_validation.sheet.md -->
````markdown
---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Budget

## A1:C3

#|A|B|C
-|-|-|-
1|Item|Status|Qty
2|Pens|Yes|5
3|Ink|No|120

```comments
C3: Excludes one-offs.<br>Check with \| finance
```

```validation
B2:B3 = list: "Yes,No"
C2 = whole between: 0 ; 100
```
````

**Defined names** close the file in a `# Names` section, workbook-level names first (sorted by name), then sheet-scoped names written `Sheet!Name` (sorted by sheet name, then name):

````markdown
# Names

```names
Growth = Assumptions!$B$2
Notes!Local = Notes!$B$1
```
````

<!-- golden: 05_loose_merges_hidden.sheet.md -->
````markdown
---
cellprose: 0.3
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: "Q1 #2"

## A3:C6

#|A|B|C
-|-|-|-
3|Item|Cost|Share
4|Rent|900|0.225
5|Wages|3100|0.775
6|Total|4000

```formulas
C4 = B4/B6
C5 = B5/B6
B6 = SUM(B4:B5)
```

```formats
C4:C5 = 0.0%
```

```cells
A1: Quarterly report
F2: Prepared by finance
F4: 2026-12-25
F6 = B6*2  # 8000
```

```formats
F4 = yyyy-mm-dd
F6 = #,##0
```

```merges
A1:C1
```

# Sheet: Notes

```meta
hidden: true
```

## A1:B1

#|A|B
-|-|-
1|secret|1

# Names

```names
Notes!Local = Notes!$B$1
```
````

---

## 9. Compact profile

For large sheets sent to a model, a writer MAY elide the middle rows of a region. The file then has `profile: compact`. A region keeps its first rows and its last rows (the CLI keeps the last 3) and shows one marker row in between. An `elided` block states which rows are missing.

<!-- golden: 06_compact.sheet.md -->
````markdown
---
cellprose: 0.3
profile: compact
---

Note: the first field of each table row is its row number, not a cell; column A is the second field.

# Sheet: Log

## A1:B13

#|A|B
-|-|-
1|Day|Visits
2|D01|10
3|D02|20
…|…|…
11|D10|100
12|D11|110
13|D12|120

```elided
rows: 4-10  # 7 rows not shown
```
````

The `formulas` and `formats` blocks still cover every row, so a reader can reconstruct the logic of elided rows. Compact files are for reading, not for round trips: a reader MUST refuse to build a workbook from one.

Summaries of elided rows (types, ranges, distinct counts) are not part of the format yet.

---

## 10. Canonical form

To make diffs meaningful, a writer MUST:

- Emit sheets in workbook order, regions in the order of §5.1, and block entries in the orders given above.
- Use LF line endings and UTF-8, and end the file with one newline.
- Separate blocks and headings with exactly one blank line.
- Use the exact representations of §5.3, §6, §7 and §8.

Two conforming writers given the same workbook (with the same cached values) MUST produce the same bytes.

---

## 11. Conformance

- **Reader:** parses any complete file and reconstructs values, formulas (by expanding fill ranges), number formats, merges, defined names, sheet order, visibility and frozen panes. It does not read cached results back; they are recomputed by a spreadsheet app.
- **Writer:** produces canonical output (§10).
- **Round trip:** for a file *F* produced by a conforming writer, `write(read(F)) == F`, once the formulas have cached values again (for example through LibreOffice) and ignoring the `not carried` note, which counts features the file cannot bring back.

The fixtures in `tests/golden/spec/` are the first conformance cases. The conformance kit in [`conformance/`](../conformance/README.md) extends them to a language-neutral suite: workbooks as JSON, the exact expected text, the expected decoded cells for readers, and a checker that runs your encoder and decoder as programs. The format is frozen as 1.0 when two independent writers pass it.

---

## 12. Known limits

What a file does not carry, so a writer or a model should say so rather than guess:

- **Data-table formulas are not supported.** Excel's what-if `{=TABLE(...)}` has no syntax. A writer writes the cached value as a typed value (or `?` if there is none), emits a warning, and adds a `note:` to the front matter. Reading such a file back loses the formula. (Array formulas are supported, §6.5.)
- **Cached results are not restored on decode.** A decoded workbook has no values in its formula cells until a spreadsheet app computes them.
- **Line breaks in text read back as LF.**
- **Number formats are carried for every cell with a value**, whether in a region or loose, but not for empty cells.
- **External-workbook links are not carried.** A formula such as `VLOOKUP(F4,'[1]Master'!$A$4:$C$545,2,FALSE)` is written as it is, but the link behind `[1]` is not, and a spreadsheet app cannot recompute it. When a decoder writes the `.xlsx` it keeps the formula as written, caches the result shown in the grid, adds an `externalLink` part for each `[n]` (a placeholder file name, so Excel opens the file and offers to update links) and warns.
- **Empty text and empty formulas.** A cell holding `""` is an empty cell and takes no part in region detection. A cell whose formula is empty (`<f></f>`, which LibreOffice writes for a lone `=`) is the text `=`. Defined names with no target are left out.
- **Dropped features** (§1, non-goals) are counted in the front matter `note` (§3), not described. Hyperlinks and conditional formatting rules are counted only when the writer's library reads them. Comment authors and validation messages (prompts, error text) are not kept.
- **Large sheets** are written in full unless the writer is asked for the compact profile; there is no summary of long tables.

---

## Appendix A — Changes

### Row-number legend (§3.1)

The legend was added during v0.3, before the v0.3 release: files written before it carry the same `cellprose: 0.3` header without the legend line, and readers accept both. Benchmark id `cellprose_v03` is the text with the legend and `cellprose_v03_nolegend` the text without; the Python and JavaScript writers write the legend by default and `legend=False` omits it.

### v0.2 to v0.3

| Area | v0.2 | v0.3 |
|---|---|---|
| Grid | `\|#\|A\|B\|` and `\|2\|Units\|1200\|`: an outer pipe on each side of every row | `#\|A\|B` and `2\|Units\|1200`: no outer pipes, trailing empty cells left out, an empty row is `5\|` |
| Elision marker | `\|…\|…\|` | `…\|…` |
| Array formulas | Not supported: cached values as typed values, with a warning | An `arrays` block (§6.5); data-table formulas stay unsupported |
| Comments, validation, dropped features | Dropped silently | `comments` and `validation` blocks (§8); the `note` counts what is dropped (§3) |
| Reader | Reads `0.2` | Reads `0.2` and `0.3` |

The pipe-less grid is what E19 tested on 14 workbooks and three models: accuracy was unchanged, billed input fell 4.5% on Claude and 2.9% on GPT, and cost per correct answer showed no difference. GitHub renders the same table.

### v0.1 to v0.2

| Area | v0.1 draft | v0.2 |
|---|---|---|
| Grid | Padded table, `\| # \| A \|`, with a `profile` line and a `not_preserved` list | Compact table `\|#\|A\|`, no padding; no `profile: full`, no `not_preserved`, no `sheets:` list |
| Region heading | `## Table "Name" A3:N12` or `## Range A3:N12` | `## A3:N12` only; Excel table names are not kept |
| Formula results | Cached value, shortest round trip | Rounded to 6 significant figures |
| Formulas | As in v0.1, plus `F3# = ...` spill syntax | Same blocks and fill ranges; no spill syntax (arrays unsupported, §12) |
| Number formats | Quoted, `"#,##0"` | Raw, `#,##0`; loose cells keep theirs |
| Dates | ISO only when the cell format is a date format | ISO whenever the value is a date or date-time |
| Text escaping | `'` prefix | Adds `\\`, `\|`, `\<br>`, `<br>` for line breaks and double quotes for padded text |
| Compact profile | `elided` block with per-column summaries | `elided` block names the missing rows only |
| Open questions | Inline formulas, label headers, final name | Settled by benchmark in DESIGN.md, except the name |

## Appendix B — Region detection

§5.1 is deliberately simple and deterministic. A smarter detector (for example SpreadsheetLLM's structural anchors, Tian et al., 2024) may change where regions begin and end without changing the format, but then the bytes for a given workbook change too; a writer that does this MUST NOT claim to be canonical.
