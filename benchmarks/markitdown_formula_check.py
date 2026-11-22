"""E20: does MarkItDown's xlsx output keep formula text?

Usage: python -I benchmarks/markitdown_formula_check.py WORKBOOK.xlsx [...]
For each workbook, counts formula cells (openpyxl, data_only=False) and counts
how many formula strings appear verbatim in MarkItDown's Markdown output.
"""
import sys

import openpyxl
from markitdown import MarkItDown


def check(path):
    wb = openpyxl.load_workbook(path)
    formulas = [c.value for ws in wb for row in ws.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("=")]
    text = MarkItDown().convert(path).text_content
    kept = sum(1 for f in formulas if f in text)
    return len(formulas), kept, len(text)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        n, kept, size = check(p)
        print(f"{p.rsplit('/', 1)[-1]}: formula cells={n} found in output={kept} output chars={size}")
