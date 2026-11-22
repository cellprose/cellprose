"""Build the benchmark real-world set, `rw2_` (docs/PROTOCOL.md section 3).

  python3 external/realworld2.py fetch  [--files DIR]                  # download and convert the 15 Damodaran files
  python3 external/realworld2.py build  [--files DIR]                  # questions, ground truth, questions.md, encodings
  python3 external/realworld2.py check  [--files DIR]                  # recompute and compare with the committed questions
  python3 external/realworld2.py freeze                                # write benchmarks/freeze/benchmark.json
  python3 external/realworld2.py select --damodaran DIR --enron DIR   # how the workbooks were picked (done once)
  CELLPROSE_CORPUS=external/realworld2 python3 api_run.py --final ...

Unlike the first real-world set (`realworld.py`, `rw_`), no question here is written by hand. Workbooks and questions
are both picked by rules fixed in this file before any model has seen them, from a seeded random draw (SEED), so the
set cannot be shaped by what the formats are good at.

Workbooks (`select`):
  - Damodaran: the 49 NYU Stern spreadsheets not used before (real-workbooks/FRESH_CHECK.md), .xls converted to .xlsx by
    LibreOffice. Eligible: ELIGIBLE (below). A seeded draw of N_DAMODARAN.
  - Enron (Hermans and Murphy-Hill 2015, figshare 1221767, CC BY 4.0): files in a seeded order, at most one per author
    (the name before `__`), and no two with the same base name. Each candidate is converted by LibreOffice and kept if
    ELIGIBLE, until N_ENRON are kept.
  ELIGIBLE: at least MIN_FORMULAS formula cells; the v0.3 text is at most MAX_TOKENS o200k tokens; the encodings the tiers run
  (v0.3, MarkItDown, CSV) succeed; no formula reads another workbook or
  is volatile (RAND, RANDBETWEEN, NOW, TODAY: values change on every recalculation, so impact has no stable answer); and the question rules below can make every question type.

Questions (`build`), per workbook, from sheets whose names have no outer spaces, each drawn from its candidates in a seeded order:
  lookup x1, address x1  a non-zero number (not a date) named by its row label (the nearest text to its left) and column
                         header (the nearest text above, within 25 rows). The pair must name no other number in the sheet.
  trace x2               a formula cell with 2 to 12 direct precedents (no INDIRECT or OFFSET), named by its address and
                         row label. Truth: its direct precedents, ranges and names expanded.
  impact x1              a typed number that some formula reads, raised by 10%. Truth: cells whose value differs between
                         two LibreOffice recalculations (realworld.impact_truth); kept if 2 to 400 cells change
                         (at most 12 candidates are tried).
  hardcode x1            a run of 4 to 24 numeric cells in a row or column holding at least one formula. A run that also
                         holds typed numbers is taken first when the sheet has one. Truth: the typed numbers in the run.
The address is given in trace, impact and hardcode questions, so those test reading formulas, not finding the cell.
"""
import argparse
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter as L

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(HERE))
import ground_truth as gt  # noqa: E402
from encoders import ENCODINGS, encode  # noqa: E402
from realworld import Book, clean, impact_truth, sha256  # noqa: E402

