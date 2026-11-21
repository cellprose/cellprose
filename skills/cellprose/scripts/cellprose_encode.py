#!/usr/bin/env python3
"""Convert .xlsx/.xlsm workbooks to Cellprose text. Needs openpyxl; LibreOffice is optional (computes missing
formula values). Uses the installed `cellprose` package when present, otherwise the vendored copy beside this file.

    python3 cellprose_encode.py book.xlsx [--sheet NAME] [--range A1:F40] [--max-rows N] [-o out.sheet.md]
"""
import sys
from pathlib import Path

try:
    from cellprose.cli import main
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent / "_vendor"))
    from cellprose.cli import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] != "encode":
        args = ["encode", *args]
    if "-o" not in args and "--output" not in args:
        args += ["-o", "-"]
    raise SystemExit(main(args))
