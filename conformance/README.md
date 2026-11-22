# Cellprose v0.3 conformance kit

A suite for proving that an independent **writer** (workbook → `.sheet.md`) or **reader** (`.sheet.md` → cells) follows [`docs/SPEC.md`](../docs/SPEC.md) byte for byte. It is language-neutral: the kit is JSON and text files, and the checker runs your implementation as a program.

26 cases cover escaping, fill ranges and overrides, formula-result rounding, region detection, merges, names, sheet states, loose-cell formats, array-formula fallback, and reader-side rejection. Cases 01–06 are the spec's own examples (identical to `tests/golden/spec/`); the rest are new.

## Run it

You need Python 3.8+ and nothing else (the checker uses only the standard library).

```bash
python conformance/check.py --encoder "node my-encode.js" --decoder "./my-decode"
```

Pass either flag or both. The checker appends one path to each command:

| Side | Command | Input | You must |
|---|---|---|---|
| Writer | `ENCODER workbook.json` | A workbook in the JSON form below | Print the `.sheet.md` text to stdout, UTF-8, LF line endings. Exit 0. Write warnings to stderr. |
| Reader | `DECODER file.sheet.md` | A Cellprose file | Print the decoded workbook (form below) as JSON to stdout and exit 0, **or** exit non-zero for a file the spec says to reject. |

Useful options: `--list` (show cases), `--only 07 08` (run some, by id or prefix), `-v` (full diffs), `--validate` (check the kit itself). Exit status is 0 when every check passes, 1 when any fails.

A passing writer produces identical bytes for all 19 writer cases. A passing reader decodes 23 files to the expected cells and rejects the 2 it must reject (the compact-profile file and the unsupported version). One of the 23 has an unknown block that the reader must ignore with a warning.

The JavaScript writer in [`js/`](../js/README.md) passes all 19 writer cases:

```bash
python conformance/check.py --encoder "node js/bin/cellprose-encode.js"
```

The Python reference implementation is wired up as an example of the interface:

```bash
python conformance/check.py \
  --encoder "python conformance/reference/encode.py" \
  --decoder "python conformance/reference/decode.py"
```

## What each case contains

```
cases/<id>/
  case.json         title, the spec sections it exercises, and what to check
  workbook.json     writer input (writer cases)
  expected.sheet.md the exact bytes a writer must produce (writer cases)
  input.sheet.md    reader input (reader-only cases; writer cases read expected.sheet.md)
  decoded.json      the cells a reader must produce
```

`case.json` has a `write` entry (`input`, `expected`, optional `warns`) and/or a `read` entry (`input`, then `expected` or `rejects: true`, optional `warns`). `warns: true` means the implementation must write something to stderr; the kit does not prescribe the wording.

## Workbook JSON (writer input)

```json
{
  "options": {"max_rows": 6},
  "sheets": [
    {"name": "P&L", "state": "hidden", "freeze": "B2", "merges": ["A1:C1"], "names": {"Local": "'P&L'!$B$1"},
     "cells": {
      "A1": {"v": "Revenue"},
      "B1": {"v": 1200, "fmt": "#,##0"},
      "C1": {"f": "B1*2", "v": 2400},
      "D1": {"v": "2026-10-07", "t": "date", "fmt": "yyyy-mm-dd"}
     }}
  ],
  "names": {"Growth": "Assumptions!$B$2"}
}
```

- **Sheet:** `name`; optional `state` (`visible` default, `hidden`, `veryHidden`), `freeze` (top-left unfrozen cell), `merges`, `names` (sheet-scoped defined names), `comments` (`{"C3": "text"}`), `validations` (a list of `{"sqref", "type", "operator"?, "formula1", "formula2"?}`) and `dropped` (counts of features the format only counts, `{"charts": 2, "conditional formats": 1, "hyperlinks": 1}`; `images` and `pivot tables` are counted too but the Python reference cannot build them). Sheets are in workbook order. Cells not listed are empty.
- **Cell:**
  - `v` is the value. JSON strings are text, so `"00123"` and `"=x"` are text, never numbers or formulas. JSON numbers are numbers (`5` and `5.0` are the same cell). JSON `true`/`false` are booleans.
  - `t` marks a value JSON cannot carry: `"date"` (`2026-10-07`), `"datetime"` (`2026-10-07T14:30:05`), `"time"` (`09:05:00`), or `"error"` (`#DIV/0!`; `v` is the literal). A `datetime` at midnight is a date.
  - `f` is a formula, without the leading `=`. Then `v` is its **cached result** (the number the spreadsheet app last computed); the writer must round and format it as the spec says. A formula without `v` has no cached value and is written `?`. The kit's cached values are given, not computed, so some are not what the formula would really return.
  - `fmt` is the number format; absent means `General`.
  - `array` (e.g. `"B1:B2"`) with `f` marks the anchor of an array formula (§6.5). Other cells of the array's range are listed as ordinary cells with their cached results.
- **`options.max_rows`:** write the compact profile for regions longer than this many rows, keeping the last 3 (§9).
- **`names`** at the top level are workbook-level defined names.

## Decoded JSON (reader output)

Same shape as the workbook form, with these differences, so `decoded.json` is what a reader must print:

- A sheet with comments or validation rules has `comments` and `validations` in the same shape as the writer input, and an array's anchor has `array` besides `f`.
- Formula cells have `f` (with fill ranges already expanded, relative references shifted) and no `v`: a reader does not read cached results (§11).
- `state` and `freeze` are always present (`"visible"`, `null`), `merges` is a list, and `names` holds the sheet-scoped names.
- A date is `"t": "date"` and a date-time is `"t": "datetime"`; the midnight rule above applies. A loose date, date-time or time without a listed format gets `yyyy-mm-dd`, `yyyy-mm-dd hh:mm:ss` or `hh:mm:ss` (§8).
- Text read from the file has its escapes resolved, and line breaks are LF.

The checker normalizes before comparing: `fmt` of `General` is the same as no `fmt`, `merges` are compared as a sorted list, and object key order does not matter. Booleans, numbers and strings stay distinct (`true` is not `1`).

## Adding or changing a case

1. Write `workbook.json` (or `input.sheet.md`) and `case.json`.
2. Run `python conformance/reference/regenerate.py` to produce the expected files with the Python reference implementation.
3. **Read the expected files against `docs/SPEC.md`.** They are only as correct as that review; the reference implementation is not the authority, the spec is. Fix the spec or the implementation if they disagree.
4. Run `python conformance/check.py --validate` and `pytest tests/test_conformance.py`.

The expected files of cases 01–06 must stay identical to `tests/golden/spec/`; a test enforces it.

## Not covered (spec gaps)

- How a reader treats a bare `?` in the grid that has no `formulas` or `arrays` entry is not specified, so no reader case depends on it.
- The exponent spelling of formula results outside 1e-4…1e15 is not spelled out; the kit follows `%.6g` (`1.23457e-05`), as in `09_formula_results`.
- The compact profile's reading rules apart from rejection (§9), `source` front matter and `--recalc` behaviour are not part of the kit.