warnings.filterwarnings("ignore")
OUT = HERE / "realworld2"
SEED = 20261106
N_DAMODARAN, N_ENRON = 15, 15
MIN_FORMULAS, MAX_TOKENS = 50, 100_000
PLAN = [("lookup", 1), ("address", 1), ("trace", 2), ("impact", 1), ("hardcode", 1)]
DYNAMIC = re.compile(r"\b(INDIRECT|OFFSET)\s*\(", re.I)
VOLATILE = re.compile(r"\b(RAND|RANDBETWEEN|NOW|TODAY)\s*\(", re.I)
REQUIRED_ENCS = ("cellprose_v03", "markitdown", "csv")   # the encodings the tiers run
EXCLUDE = {   # generated questions that are not part of the set, with the reason; by their id as generated
    'rw2_dam_ddm2st': {'q1': "column header 'Weight' heads a different table 15 rows above"},
    'rw2_dam_fcfe2st': {'q2': "column header is a note ('Do not enter') that appears four times in the sheet"},
    'rw2_dam_fcff2st': {'q2': "column header is '(in percent)', a note not a header"},
    'rw2_dam_fcffgen': {'q2': "column header is 'No', not a real header"},
    'rw2_dam_fcffvsfcfe': {'q2': 'column header is a note, not a header'},
    'rw2_dam_higrowth': {'q1': "column header is 'NA', not a real header"},
    'rw2_enron_andy_zipper': {'q5': "answer misses Enron Activity-ICE!E7: LibreOffice renames the pivot row 'Grand Total' on recalculation, so the change is lost"},
    'rw2_enron_james_steffes': {'q1': "column header is 'to', which also matches other cells"},
    'rw2_enron_jonathan_mckay': {'q2': 'stated answer N8; the natural reading of the label gives B8'},
    'rw2_enron_kevin_presto': {'q1': "column header is '#N/A', not a real header", 'q2': "column header is '#N/A', not a real header"},
    'rw2_enron_lisa_gang': {'q1': "row label is the sheet's title line; the value is a drop-down index 34 columns away"},
    'rw2_enron_phillip_platter': {'q1': 'column header is not a real header', 'q2': 'row label is free text in a Notes column; the heading spans four columns'},
    'rw2_enron_thomas_martin': {'q1': "floor plan: the 'header' is another person's desk, not a header", 'q2': "floor plan: the 'header' is another person's desk; 'Row 4' also labels another table"},
    'rw2_enron_vkaminski': {'q2': "two columns are headed 'Risk Metrics' in the 4M row (H4 and J4); the answer takes only J4"},
}
DEFAULT_FILES = ["/mnt/project-files/real-workbooks/files2"]


def text(v):
    if not isinstance(v, str):
        return None
    s = " ".join(v.split())
    return s[:80] if re.search(r"[A-Za-z]", s) else None


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_formula(v):
    return isinstance(v, str) and v.startswith("=")


class Labels:
    """Row label and column header of each cell of a sheet, from cached values."""

    def __init__(self, ws):
        self.ws = ws
        self.grid = {(c.row, c.column): c.value for row in ws.iter_rows() for c in row if c.value is not None}

    def row_label(self, r, c):
        for cc in range(c - 1, 0, -1):
            t = text(self.grid.get((r, cc)))
            if t:
                return t
        return None

    def col_header(self, r, c):
        for rr in range(r - 1, max(0, r - 26), -1):
            t = text(self.grid.get((rr, c)))
            if t:
                return t
        return None

    def name(self, r, c):
        return self.row_label(r, c), self.col_header(r, c)


def describe(sheet, lab, hdr):
    s = f"the row labelled '{lab}'"
    return s + (f", column headed '{hdr}'" if hdr else "") + f", in the sheet '{sheet}'"


def formula_cells(book):
    for ws in book.f.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if is_formula(c.value):
                    yield ws.title, c


def external_refs(book):
    return any("[" in c.value for _, c in formula_cells(book))


def precedent_index(book):
    """cell -> its direct precedents, and the set of every cell some formula reads."""
    prec, read = {}, set()
    for sheet, c in formula_cells(book):
        try:
            p = gt.precedents(book.f, sheet, c.value)
        except Exception:
            continue
        prec[f"{sheet}!{c.coordinate}"] = p
        read |= p
    return prec, read


