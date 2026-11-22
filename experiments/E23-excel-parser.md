# E23: excel-parser (knowledgestack) against Sheetmark v0.2 on shared workbooks

**Date:** 2026-10-11 · **Type:** baseline comparison · **Status:** done. No model calls, no cost.

## Question

excel-parser (MIT, knowledgestack) chunks a workbook for retrieval. Does its output keep formulas, and how many tokens does it take compared with CSV, MarkItDown and Sheetmark v0.2 on the same files?

## Setup

- 14 synthetic benchmark workbooks and 42 real workbooks (`tests/real`, the project-files real set). Every tool ran on the same file in one session.
- excel-parser read two ways: `render_text` of each chunk (the text a retrieval system would embed), and the full chunk JSON (cells with `formula`, `value`, style).
- Tokens: tiktoken `o200k_base`. Formula recovery: the formula text of each formula cell (from openpyxl) must appear in the output, whitespace ignored.
- Code: `benchmarks/excel_parser_compare.py`. Raw numbers: `experiments/data/E23-excel-parser.json`. Run: `python -I benchmarks/excel_parser_compare.py OUT.json WORKBOOK.xlsx ...`.

## Results

Real workbooks where every encoder worked (35 of 42; the CSV baseline crashed on the other 7, which have empty or chart sheets):

| Encoding | Tokens | vs CSV | Formula cells recovered |
|---|---|---|---|
| CSV | 2.64M | 1.00 | 0 |
| MarkItDown | 3.13M | 1.19 | 15 of 26,318 (all 42 workbooks) |
| Sheetmark v0.2 | 3.00M | 1.14 | all but 25 (see below) |
| excel-parser, `render_text` | 7.93M | 3.0 | 33 of 26,318 |
| excel-parser, JSON | 54.8M | 20.8 | 26,284 of 26,318 |

Synthetic (14 workbooks, 1,037 formulas): CSV 13.8K, MarkItDown 19.7K, v0.2 18.5K, excel-parser text 27.1K, excel-parser JSON 412K tokens. v0.2 and the excel-parser JSON recover all 1,037 formulas; the others recover none.

- excel-parser's text keeps a `[=]` marker on formula cells but not the formula. Its marked-cell count is also below the true count on 8 Damodaran workbooks (for example 11,283 of 11,388 on `dam_ctryprem`).
- The formula text exists only in the JSON, which costs about 21 times CSV, so it is not a usable prompt format.
- The 25 formulas v0.2 "missed" are cells whose openpyxl formula is the empty string (a literal `=` text cell: 10 in `census_newresconst`, 12 in `dam_divginzu`, 3 in `dam_wacccalc`). No real formula was lost. `dam_divginzu` also has an array formula that v0.2 writes as typed values and warns about (SPEC §12).

## Limitations

One session, one pass, no repeats (the tools are deterministic, so tokens do not vary). Token counts are o200k, not each vendor's tokenizer. The real set is public Damodaran/government/open-data workbooks and is not a random sample. Retrieval chunking is excel-parser's purpose, so this compares prompt cost and formula visibility, not retrieval quality. No model was run, so nothing here says how accurately a model answers from either text.

## Conclusion

On formula visibility and size, excel-parser's text costs about 3 times CSV and drops formula text, and its JSON keeps formulas at about 21 times CSV; v0.2 keeps every formula at 1.14 times CSV.
