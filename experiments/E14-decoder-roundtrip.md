# E14: Decoder and round trip on the corpus

**Date:** 2026-10-09 · **Type:** round-trip test (no model calls, no cost) · **Status:** passing; 7 writer and decoder gaps found and fixed

## Question

Does `encode → decode → recalculate → encode` give byte-identical text, and are values, formulas, formats, merges, names and sheet state intact in the decoded `.xlsx`? ([DESIGN](../docs/DESIGN.md) "Testing and conformance".)

## Setup

| Item | Value |
| --- | --- |
| Decoder | [`src/sheetmark/reader.py`](../src/sheetmark/reader.py): `sheetmark.load(text)` → `Workbook`, `Workbook.to_xlsx(path)`; CLI `sheetmark decode` and `sheetmark check` |
| Corpus | the 14 benchmark workbooks, plus one edge-case workbook built in [`tests/corpus.py`](../tests/corpus.py): three sheets named with a space, `&` and `#`, a hidden sheet, freeze panes, merged cells, dates and date-times, error constants, text look-alikes (`00123`, `TRUE`, `=not a formula`, `12:30:00`, pipes, backslashes, `<br>`, quotes), loose cells, typed-in override in a formula row, global and sheet-scoped names |
| Round trip | text₁ = `dumps(original)`; decode text₁ to .xlsx (no cached values); text₂ = `dumps(decoded)`, which recalculates with headless LibreOffice. Pass when text₂ == text₁ |
| Content check | formulas (as text), typed values and types, number formats of cells inside regions, merges, sheet state, freeze panes and names compared between the original and decoded .xlsx |
| Text fuzz | 58 hand-picked nasty strings and 3,000 random strings from a quote/pipe/backslash/`<br>`/time/date alphabet, each through `fmt_value` → split → decode; plus the same hand-picked set through a real .xlsx |

## Results

| Check | Result |
| --- | --- |
| 14 benchmark workbooks, text₂ == text₁ | 14 of 14 identical |
| 14 benchmark workbooks, content check | 14 of 14 equal |
| Edge-case workbook, text₂ == text₁ and content check | identical |
| Fuzz: 58 hand-picked + 3,000 random strings | 0 mismatches after the fixes below |
| Encoding of the 14 benchmark workbooks, before vs after the writer fixes | unchanged (0 of 14 differ) |

The writer fixes touch only text that contains backslashes, `<br>`, a leading `"`, `HH:MM:SS` text, or string cells starting with `=`, so the benchmarked encodings are unchanged. [`benchmarks/encoders.py`](../benchmarks/encoders.py), which produced the benchmarked text, is untouched.

## Problems found

Each was reproduced against the previous writer before being fixed. Reading the format back showed that the escaping was not invertible.

| Input text | What the old writer did | Fix |
| --- | --- | --- |
| `C:\dir\` | `\|` at the end of a cell was read as an escaped pipe, corrupting the row | `\` is written `\\` |
| `a\|b` | row split into two cells | same |
| `1 <br> 2` | read back with a newline | literal `<br>` is written `\<br>` |
| `"hello"` | quotes stripped on read | text starting with `"` is always quoted |
| `12:30:00` | read back as a time of day | `HH:MM:SS` text gets the `'` prefix |
| string cell `=not a formula` | written as a formula (the writer tested for a leading `=`, not the cell type) | formula means `data_type == "f"` |
| loose date cell | `cells` block has no number format, so the date came back as the serial `46381` | decoder gives loose dates a default date format; documented as a limit |

A lone CR was also written raw. It decodes fine, but Markdown renderers treat CR as a line break, so every line break (LF, CRLF, CR) is now written `<br>` and reads back as LF. That is by the CommonMark rules and was not tried on GitHub.

## Limits

- Files saved without cached values are read through LibreOffice by `dumps()`, which can rewrite number-format strings (`yyyy-mm-dd` became `yyyy\-mm\-dd`). The edge-case test therefore starts from a LibreOffice-saved copy, as a file saved by Excel would have.
- The corpus is synthetic. Real-world workbooks (workstream 1) will test region detection and formats harder.
- Not covered: array and dynamic formulas, loose-cell number formats, line-ending preservation, compact-profile files (refused by design).

## Conclusion

Decoding works on the whole corpus and the format is now invertible for every text and type tested. Formats are the next risk: they come back as LibreOffice or Excel wrote them.

## Reproduce

```bash
pip install -e ".[dev]"      # LibreOffice (soffice) must be on PATH
pytest tests/test_reader.py
```
