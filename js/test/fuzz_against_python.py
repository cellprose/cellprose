#!/usr/bin/env python3
"""Differential fuzzer: random workbooks through the JavaScript writer and the Python reference writer, comparing bytes.

    python js/test/fuzz_against_python.py [--seed 1] [--count 300] [--keep DIR]

Both writers read the conformance kit's workbook JSON. A mismatch is not necessarily a bug in the JavaScript writer: it
is a place where the spec, the Python writer and the JavaScript writer do not all say the same thing. Mismatching
workbooks are written to --keep (default: a temporary directory) for inspection.
"""
import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = [sys.executable, str(ROOT / "conformance" / "reference" / "encode.py")]
JS = ["node", str(ROOT / "js" / "bin" / "cellprose-encode.js")]

WORDS = ["Revenue", "North", "Q1", "Total", "x", "a b", "00123", "TRUE", "FALSE", "true", "?", "=SUM(A1)", "'q", "'", "''",
         "a|b", "a\\b", "<br>", "<BR>", "\\<br>", "a<br>b", "line1\nline2", "a\r\nb", " padded ", "\ttab", '"quoted"', '"',
         "2026-10-07 plan", "12:30:00", "1e5", "-5", ".5", "5.", "+5", "#N/A", "#REF! was here", "#", "café", "…", "日本", "😀",
         "", " ", "5\n", "x ", "　y", "A1", "1/0"]
FORMULAS = ["B{r}*2", "$A{r}*B$1", "SUM(B{r}:E{r})", "SUM(B$2:B{rm})", "'Other Sheet'!$A$1+F{r}", "Growth*B{r}", "IF(A{r}>0,\"x,y\",A{r})",
            "LOG10(B{r})", "A:A", "SUM($A:$A)", "1:1", "Sheet1!A{r}+1", "B{r}&\"a\"\"b\"", "1.5E3*B{r}", "TAX2026*2", "R{r}C1",
            "{r}:{r}", "SUM(B{r}:B{r2})", "B{r}", "-B{r}", "B{r}^2", "A1", "$A$1", "Q1+Q2", "LOG10(1)+B{r}", "x[1]+B{r}"]
FMTS = ["0%", "0.00", "#,##0", "$#,##0", "yyyy-mm-dd", "General", "@", "0.0%", '0.0"x"', "#,##0.00;[Red]-#,##0.00"]


def number(rng):
    return rng.choice([0, 1, -1, 5, 5.0, 100, 1200, 0.5, 0.125, -3.2e-07, 0.1 + 0.2, 1 / 3, 1234567.5, 1515987.648, 0.0001, 9.9999e-05,
                       123456789012, 1e15, 1e16, 1e22, 12345678.9, 0.000123456789, 1.5e-10, -2.5, 99999.95, 0.30000000000000004,
                       rng.random() * 10 ** rng.randint(-8, 8), rng.randint(-10**6, 10**6)])


def cached(rng):
    """A cached formula result. Known, reported divergences are avoided here so they do not drown out new ones:
    non-integers below 0.1 (the Python writer prints them with 6 decimals, not 6 significant figures), and text equal to
    an error literal (the reference adapter turns it into an error value)."""
    x = rng.choice([number(rng), number(rng), rng.choice(WORDS), True, 0])
    if isinstance(x, float) and 0 < abs(x) < 0.1:
        x = round(x, 3) or 0.5
    return "x" if x in ("#N/A", "#N/A ") else x


def addr(c, r):
    s = ""
    while c:
        c, m = divmod(c - 1, 26)
        s = chr(65 + m) + s
    return f"{s}{r}"


def split(a):
    letters = a.rstrip("0123456789")
    c = 0
    for ch in letters:
        c = c * 26 + ord(ch) - 64
    return c, int(a[len(letters):])


def cell(rng, r, c):
    k = rng.random()
    out = {}
    if k < 0.30:
        out["v"] = rng.choice(WORDS)
    elif k < 0.50:
        out["v"] = number(rng)
    elif k < 0.55:
        out["v"] = rng.choice([True, False])
    elif k < 0.60:
        out.update(rng.choice([{"t": "date", "v": "2026-10-07"}, {"t": "datetime", "v": "2026-10-07T14:30:05"},
                               {"t": "datetime", "v": "2026-10-07T00:00:00"}, {"t": "time", "v": "09:05:00"},
                               {"t": "error", "v": "#DIV/0!"}, {"t": "error", "v": "#N/A"}]))
    elif k < 0.95:
        out["f"] = rng.choice(FORMULAS).format(r=r, rm=max(r - 1, 1), r2=r + 2)
        if rng.random() < 0.85:
            out["v"] = cached(rng)
            if out["v"] == 0 and rng.random() < 0.5:
                out["t"], out["v"] = "error", "#DIV/0!"
    else:
        out["f"] = rng.choice(FORMULAS).format(r=r, rm=max(r - 1, 1), r2=r + 2)
        out["array"] = addr(c, r)
        out["v"] = number(rng)  # (an array cell without a cached value: Python writes "", the spec says "?")
    if rng.random() < 0.3 and ("v" in out or "f" in out):
        out["fmt"] = rng.choice(FMTS)
    return out


