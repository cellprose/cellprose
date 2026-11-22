"""Recalculate workbooks with LibreOffice and compute ground truth for every question.

lookup  -> recalculated value of the target cell
address -> the target cell itself
trace   -> direct precedents parsed from the target's formula (ranges and names expanded)
impact  -> perturb the input cell, recalculate, and diff every cell's value
"""
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.formula import Tokenizer
from openpyxl.utils import range_boundaries, get_column_letter

ROOT = Path(__file__).parent
SRC, CALC, QDIR = ROOT / "workbooks_src", ROOT / "workbooks", ROOT / "questions"
CALC.mkdir(exist_ok=True)


def recalc(paths, outdir):
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(outdir)] +
                   [str(p) for p in paths], check=True, capture_output=True, timeout=600)


def split_ref(ref, default_sheet):
    ref = ref.replace("$", "")
    if "!" in ref:
        sh, rng = ref.rsplit("!", 1)
        sh = sh.strip("'")
    else:
        sh, rng = default_sheet, ref
    return sh, rng


def expand(sheet, rng):
    c1, r1, c2, r2 = range_boundaries(rng)
    return {f"{sheet}!{get_column_letter(c)}{r}" for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def precedents(wb, sheet, formula):
    names = {n: dn.attr_text for n, dn in wb.defined_names.items()}
    out = set()
    tok = Tokenizer(formula)
    for t in tok.items:
        if t.type == "OPERAND" and t.subtype == "RANGE":
            v = t.value
            if v in names:
                v = names[v]
            sh, rng = split_ref(v, sheet)
            out |= expand(sh, rng)
    return out


def all_values(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    return {f"{ws.title}!{c.coordinate}": c.value for ws in wb for row in ws.iter_rows() for c in row
            if c.value is not None}


def norm_val(v):
    if isinstance(v, float):
        return round(v, 9)
    return v


def main():
    srcs = sorted(SRC.glob("*.xlsx"))
    recalc(srcs, CALC)
    for src in srcs:
        key = src.stem
        qs = json.loads((QDIR / f"{key}.json").read_text())
        wbf = openpyxl.load_workbook(CALC / src.name)
        base = all_values(CALC / src.name)
        for q in qs:
            sh, cell = q["cell"].split("!")
            if q["type"] == "lookup":
                v = base.get(q["cell"])
                q["truth"] = v.isoformat()[:10] if hasattr(v, "isoformat") else v
            elif q["type"] == "address":
                q["truth"] = q["cell"]
            elif q["type"] == "trace":
                f = wbf[sh][cell].value
                assert isinstance(f, str) and f.startswith("="), (key, q)
                q["truth"] = sorted(precedents(wbf, sh, f))
            elif q["type"] == "hardcode":
                rsh, rng = q["range"].split("!")
                q["truth"] = sorted(c for c in expand(rsh, rng)
                                    if isinstance(wbf[rsh][c.split("!")[1]].value, (int, float)))
            elif q["type"] == "impact":
                with tempfile.TemporaryDirectory() as td:
                    td = Path(td)
                    w = openpyxl.load_workbook(src)
                    orig = w[sh][cell].value
                    assert isinstance(orig, (int, float)), (key, q)
                    w[sh][cell].value = orig * q["factor"]
                    w.save(td / src.name)
                    (td / "out").mkdir()
                    recalc([td / src.name], td / "out")
                    new = all_values(td / "out" / src.name)
                changed = sorted(k for k in set(base) | set(new)
                                 if k != q["cell"] and norm_val(base.get(k)) != norm_val(new.get(k)))
                q["truth"] = changed
        (QDIR / f"{key}.json").write_text(json.dumps(qs, indent=1, default=str))
        print(key, [(q["type"], q["truth"] if not isinstance(q["truth"], list) else len(q["truth"])) for q in qs])


if __name__ == "__main__":
    main()
