"""Build the real-world question corpus (backlog B9; docs/PROTOCOL.md section 3).

  python3 external/realworld.py build [--files DIR]   # workbooks + encodings + questions + review.md
  python3 external/realworld.py check [--files DIR]   # recompute ground truth and compare with the committed questions
  CELLPROSE_CORPUS=external/realworld python3 api_run.py --models haiku55 --encs csv,markitdown,cellprose_v03 ...

What is in git (external/realworld/):
  spec.json       the questions (hand-written) or the rule that picks them (`table`), with the checks that guard them
  manifest.json   workbook -> source file, licence, SHA-256, size in tokens
  questions/      rw_<name>.json, one per workbook, ground truth included
  review.md       what a reviewer read for every question: the question, the answer, and the cells around it
What is not (see .gitignore): workbooks/ and encoded/, rebuilt from the source files by `build`.

Source files. Twelve open-licence workbooks are committed in tests/real/. The four Damodaran models have no explicit
licence, so they are not committed: `build` reads them from --files (default: the first existing of
$CELLPROSE_REAL_FILES, /mnt/project-files/real-workbooks/files) or downloads them from the URL in tests/real/manifest.json
when CELLPROSE_FETCH_REAL=1, and checks every file against its SHA-256 first.

Ground truth (never typed by hand):
  lookup   the cached value of the cell (dates are not used: the scorer compares them as text)
  address  the cell itself
  trace    the direct precedents of the cell's formula, ranges and names expanded (ground_truth.precedents)
  impact   cells whose value differs between a LibreOffice recalculation of the workbook and of a copy in which the
           input cell is multiplied by `factor`. Both sides are LibreOffice, so Excel-versus-LibreOffice rounding
           does not show up as a change.
Hand check. Questions were written, and the review.md rows read, by one reviewer (Claude), in one pass. The builder adds
the machine checks it can: every `key` must match exactly one row and that row must be the answer's row; table rules
must find a unique key; lookups must not be dates, errors or empty. See review.md for the caveats.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.request
import warnings
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string as col_idx, get_column_letter as L

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))
import ground_truth as gt  # noqa: E402
from encoders import ENCODINGS, encode  # noqa: E402

warnings.filterwarnings("ignore", module="openpyxl")
OUT = HERE / "realworld"
REAL = BENCH.parent / "tests" / "real"
DEFAULT_FILES = [os.environ.get("CELLPROSE_REAL_FILES"), "/mnt/project-files/real-workbooks/files"]
ROWS_AT = (0.2, 0.5, 0.8)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_manifest() -> dict:
    m = json.loads((REAL / "manifest.json").read_text())
    return {e["file"]: e for e in m["committed"] + m["fetch"]}


def find_source(entry: dict, files_dir: str | None, fetch_dir: Path) -> Path:
    """The source .xlsx for a manifest entry, verified against its SHA-256."""
    name = entry["file"]
    candidates = [REAL / name] + [Path(d) / name for d in ([files_dir] if files_dir else DEFAULT_FILES) if d]
    for p in candidates:
        if p.exists() and sha256(p) == entry["sha256"]:
            return p
    if os.environ.get("CELLPROSE_FETCH_REAL") == "1" and entry.get("source_url"):
        fetch_dir.mkdir(parents=True, exist_ok=True)
        p = fetch_dir / name
        if not p.exists():
            urllib.request.urlretrieve(entry["source_url"], p)
        if sha256(p) == entry["sha256"]:
            return p
    raise SystemExit(f"{name}: no copy with SHA-256 {entry['sha256'][:12]}… found (looked in {[str(c) for c in candidates]}); "
                     "pass --files DIR, or set CELLPROSE_FETCH_REAL=1 to download it")


def cell_ref(sheet, coord):
    return f"{sheet}!{coord}"


def split_cell(ref):
    sheet, coord = ref.rsplit("!", 1)
    return sheet, coord


def norm(v):
    return v.strip().lower() if isinstance(v, str) else v


class Book:
    def __init__(self, path):
        self.path = path
        self.f = openpyxl.load_workbook(path)
        self.v = openpyxl.load_workbook(path, data_only=True)

    def val(self, ref):
        sheet, coord = split_cell(ref)
        return self.v[sheet][coord].value

    def formula(self, ref):
        sheet, coord = split_cell(ref)
        return self.f[sheet][coord].value

    def rows_matching(self, sheet, where: dict, first_row=1, last_row=None):
        ws = self.v[sheet]
        return [r for r in range(first_row, (last_row or ws.max_row) + 1)
                if all(norm(ws[f"{c}{r}"].value) == norm(x) for c, x in where.items())]


def resolve_at(book, at):
    """A cell from {"sheet", "row": {col: value}, "col": {rownumber: value}} (row found by labels, column by header)."""
    sheet = at["sheet"]
    rows = book.rows_matching(sheet, at["row"])
    assert len(rows) == 1, (at, rows)
    (hdr_row, hdr_val), = at["col"].items()
    ws = book.v[sheet]
    cols = [c for c in range(1, ws.max_column + 1) if str(ws.cell(int(hdr_row), c).value) == str(hdr_val)]
    assert len(cols) == 1, (at, cols)
    return f"{sheet}!{L(cols[0])}{rows[0]}"


def check_lookup_value(ref, v):
    assert v is not None and not (isinstance(v, str) and v.startswith("#")), (ref, v)
    assert not hasattr(v, "isoformat"), f"{ref}: dates are not used as lookup answers"
    assert isinstance(v, (int, float, str)) and not isinstance(v, bool), (ref, v)


def clean(v):
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return int(v)
    return v


def table_questions(book, cfg, name):
    """Three questions from a table by the fixed row rule (see spec.json selection_rule)."""
    sheet, hdr = cfg["sheet"], cfg["header_row"]
    keys = cfg["key"] if isinstance(cfg["key"], list) else [cfg["key"]]
    ws = book.v[sheet]
    first, last = hdr + 1, ws.max_row
    while last > first and all(ws.cell(last, c).value is None for c in range(1, ws.max_column + 1)):
        last -= 1
    n = last - first + 1
    heads = {c: " ".join(str(ws[f"{c}{hdr}"].value or "").split()) for c in set(keys + cfg["lookups"] + [cfg["address"]])}
    assert all(heads.values()), (name, "a column used in the rule has no header", heads)
    out = []
    plan = [("lookup", cfg["lookups"][0], ROWS_AT[0]), ("lookup", cfg["lookups"][1], ROWS_AT[1]),
            ("address", cfg["address"], ROWS_AT[2])]
    for kind, col, frac in plan:
        r = first + int(frac * n)
        # the first row at or after the rule's row whose key is non-empty, unique, and whose answer is usable
        while r <= last:
            kv = {k: ws[f"{k}{r}"].value for k in keys}
            ok = all(v is not None for v in kv.values()) and len(book.rows_matching(sheet, kv, first)) == 1
            ans = ws[f"{col}{r}"].value
            if ok and ans is not None and not hasattr(ans, "isoformat") and not (isinstance(ans, str) and ans.startswith("#")):
                break
            r += 1
        else:
            raise SystemExit(f"{name}: no usable row for {kind} {col} from {frac:.0%}")
        where = " and ".join(f"'{heads[k]}' is {clean(kv[k])!r}" if not isinstance(kv[k], str) else f"'{heads[k]}' is '{kv[k].strip()}'"
                             for k in keys)
        if kind == "lookup":
            q = f"In the sheet '{sheet}', for the row where {where}, what is the value of '{heads[col]}'?"
        else:
            q = (f"In the sheet '{sheet}', which cell holds '{heads[col]}' for the row where {where}? "
                 "Give its cell address.")
        out.append({"type": kind, "q": q, "cell": f"{sheet}!{col}{r}", "key": {k: kv[k] for k in keys},
                    "labels": [f"{k}{r}" for k in keys] + [f"{col}{r}", f"{col}{hdr}"]})
    return out


def impact_truth(src: Path, ref: str, factor: float, workdir: Path) -> list[str]:
    """Cells that change when `ref` is multiplied by `factor`. Both sides are a LibreOffice recalculation of a copy saved
    by openpyxl, differing only in that cell, so anything the round trip or LibreOffice does to every copy cancels out.
    A cell that also changes when nothing is changed (volatile or order-dependent iteration) is removed as noise."""
    sheet, coord = split_cell(ref)
    workdir.mkdir(parents=True, exist_ok=True)
    orig = openpyxl.load_workbook(src)[sheet][coord].value
    assert isinstance(orig, (int, float)) and not isinstance(orig, bool), (ref, orig)

    def recalc_copy(tag, value):
        w = openpyxl.load_workbook(src)     # a workbook with images can only be saved once
        w[sheet][coord].value = value
        (workdir / tag).mkdir(exist_ok=True)
        w.save(workdir / f"{tag}.xlsx")
        gt.recalc([workdir / f"{tag}.xlsx"], workdir / tag)
        return gt.all_values(workdir / tag / f"{tag}.xlsx")

    base, again, new = recalc_copy("base", orig), recalc_copy("again", orig), recalc_copy("pert", orig * factor)
    noise = {k for k in set(base) | set(again) if gt.norm_val(base.get(k)) != gt.norm_val(again.get(k))}
    if noise:
        print(f"  impact {ref}: {len(noise)} cells change between two recalculations of the same file and are ignored")
    return sorted(k for k in set(base) | set(new)
                  if k != ref and k not in noise and gt.norm_val(base.get(k)) != gt.norm_val(new.get(k)))


def make_questions(book, spec_wb, src, name, workdir, with_impact=True):
    raw = table_questions(book, spec_wb["table"], name) if "table" in spec_wb else spec_wb["questions"]
    out = []
    for i, q in enumerate(raw, 1):
        q = dict(q)
        q["id"] = f"q{i}"
        if "at" in q:
            q["cell"] = resolve_at(book, q.pop("at"))
        sheet, coord = split_cell(q["cell"])
        assert sheet in book.v.sheetnames, (name, q["cell"], book.v.sheetnames)
        key = q.get("key")
        if key and "table" not in spec_wb:
            lo, hi = q.get("rows", [1, None])
            rows = book.rows_matching(sheet, key, lo, hi)
            assert rows == [int("".join(ch for ch in coord if ch.isdigit()))], (name, q["id"], "key does not identify the row", rows)
        t = q["type"]
        if t == "lookup":
            v = book.val(q["cell"])
            check_lookup_value(q["cell"], v)
            q["truth"] = clean(v)
        elif t == "address":
            assert book.val(q["cell"]) is not None, (name, q["cell"], "empty answer cell")
            q["truth"] = q["cell"]
        elif t == "trace":
            f = book.formula(q["cell"])
            assert isinstance(f, str) and f.startswith("="), (name, q["cell"], f)
            q["truth"] = sorted(gt.precedents(book.f, sheet, f))
            assert q["truth"], (name, q["cell"], "no precedents")
        elif t == "impact":
            q["truth"] = impact_truth(src, q["cell"], q["factor"], workdir / f"{name}_{q['id']}") if with_impact else None
        else:
            raise SystemExit(f"{name}: unsupported type {t}")
        out.append(q)
    return out


def review_cell(book, ref):
    sheet, coord = split_cell(ref)
    v = book.v[sheet][coord].value
    return f"{ref} = {str(v)[:60]!r}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--files", help="directory holding the Damodaran source files")
    ap.add_argument("--no-impact", action="store_true", help="skip the LibreOffice recalculation (impact truth is left alone)")
    ap.add_argument("--only", help="comma list of workbook names")
    a = ap.parse_args(argv)
    spec = json.loads((OUT / "spec.json").read_text())
    sources = source_manifest()
    names = a.only.split(",") if a.only else list(spec["workbooks"])
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"workbooks": {}}
    (OUT / "questions").mkdir(exist_ok=True)
    review, bad = ["# Review record", "",
                   "Every question below was read against the cells around its answer by one reviewer (Claude) in one pass, "
                   "after the builder's own checks passed (unique key, usable answer, ground truth computed from the file). "
                   "`labels` are the cells that name the row and column. Limits: one reviewer, no second pass, no domain "
                   "expert for the Damodaran models.", ""], 0
    with tempfile.TemporaryDirectory() as td:
        for name in names:
            swb = spec["workbooks"][name]
            src = find_source(sources[swb["file"]], a.files, Path(td) / "fetch")
            book = Book(src)
            old_path = OUT / "questions" / f"{name}.json"
            qs = make_questions(book, swb, src, name, Path(td), with_impact=not a.no_impact)
            if a.mode == "check":
                old = json.loads(old_path.read_text())
                for q, o in zip(qs, old):
                    for k in ("type", "q", "cell", "truth"):
                        if q[k] is None:
                            continue
                        if q[k] != o[k]:
                            print(f"MISMATCH {name} {o['id']} {k}: committed {str(o[k])[:80]} recomputed {str(q[k])[:80]}")
                            bad += 1
                print(f"{name}: {len(qs)} questions checked")
                continue
            old = json.loads(old_path.read_text()) if old_path.exists() else []
            for q in qs:
                if q["truth"] is None:      # --no-impact: keep the committed answer
                    q["truth"] = next((o["truth"] for o in old if o["id"] == q["id"] and o["cell"] == q["cell"]), None)
            old_path.write_text(json.dumps(qs, indent=1, default=str) + "\n")
            wbdir = OUT / "workbooks"
            wbdir.mkdir(exist_ok=True)
            shutil.copy(src, wbdir / f"{name}.xlsx")
            encdir = OUT / "encoded"
            encdir.mkdir(exist_ok=True)
            toks = None
            for enc in ENCODINGS:
                try:
                    (encdir / f"{name}.{enc}.txt").write_text(encode(src, enc))
                except Exception as e:
                    print(f"  {name}: encoding {enc} failed: {type(e).__name__}: {str(e)[:100]}")
            try:
                import tiktoken
                e = tiktoken.get_encoding("o200k_base")
                toks = {enc: len(e.encode((encdir / f"{name}.{enc}.txt").read_text(), disallowed_special=()))
                        for enc in ("csv", "sheetmark_lean_gfm", "cellprose_v03") if (encdir / f"{name}.{enc}.txt").exists()}
            except Exception:
                pass
            entry = sources[swb["file"]]
            manifest["workbooks"][name] = {
                "source_file": swb["file"], "sha256": entry["sha256"], "licence": entry["licence"],
                "source_url": entry["source_url"], "committed_in_git": (REAL / swb["file"]).exists(),
                "questions": len(qs), "types": sorted({q["type"] for q in qs}),
                "formula_cells": sum(1 for ws in book.f for row in ws.iter_rows() for c in row
                                     if isinstance(c.value, str) and c.value.startswith("=")),
                "tokens_o200k": toks}
            review.append(f"## {name}\n")
            for q in qs:
                tr = q["truth"] if not isinstance(q["truth"], list) or len(q["truth"]) <= 8 else f"{len(q['truth'])} cells, e.g. {q['truth'][:3]}"
                review += [f"- **{q['id']}** ({q['type']}) {q['q']}", f"  - answer: `{tr}`; cell `{q['cell']}`",
                           "  - read: " + "; ".join(review_cell(book, f"{q['cell'].rsplit('!', 1)[0]}!{c}") if "!" not in c else review_cell(book, c)
                                                    for c in q.get("labels", [])), ""]
            print(f"{name}: {len(qs)} questions, tokens {toks}")
    if a.mode == "build":
        manifest["about"] = "Written by external/realworld.py build. tokens_o200k are OpenAI-tokenizer counts of the CSV, v0.2 and v0.3 encodings."
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
        if not a.only:
            (OUT / "review.md").write_text("\n".join(review) + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