def candidates(book):
    """Every candidate for every question type, in sheet order."""
    prec, read = precedent_index(book)
    out = {t: [] for t, _ in PLAN}
    for ws in book.f.worksheets:
        if ws.title != ws.title.strip():
            continue    # a sheet name with outer spaces cannot be written unambiguously as Sheet!A1
        vs = book.v[ws.title]
        lab = Labels(vs)
        names = {}
        for row in vs.iter_rows():
            for c in row:
                if is_num(c.value):
                    names.setdefault(lab.name(c.row, c.column), []).append(c.coordinate)
        for (rl, hd), cells in names.items():
            if rl and len(cells) == 1 and vs[cells[0]].value != 0 and not hasattr(vs[cells[0]].value, "isoformat"):
                out["lookup"].append({"cell": f"{ws.title}!{cells[0]}", "labels": (rl, hd)})
        for row in ws.iter_rows():
            for c in row:
                ref = f"{ws.title}!{c.coordinate}"
                if is_formula(c.value) and ref in prec and 2 <= len(prec[ref]) <= 12 and not DYNAMIC.search(c.value) \
                        and is_num(vs[c.coordinate].value):
                    out["trace"].append({"cell": ref, "labels": lab.name(c.row, c.column)})
                if is_num(c.value) and c.value != 0 and ref in read:
                    out["impact"].append({"cell": ref, "labels": lab.name(c.row, c.column)})
        out["hardcode"] += runs(ws, lab)
    out["address"] = out["lookup"]   # the same pool; a cell is used once
    return out


def runs(ws, lab):
    """Runs of 4 to 24 numeric cells (typed or formula) along a row or a column that hold at least one formula."""
    grid = {(c.row, c.column): c.value for row in ws.iter_rows() for c in row
            if is_num(c.value) or is_formula(c.value)}
    found = []
    for horizontal in (True, False):
        seen = set()
        for (r, c) in sorted(grid):
            if (r, c) in seen:
                continue
            cells = []
            rr, cc = r, c
            while (rr, cc) in grid:
                cells.append((rr, cc))
                seen.add((rr, cc))
                rr, cc = (rr, cc + 1) if horizontal else (rr + 1, cc)
            if not 4 <= len(cells) <= 24 or not any(is_formula(grid[x]) for x in cells):
                continue
            typed = [x for x in cells if is_num(grid[x])]
            a, b = cells[0], cells[-1]
            rng = f"{L(a[1])}{a[0]}:{L(b[1])}{b[0]}"
            found.append({"range": f"{ws.title}!{rng}", "cell": f"{ws.title}!{L(a[1])}{a[0]}", "mixed": bool(typed),
                          "labels": (lab.row_label(a[0], a[1]) if horizontal else lab.col_header(a[0], a[1]),
                                     "row" if horizontal else "column")})
    return found


def question(kind, cand, book, src, workdir, name, i):
    sheet, coord = cand["cell"].rsplit("!", 1)
    rl, hd = cand["labels"]
    tag = f" (in the row labelled '{rl}')" if kind in ("trace", "impact") and rl else ""
    q = {"type": kind, "cell": cand["cell"]}
    if kind == "lookup":
        q["q"] = f"What is the value in {describe(sheet, rl, hd)}?"
        q["truth"] = clean(book.val(cand["cell"]))
    elif kind == "address":
        q["q"] = f"Which cell holds the value in {describe(sheet, rl, hd)}? Give its cell address."
        q["truth"] = cand["cell"]
    elif kind == "trace":
        q["q"] = f"Consider the cell {cand['cell']}{tag}. List the cells its formula reads directly (not indirectly)."
        q["truth"] = sorted(gt.precedents(book.f, sheet, book.formula(cand["cell"])))
    elif kind == "impact":
        q["factor"] = 1.1
        q["q"] = (f"Suppose the number in {cand['cell']}{tag} were 10% higher. "
                  "List every other cell whose value would change.")
        truth = impact_truth(src, cand["cell"], 1.1, workdir / f"{name}_{i}")
        if not 2 <= len(truth) <= 400:
            return None
        q["truth"] = truth
    elif kind == "hardcode":
        q["range"] = cand["range"]
        what = f" (the {hd} of '{rl}')" if rl else ""
        q["q"] = (f"Consider the range {cand['range']}{what}. "
                  "List the cells that hold typed-in numbers rather than formulas.")
        rsh, rng = cand["range"].rsplit("!", 1)
        q["truth"] = sorted(c for c in gt.expand(rsh, rng) if is_num(book.f[rsh][c.rsplit("!", 1)[1]].value))
    if kind in ("lookup", "address"):
        r, c = openpyxl.utils.cell.coordinate_to_tuple(coord)
        lab = Labels(book.v[sheet])
        q["labels"] = [x for x in (find_text(lab, r, c, "row"), find_text(lab, r, c, "col")) if x]
    return q


