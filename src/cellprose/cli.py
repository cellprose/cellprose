"""Command line: `cellprose encode book.xlsx`, `cellprose decode book.sheet.md`, `cellprose check book.sheet.md`, `cellprose stats book.xlsx`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import ParseError, __version__, dumps, load_file


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cellprose", description="Convert spreadsheets to Cellprose (.sheet.md).")
    p.add_argument("--version", action="version", version=f"cellprose {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("encode", help="write .xlsx files as .sheet.md")
    e.add_argument("files", nargs="+", type=Path)
    e.add_argument("-o", "--output", type=Path, help="output file (one input) or '-' for stdout")
    e.add_argument("--sheet", action="append", help="only this sheet (repeatable)")
    e.add_argument("--range", dest="cell_range", help="only this A1 range, e.g. A1:F40")
    e.add_argument("--max-rows", type=int, help="elide regions longer than this (compact profile)")
    e.add_argument("--recalc", choices=["auto", "always", "never"], default="auto")
    d = sub.add_parser("decode", help="write .sheet.md files as .xlsx")
    d.add_argument("files", nargs="+", type=Path)
    d.add_argument("-o", "--output", type=Path, help="output file (one input only)")
    d.add_argument("--recalc", choices=["auto", "always", "never"], default="never",
                   help="pass the result through LibreOffice so formulas have cached values (it may rewrite formats)")
    c = sub.add_parser("check", help="validate .sheet.md files without writing anything")
    c.add_argument("files", nargs="+", type=Path)
    t = sub.add_parser("textconv", help="print a workbook as Cellprose text for `git diff` (used by the diff driver)")
    t.add_argument("file", type=Path)
    st = sub.add_parser("stats", help="compare a workbook's size as Cellprose vs CSV and Markdown (chars and tokens)")
    st.add_argument("files", nargs="+", type=Path)
    st.add_argument("--no-tokens", action="store_true", help="characters only (no tiktoken needed)")
    st.add_argument("--json", action="store_true", help="machine-readable output")
    sub.add_parser("pre-commit", help="write and stage a .sheet.md beside each staged .xlsx (used by the git hook)")
    g = sub.add_parser("git-setup", help="configure this repository: diff driver, .gitattributes and pre-commit hook")
    g.add_argument("--no-hook", action="store_true", help="only set up the diff driver")
    sub.add_parser("mcp", help="run the MCP server over stdio (same as `cellprose-mcp`; needs `pip install cellprose[mcp]`)")
    a = p.parse_args(argv)

    if a.cmd == "mcp":
        try:
            from .mcp_server import main as mcp_main
        except ImportError as e:
            print(f"error: the MCP server needs the MCP SDK: pip install 'cellprose[mcp]' ({e})", file=sys.stderr)
            return 1
        mcp_main()
        return 0

    if a.cmd in ("textconv", "pre-commit", "git-setup"):
        from . import gitflow
        if a.cmd == "textconv":
            sys.stdout.reconfigure(encoding="utf-8", newline="\n")
            sys.stdout.write(gitflow.textconv(a.file))
            return 0
        if a.cmd == "pre-commit":
            return gitflow.precommit()
        for line in gitflow.setup(hook=not a.no_hook):
            print(f"set up {line}", file=sys.stderr)
        return 0
    if a.cmd == "stats":
        import json
        from . import stats
        out, status = [], 0
        for f in a.files:
            try:
                out.append((f, stats.compute(f, tokens=not a.no_tokens)))
            except RuntimeError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
            except Exception as e:
                print(f"{f}: {e}", file=sys.stderr)
                status = 1
        if a.json:
            print(json.dumps({str(f): r for f, r in out}, indent=2))
        else:
            print("\n\n".join(stats.render(str(f), r) for f, r in out))
        return status
    if a.cmd == "check":
        bad = 0
        for f in a.files:
            try:
                wb = load_file(f)
            except ParseError as e:
                print(f"{f}: {e}", file=sys.stderr)
                bad += 1
                continue
            for w in wb.warnings:
                print(f"{f}: warning: {w}", file=sys.stderr)
            print(f"{f}: ok ({len(wb.sheets)} sheets)", file=sys.stderr)
        return 1 if bad else 0
    if a.cmd == "decode":
        if a.output and len(a.files) > 1:
            p.error("-o works with a single input file")
        status = 0
        for f in a.files:
            out = a.output or f.with_name(f.name.removesuffix(".sheet.md").removesuffix(".cellprose.md").removesuffix(".md") + ".xlsx")
            try:
                load_file(f).to_xlsx(out, recalc=a.recalc)
            except ParseError as e:
                print(f"{f}: {e}", file=sys.stderr)
                status = 1
                continue
            print(f"{f} -> {out}", file=sys.stderr)
        return status

    if a.output and len(a.files) > 1 and str(a.output) != "-":
        p.error("-o works with a single input file")
    for f in a.files:
        text = dumps(f, sheets=a.sheet, cell_range=a.cell_range, max_rows=a.max_rows, recalc=a.recalc)
        if a.output and str(a.output) == "-":
            sys.stdout.write(text)
            continue
        out = a.output or f.with_suffix(".sheet.md")
        out.write_text(text, encoding="utf-8", newline="\n")
        print(f"{f} -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
