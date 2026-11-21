# E20: Does MarkItDown keep formula text? And the state of xlgit and xltrail

**Date:** 2026-10-11 · **Type:** baseline check and tool survey · **Status:** done. No model calls, no cost.

## Question

1. Does MarkItDown's xlsx-to-Markdown output include formulas, or only values?
2. What is the technical scope and maintenance status of two Excel-in-git tools, xlgit and xltrail?

## Setup

| Item | Value |
| --- | --- |
| MarkItDown | 0.1.7 installed via pip (0.1.8 is the latest on PyPI, released 2026-09-21) |
| Workbooks | Six real workbooks from the real-workbook set (`dam_wacccalc`, `dam_fcff3st`, `dam_capbudg`, `dam_fcffsimpleginzu`, `dam_lboval`, `dam_apv`) plus one synthetic file with two formulas and no cached values |
| Method | Count formula cells with openpyxl (`data_only=False`), then count how many formula strings appear in MarkItDown's output |
| Safety | Workbooks were treated as untrusted data and converted with `python -I` from an empty directory |

## Results: MarkItDown

| Workbook | Formula cells | Found in output | Output chars |
| --- | ---: | ---: | ---: |
| dam_wacccalc | 268 | 0 (see note) | 90,318 |
| dam_fcff3st | 240 | 0 | 9,279 |
| dam_capbudg | 214 | 0 | 7,054 |
| dam_fcffsimpleginzu | 1,231 | 0 | 173,635 |
| dam_lboval | 535 | 0 | 14,067 |
| dam_apv | 800 | 0 | 37,460 |
| synthetic (no cached values) | 2 | 0 | 32 |

Note: the raw check reported 3 hits for `dam_wacccalc`. All three are cells whose formula text is the bare string `=`, which matches any `=` in the output. They are not real matches.

Findings:

- **MarkItDown does not keep formula text.** It reads the cached values and drops the formulas. For example `=D4/D3` appears as its computed number.
- **A workbook saved without cached values loses the cells.** The synthetic file (`C1 = A1*B1`) came out as an empty table.
- **Header handling is lossy.** The first row becomes the table header, and empty cells show as `NaN` and empty header cells as `Unnamed: N`. Row numbers and column letters are absent, so a question like "what is in C7?" has no address to read.
- This is a version-specific result (0.1.7). A future MarkItDown release could change it; recheck before the publishable run.

Consequence for the benchmark: MarkItDown is a fair values-only baseline. Questions that need formula text (for example "what does B4 compute?") are unanswerable from its output, so report them as failures of the encoding, not of the model, and say so next to the number.

## Results: xlgit and xltrail

Facts below were read from each project's public package index entry, README and website on 2026-10-11.

| | xlgit | xltrail |
| --- | --- | --- |
| What it is | Git diff and merge driver for Excel, with a CLI, an HTML grid view and a GitHub PR comment bot | Web platform for Excel version control, with a Git integration and a self-hosted edition |
| Licence | Apache-2.0 (PyPI metadata) | Proprietary SaaS and self-hosted product |
| Release history | `0.1.0` and `0.1.1`, both on 2026-09-26. Marked Beta | Product site is live and copyrighted 2026. The blog's newest post is from August 2021 and no public changelog was found |
| Formulas | Compared as formulas (`=B2+C2`), not cached results | Tracks formulas, entered values, defined names, comments, Power Query and VBA. Calculated values are not tracked |

What this means for Sheetmark:

- Both tools keep `.xlsx` as the stored file and add a diff layer on top. Neither stores the workbook as text, which is the Sheetmark wedge (see `docs/DESIGN.md`).
- xlgit is brand new (about two weeks old at the time of the check) and is the closest match to a Sheetmark diff Action. Its activity should be rechecked before any positioning claim.
- xltrail is established but shows little public sign of new development. This is an inference from the blog and docs, not a statement from the vendor.

## Limitations

- Six real workbooks and one synthetic file. The finding is structural (the converter reads values only), so more files are unlikely to change it.
- xlgit's GitHub repository page could not be read from this environment. Its facts come from PyPI metadata and the README published there. Stars, open issues and commit history were not checked.
- "Still active" for xltrail is inferred from public pages only.

## Reproduce

```bash
pip install markitdown openpyxl
python -I benchmarks/markitdown_formula_check.py path/to/workbook.xlsx
```

Code: [`benchmarks/markitdown_formula_check.py`](../benchmarks/markitdown_formula_check.py). Backlog items B13 and E5.