def find_text(lab, r, c, which):
    rng = range(c - 1, 0, -1) if which == "row" else range(r - 1, max(0, r - 26), -1)
    for k in rng:
        pos = (r, k) if which == "row" else (k, c)
        if text(lab.grid.get(pos)):
            return f"{L(pos[1])}{pos[0]}"
    return None


def make_questions(book, src, name, workdir, impact=True):
    """The questions for one workbook by the rules above, or None when a type has no usable candidate."""
    rng = random.Random(f"{SEED}:{name}")
    cands = candidates(book)
    used, out = set(), []
    for kind, n in PLAN:
        pool = cands[kind]
        if kind == "hardcode":
            mixed = [c for c in pool if c["mixed"]]
            pool = mixed or pool
        pool = pool[:]
        rng.shuffle(pool)
        got, tries = 0, 0
        for cand in pool:
            if got == n or tries >= 12:
                break
            if cand["cell"] in used:
                continue
            if kind == "impact" and not impact:
                q = {"type": "impact", "cell": cand["cell"], "factor": 1.1, "truth": None}
            else:
                tries += kind == "impact"
                q = question(kind, cand, book, src, workdir, name, len(out) + 1)
            if q is None:
                continue
            used.add(cand["cell"])
            out.append(q)
            got += 1
        if got < n:
            return None
    for i, q in enumerate(out, 1):
        q["id"] = f"q{i}"
    out = [q for q in out if q["id"] not in EXCLUDE.get(name, ())]      # the exclusion list above
    for i, q in enumerate(out, 1):
        q["id"] = f"q{i}"
    return out


def v03_tokens(path):
    import tiktoken
    return len(tiktoken.get_encoding("o200k_base").encode(encode(path, "cellprose_v03"), disallowed_special=()))


def eligible(path, name, workdir):
    """(ok, reason, info) under ELIGIBLE. Every question is made, impact truth included, so `build` cannot fail."""
    try:
        book = Book(path)
    except Exception as e:
        return False, f"unreadable: {type(e).__name__}", {}
    nf = sum(1 for _ in formula_cells(book))
    if nf < MIN_FORMULAS:
        return False, f"{nf} formulas", {}
    if external_refs(book):
        return False, "reads another workbook", {}
    if any(VOLATILE.search(c.value) for _, c in formula_cells(book)):
        return False, "volatile formulas (RAND, NOW, ...)", {}
    for enc in REQUIRED_ENCS:
        try:
            encode(path, enc)
        except Exception as e:
            return False, f"encoding {enc} failed: {type(e).__name__}", {}
    toks = v03_tokens(path)
    if toks > MAX_TOKENS:
        return False, f"{toks} tokens", {}
    if make_questions(book, path, name, workdir) is None:
        return False, "a question type has no candidate", {}
    return True, "ok", {"formula_cells": nf, "tokens_o200k_v03": toks}


