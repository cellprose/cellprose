# cellprose (JavaScript)

A second, independent Cellprose v0.3 **writer**, in JavaScript with no dependencies (Node 18+). It turns an `.xlsx` workbook, or a conformance-kit workbook JSON, into byte-exact `.sheet.md`.

It was written from [`docs/SPEC.md`](https://github.com/cellprose/cellprose/blob/main/docs/SPEC.md), not ported from `src/cellprose/writer.py`; the two share no code. Where the spec leaves a detail open, `src/writer.js` says which choice it made. The Python writer was read afterwards, only to settle those open details (listed below), so on those points the two writers agree because the kit and the Python writer fixed the answer, not because the spec did.

```bash
npm install cellprose
npx cellprose-encode book.xlsx > book.sheet.md
node js/bin/cellprose-encode.js book.xlsx > book.sheet.md          # source: line is the file name, as in the Python CLI
node js/bin/cellprose-encode.js book.xlsx --max-rows 40            # compact profile
node js/bin/cellprose-encode.js conformance/cases/02_model/workbook.json
```

```js
const { loadXlsx, fromJson, dumpsWorkbook } = require('cellprose');
const { text, warnings } = dumpsWorkbook(loadXlsx('book.xlsx'), { maxRows: 40 });
```

`loadXlsx` also takes an archive that is already unzipped: any object with `read(name)` returning a part's text or `null`. That is how a browser uses it, since `fs` and `zlib` exist only in Node; the website's playground (`site/`) unzips with `DecompressionStream` and passes such an object.

## Tests

```bash
cd js && npm test                                                        # unit tests + all kit writer cases, in-process
python conformance/check.py --encoder "node js/bin/cellprose-encode.js"  # the kit's own checker, as CI runs it
python js/test/fuzz_against_python.py --count 300                        # random workbooks, JS against Python, byte for byte
python js/test/fuzz_against_python.py --xlsx --count 25                  # same, through .xlsx files rewritten by LibreOffice
```

The fuzzer is a development tool, not part of CI: it compares two writers, and any mismatch is a place where the spec, the Python writer and this writer do not all say the same thing.

## Layout

| File | Job |
|---|---|
| `src/writer.js` | The format: values, escaping, regions, fill ranges, formats, names, compact profile (§5–§9) |
| `src/formula.js` | Splits a formula into text and references, to compare "same formula, shifted" and to expand shared formulas |
| `src/xlsx.js`, `zip.js`, `xml.js` | `.xlsx` reader: workbook, sheets, shared strings, styles. About 300 lines, because the format needs names, shared formulas, array formulas and cached results exactly as the file stores them, plus comments, data validation and the counts for the "not carried" note |
| `src/model.js` | The in-memory workbook, and the loader for the kit's JSON |

The viewer in `viewer/` reads the format; this package writes it. They are kept apart because the viewer ships to a browser extension, which has no use for an `.xlsx` reader.

## What the spec leaves open

These are the points where this writer's output was fixed by the kit or the Python writer, not by the spec. The kit covers some of them (marked); the rest are not covered by any case, so a third writer could differ.

1. **Which text gets the `'` prefix (§5.3).** The spec lists types ("a number, a date, …"). The kit (case 07) shows a prefix test on the *start* of the text: `2026-10-07 plan` and `#REF! was here` are prefixed. The exact patterns used here: a number (`[-+]?` digits with optional `.` and exponent, so `+5`, `5.`, `.5` and `1e5`), text starting with four digits, `-`, two digits, `-`, two digits (or two digits, `:`, two, `:`, two), exactly `TRUE`, `FALSE` or `?` (upper case only), or starting with `#` and then `A–Z / 0 ! ?`. Not covered by the kit: `+5`, `5.`, `#NAME?`.
2. **"Leading or trailing whitespace" (§5.3)** is Python's `str.isspace()` set (adds no-break space, U+3000, U+0085, U+001C–U+001F, …). The kit covers space and tab only.
3. **Integer-valued formula results are not rounded (§5.3).** `1234567` stays `1234567`; only non-integers get 6 significant figures. The spec's example (`1515987.648` → `1515990`) is a non-integer, and its "from `1e15`" exponent rule is not applied to integer-valued results (they are written in full). Not covered by the kit.
4. **The `note:` for `?` (§3)** is added only when a `?` is written in a region grid. A `?` in a loose-cell formula (`M3 = C1+1  # ?`) does not add it; kit case 12 requires that.
5. **Array formula without a cached value, as a loose cell (§12).** The spec says `?`; this writer writes `H10: ?`. The Python writer writes `H10: ` (nothing after the colon). Not covered by the kit.
6. **Sheet names (§4).** Quoted when they contain `#`, LF or CR. The spec does not say how a `"` or a line break inside the quotes is written, and a raw line break in a heading breaks the Markdown anyway.
7. **Ordering (§8).** "Sorted by name" is code point order, so `Zeta` sorts before `alpha`. The kit's names are all capitalized.
8. **Compact profile (§9).** Keeps `max_rows - 3` leading rows (at least 1) and 3 trailing rows, and the marker row sits between them.
9. **Reading `.xlsx`.** `_xlnm.*` built-in names are not user names and are left out. Only *frozen* panes count as `freeze`. A number with a date format is a time of day when it is in [0, 1), a date-time otherwise, rounded to the second; a serial outside the date range stays a number.

## Where the Python writer disagreed with the spec

Formula results below 0.1 used to lose digits in `writer.py` (6 decimals, not 6 significant figures: `0.0296862` was written `0.029686`). Fixed, and kit case `19_small_results` covers it. The fuzzer found it.