def workbook(rng):
    sheets = []
    for i in range(rng.randint(1, 3)):
        cells = {}
        for _ in range(rng.randint(0, 4)):  # a few clusters, some filled with a repeating formula pattern
            r0, c0 = rng.randint(1, 12), rng.randint(1, 8)
            h, w = rng.randint(1, 8), rng.randint(1, 6)
            pattern = rng.random() < 0.5
            f = rng.choice(FORMULAS) if pattern else None
            fmt = rng.choice(FMTS) if rng.random() < 0.4 else None
            for r in range(r0, r0 + h):
                for c in range(c0, c0 + w):
                    if rng.random() < 0.85:
                        if pattern and rng.random() < 0.9:
                            x = {"f": f.format(r=r, rm=max(r - 1, 1), r2=r + 2), "v": cached(rng)}
                        else:
                            x = cell(rng, r, c)
                        if fmt and ("v" in x or "f" in x) and rng.random() < 0.9:
                            x["fmt"] = fmt
                        cells[addr(c, r)] = x
        for _ in range(rng.randint(0, 3)):  # stray cells
            r, c = rng.randint(1, 30), rng.randint(1, 20)
            cells[addr(c, r)] = cell(rng, r, c)
        sh = {"name": rng.choice(["Sheet%d" % i, "P&L %d" % i, "Q1 #%d" % i, "Bob's %d" % i, "Ünï %d" % i]), "cells": cells}
        if rng.random() < 0.2:
            sh["state"] = rng.choice(["hidden", "veryHidden"])
        if rng.random() < 0.2:
            sh["freeze"] = rng.choice(["A2", "B2", "C3"])
        if rng.random() < 0.3:
            sh["merges"] = rng.sample(["A1:C1", "B5:C6", "A10:B10", "D4:E9"], rng.randint(1, 2))
        for m in sh.get("merges", []):  # only the top-left cell of a merged range may hold a value (spec §8)
            a, b = m.split(":")
            (c1, r1), (c2, r2) = split(a), split(b)
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    if (r, c) != (r1, c1):
                        cells.pop(addr(c, r), None)
        if rng.random() < 0.2:
            sh["names"] = {rng.choice(["Rate", "Cap", "Zeta", "alpha"]): "'%s'!$A$1" % sh["name"].replace("'", "''")}
        sheets.append(sh)
    # sheet names must be unique
    seen = set()
    for sh in sheets:
        while sh["name"] in seen:
            sh["name"] += "x"
        seen.add(sh["name"])
    doc = {"sheets": sheets}
    if rng.random() < 0.3:
        doc["names"] = {rng.choice(["Growth", "Tax", "zeta", "Ünï"]): rng.choice(["Sheet0!$A$1", "0.07", "A1*2"])}
    if rng.random() < 0.25:
        doc["options"] = {"max_rows": rng.choice([4, 6, 8])}
    return doc


def run(cmd, path):
    r = subprocess.run(cmd + [str(path)], capture_output=True)
    return r.returncode, r.stdout, bool(r.stderr.strip())


def xlsx_main(a, keep):
    """Same workbooks, but through real .xlsx files: built with openpyxl, recalculated and rewritten by LibreOffice (so
    cached results, shared strings and styles are as an application writes them), then read by both writers."""
    sys.path.insert(0, str(ROOT / "conformance" / "reference"))
    from _xlsx import build_pair
    from cellprose import dumps

    src, out = keep / "src", keep / "lo"
    src.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)
    docs = {}
    for i in range(a.count):
        doc = workbook(random.Random(a.seed * 100003 + i))
        for sh in doc["sheets"]:  # array formulas and the editor-specific cases are covered by the JSON mode
            for k, c in list(sh["cells"].items()):
                c.pop("array", None)
                if c.get("t") == "error" and "f" not in c:
                    sh["cells"][k] = {"v": "x"}
        fwb, _ = build_pair(doc)
        try:
            fwb.save(src / f"w{i:04d}.xlsx")
            docs[i] = doc
        except Exception as e:  # openpyxl refuses some random inputs (illegal characters)
            print(f"skip {i}: {e}", file=sys.stderr)
    files = sorted(str(p) for p in src.glob("*.xlsx"))
    subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", str(out), *files], capture_output=True, timeout=1500)
    bad = same = 0
    for p in sorted(out.glob("*.xlsx")):
        py = dumps(str(p), recalc="never").encode("utf-8")
        js = subprocess.run(JS + [str(p)], capture_output=True).stdout
        if py == js:
            same += 1
        else:
            bad += 1
            (keep / f"{p.stem}.py.md").write_bytes(py)
            (keep / f"{p.stem}.js.md").write_bytes(js)
    print(f"{same}/{same + bad} identical; {bad} differ (kept in {keep})")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", action="store_true", help="go through .xlsx files recalculated by LibreOffice")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--count", type=int, default=300)
    ap.add_argument("--keep")
    a = ap.parse_args()
    keep = Path(a.keep) if a.keep else Path(tempfile.mkdtemp(prefix="fuzz-"))
    keep.mkdir(parents=True, exist_ok=True)
    if a.xlsx:
        return xlsx_main(a, keep)
    bad = 0
    for i in range(a.count):
        doc = workbook(random.Random(a.seed * 100003 + i))
        p = keep / f"w{i:04d}.json"
        p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        py, js = run(PY, p), run(JS, p)
        if py != js:
            bad += 1
            (keep / f"w{i:04d}.py.md").write_bytes(py[1])
            (keep / f"w{i:04d}.js.md").write_bytes(js[1])
        else:
            p.unlink()
    print(f"{a.count - bad}/{a.count} identical; {bad} differ (kept in {keep})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