def convert(src, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", str(outdir), str(src)],
                   check=True, capture_output=True, timeout=180)
    return outdir / (src.stem + ".xlsx")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def select(a):
    files = Path(a.out_files)
    files.mkdir(parents=True, exist_ok=True)
    chosen, log = {}, []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # Damodaran: every eligible file, then a seeded draw
        ok = []
        for p in sorted(Path(a.damodaran).glob("*.xlsx")):
            name = "rw2_dam_" + slug(p.stem)
            good, why, info = eligible(p, name, td)
            log.append({"file": p.name, "source": "damodaran", "eligible": good, "reason": why})
            if good:
                ok.append((name, p, info))
        random.Random(SEED).shuffle(ok)
        for name, p, info in sorted(ok[:N_DAMODARAN]):
            shutil.copy(p, files / p.name)
            chosen[name] = {"source": "damodaran", "file": p.name, "sha256": sha256(p),
                            "source_url": f"https://pages.stern.nyu.edu/~adamodar/pc/{p.stem}.xls",
                            "licence": "none stated (A. Damodaran, NYU Stern); not committed", **info}
        # Enron: seeded order, one per author, convert and test until N_ENRON
        allx = sorted(p for p in Path(a.enron).rglob("*") if p.suffix.lower() in (".xls", ".xlsx"))
        random.Random(SEED).shuffle(allx)
        authors, bases, n = set(), set(), 0
        for p in allx:
            if n >= N_ENRON:
                break
            author, _, rest = p.name.partition("__")
            base = rest.split("__", 1)[-1].lower()
            if author in authors or base in bases:
                continue
            try:
                x = convert(p, td / "conv") if p.suffix.lower() == ".xls" else p
            except Exception:
                log.append({"file": p.name, "source": "enron", "eligible": False, "reason": "conversion failed"})
                continue
            name = "rw2_enron_" + slug(author)
            good, why, info = eligible(x, name, td)
            log.append({"file": p.name, "source": "enron", "eligible": good, "reason": why})
            if not good:
                continue
            authors.add(author)
            bases.add(base)
            out = files / f"enron__{p.stem}.xlsx"
            shutil.copy(x, out)
            chosen[name] = {"source": "enron", "file": out.name, "sha256": sha256(out), "original": p.name,
                            "original_sha256": sha256(p), "source_url": "https://doi.org/10.6084/m9.figshare.1221767",
                            "licence": "CC BY 4.0 (Hermans and Murphy-Hill, 2015)", **info}
            n += 1
    OUT.mkdir(exist_ok=True)
    (OUT / "selection.json").write_text(json.dumps(
        {"about": "Written by external/realworld2.py select; the rule is in that file's docstring.", "seed": SEED,
         "workbooks": dict(sorted(chosen.items())), "screened": log}, indent=1) + "\n")
    print(f"{sum(1 for v in chosen.values() if v['source'] == 'damodaran')} Damodaran, "
          f"{sum(1 for v in chosen.values() if v['source'] == 'enron')} Enron; {len(log)} files screened")


def find_source(entry, files_dir):
    """The chosen source file: the same bytes, or for a Damodaran file (re-converted by `fetch`) the same content."""
    from freeze import cell_sha256
    for d in ([files_dir] if files_dir else []) + DEFAULT_FILES + [str(OUT / "sources")]:
        p = Path(d) / entry["file"]
        if p.exists() and (sha256(p) == entry["sha256"] or
                           (entry.get("cell_sha256") and cell_sha256(p) == entry["cell_sha256"])):
            return p
    raise SystemExit(f"{entry['file']}: no copy with SHA-256 {entry['sha256'][:12]} found; run fetch or pass --files DIR")


def fetch(a):
    """Download each Damodaran .xls from its source_url, check it is the file the set was built from (source_sha256),
    convert it with LibreOffice and check the result says what the frozen workbook says (cell_sha256). Damodaran's
    files carry no licence, so they are fetched, never redistributed (docs/PROTOCOL.md section 3)."""
    import urllib.request
    from freeze import cell_sha256
    dest = Path(a.files or DEFAULT_FILES[0])
    dest.mkdir(parents=True, exist_ok=True)
    entries = json.loads((OUT / "selection.json").read_text())["workbooks"]
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for name, e in sorted(entries.items()):
            if e["source"] != "damodaran":
                continue
            xls = Path(td) / Path(e["source_url"]).name
            with urllib.request.urlopen(e["source_url"], timeout=120) as r:
                xls.write_bytes(r.read())
            if sha256(xls) != e["source_sha256"]:
                print(f"{name}: the .xls on the site changed since the freeze (SHA-256 {sha256(xls)[:12]}); "
                      "checking its content anyway")
            x = convert(xls, Path(td) / "conv")
            if cell_sha256(x) != e["cell_sha256"]:
                print(f"{name}: converted content differs from the frozen workbook; not used")
                bad += 1
                continue
            shutil.copy(x, dest / e["file"])
            print(f"{name}: ok")
    return 1 if bad else 0


def source_line(book, ref):
    sheet, coord = ref.rsplit("!", 1)
    return f"{ref} = {str(book.v[sheet][coord].value)[:60]!r}"


def build(a, check=False):
    sel = json.loads((OUT / "selection.json").read_text())["workbooks"]
    names = a.only.split(",") if a.only else list(sel)
    (OUT / "questions").mkdir(exist_ok=True)
    listing = ["# Questions (benchmark real-world set)", "",
              "Every question was made by the rules in `external/realworld2.py` and its answer computed from the file. "
              "Under each question is what it was built from: the labels it read, or the formula it traces.", ""]
    mpath = OUT / "manifest.json"
    manifest = json.loads(mpath.read_text())["workbooks"] if a.only and mpath.exists() else {}
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for name in names:
            e = sel[name]
            src = find_source(e, a.files)
            book = Book(src)
            qs = make_questions(book, src, name, Path(td))
            assert qs is not None, name
            qpath = OUT / "questions" / f"{name}.json"
            if check:
                old = json.loads(qpath.read_text())
                if len(qs) != len(old):
                    print(f"MISMATCH {name}: {len(qs)} questions rebuilt, {len(old)} committed")
                    bad += 1
                for q, o in zip(qs, old):
                    for k in ("type", "q", "cell", "truth"):
                        if q[k] != o[k]:
                            print(f"MISMATCH {name} {o['id']} {k}")
                            bad += 1
                print(f"{name}: {len(qs)} checked")
                continue
            qpath.write_text(json.dumps(qs, indent=1, default=str) + "\n")
            (OUT / "workbooks").mkdir(exist_ok=True)
            shutil.copy(src, OUT / "workbooks" / f"{name}.xlsx")
            (OUT / "encoded").mkdir(exist_ok=True)
            for enc in ENCODINGS:
                try:
                    (OUT / "encoded" / f"{name}.{enc}.txt").write_text(encode(src, enc))
                except Exception as ex:
                    assert enc not in REQUIRED_ENCS, (name, enc, ex)
            if e["source"] == "enron":
                (OUT / "sources").mkdir(exist_ok=True)
                shutil.copy(src, OUT / "sources" / e["file"])
            manifest[name] = {**e, "questions": len(qs), "types": [q["type"] for q in qs],
                              "committed_in_git": e["source"] == "enron"}
            listing.append(f"## {name} ({e['source']}: `{e.get('original', e['file'])}`)\n")
            for q in qs:
                tr = q["truth"]
                tr = tr if not isinstance(tr, list) or len(tr) <= 8 else f"{len(tr)} cells, e.g. {tr[:3]}"
                sheet = q["cell"].rsplit("!", 1)[0]
                listing += [f"- **{q['id']}** ({q['type']}) {q['q']}", f"  - answer: `{tr}`; cell `{q['cell']}`"]
                if q["type"] == "trace":
                    listing.append(f"  - formula: `{book.formula(q['cell'])}`")
                if q.get("labels"):
                    listing.append("  - read: " + "; ".join(source_line(book, f"{sheet}!{c}") for c in q["labels"]))
                listing.append("")
            print(f"{name}: {len(qs)} questions")
    if not check:
        mpath.write_text(json.dumps(
            {"about": "Written by external/realworld2.py build.", "workbooks": dict(sorted(manifest.items()))},
                                    indent=1) + "\n")
        if not a.only:
            (OUT / "questions.md").write_text("\n".join(listing) + "\n")
    return 1 if bad else 0


def freeze(_a):
    """The freeze manifest (docs/PROTOCOL.md section 9) is written by benchmarks/freeze.py."""
    import runpy
    runpy.run_path(str(BENCH / "freeze.py"), run_name="__main__")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "fetch", "build", "check", "freeze"])
    ap.add_argument("--damodaran", help="select: folder of the converted Damodaran .xlsx files")
    ap.add_argument("--enron", help="select: folder of the extracted Enron spreadsheets")
    ap.add_argument("--out-files", default=DEFAULT_FILES[0], help="select: where the chosen source files are copied")
    ap.add_argument("--files", help="fetch/build/check: folder holding the chosen source files")
    ap.add_argument("--only", help="comma list of workbook names")
    a = ap.parse_args(argv)
    if a.mode == "select":
        return select(a)
    if a.mode == "freeze":
        return freeze(a)
    if a.mode == "fetch":
        return fetch(a)
    return build(a, check=a.mode == "check")


if __name__ == "__main__":
    sys.exit(main() or 0)
