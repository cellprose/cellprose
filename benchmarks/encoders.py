"""Encode a recalculated .xlsx as text in each benchmark format.

Baselines follow common practice (header = first row, values only):
  csv, markdown (MarkItDown style), markdown_kv (improvingagents style), toon (official encoder)
Address-aware control:
  grid_values  — Sheetmark grid with A1 coordinates but no formulas, formats or names
Sheetmark variants (SPEC.md v0.1):
  sheetmark         — letter headers, formulas in a separate block with fill ranges
  sheetmark_inline  — letter headers, formulas inline in each grid cell
  sheetmark_labels  — header row shows "letter: label", formulas in a separate block
  cellprose_v03     — the shipped v0.3 writer (pipe-less rows, array formulas, comments, validation, row-number
                      legend). The compared encoding for every new run (docs/PROTOCOL.md section 1)
  cellprose_v03_nolegend — the same text without the SPEC 3.1 legend line; what E28-E30 ran under the old id
                      `sheetmark_v03` (see LEGACY: old ids still resolve, so old raw results score unchanged)
  sheetmark_lean_gfm_nopipe — sheetmark_lean_gfm with the grid's outer pipes and trailing empty cells dropped
                      (`2|Units|1200`); GitHub renders the same tables (E19)
"""
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

import openpyxl
from openpyxl.formula.translate import Translator
from openpyxl.utils import get_column_letter as L

ROOT = Path(__file__).parent
ENCODINGS = ["csv", "markdown", "markdown_kv", "toon", "grid_values",
             "sheetmark", "sheetmark_inline", "sheetmark_labels", "sheetmark_lean", "sheetmark_lean_gfm", "markitdown",
             "sheetmark_lean_gfm_nopipe", "cellprose_v03", "cellprose_v03_nolegend"]

from runner.ids import LEGACY, canon   # noqa: E402  (old ids still resolve; see runner/ids.py)

# Experimental (backlog B20): v0.2 plus a comment on each multi-cell fill range showing its last cell's formula, e.g.
# `C2:E2 = B2*(1+g)  # E2 = D2*(1+g)`. Not a registered encoding: it is not in ENCODINGS, so no default run sends it, and
# the v0.2 reader does not accept the comment (see experiments/E22-fill-range-hint.md). `add_fill_hints` works on the
# finished v0.2 text, so the hint file is the committed v0.2 file plus comments and nothing else.
HINT_ENCODING = "sheetmark_lean_gfm_hint"

NUMLIKE = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$|^\d{4}-\d{2}-\d{2}|^(TRUE|FALSE|\?)$|^#[A-Z/0!?]+")


# ------------------------------------------------------------ value rendering
def fmt(v, escape=True):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else "%.10g" % v
    if isinstance(v, dt.datetime):
        return v.date().isoformat() if v.time() == dt.time(0) else v.isoformat(timespec="seconds")
    if isinstance(v, dt.date):
        return v.isoformat()
    s = str(v)
    if escape:
        if NUMLIKE.match(s) or s.startswith("=") or s.startswith("'"):
            s = "'" + s
        s = s.replace("|", "\\|").replace("\n", "<br>")
    return s


def load(path):
    return openpyxl.load_workbook(path), openpyxl.load_workbook(path, data_only=True)


def grid(ws):
    """Cell values of a sheet as rows. A chart sheet or an empty sheet has none: callers get [[]] so that the first row
    (the header) always exists and the sheet encodes as a heading with no data."""
    if not hasattr(ws, "max_row"):
        return [[]]
    rows = []
    for r in range(1, ws.max_row + 1):
        rows.append([ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)])
    while rows and all(v is None for v in rows[-1]):
        rows.pop()
    return rows or [[]]


def headers(row):
    """pandas-style column names for header=0."""
    out, seen = [], {}
    for i, v in enumerate(row):
        h = fmt(v, escape=False) if v is not None else f"Unnamed: {i}"
        if h in seen:
            seen[h] += 1
            h = f"{h}.{seen[h]}"
        else:
            seen[h] = 0
        out.append(h)
    return out


# ------------------------------------------------------------ baselines
def enc_csv(fwb, vwb):
    import csv, io
    parts = []
    for ws in vwb:
        g = grid(ws)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(headers(g[0]))
        for row in g[1:]:
            w.writerow([fmt(v, escape=False) for v in row])
        parts.append(f"## {ws.title}\n{buf.getvalue()}")
    return "\n".join(parts)


def enc_markdown(fwb, vwb):
    parts = []
    for ws in vwb:
        g = grid(ws)
        h = headers(g[0])
        lines = ["| " + " | ".join(x.replace("|", "\\|") for x in h) + " |", "|" + "---|" * len(h)]
        for row in g[1:]:
            lines.append("| " + " | ".join(fmt(v, escape=False).replace("|", "\\|") for v in row) + " |")
        parts.append(f"## {ws.title}\n" + "\n".join(lines))
    return "\n\n".join(parts)


def enc_markdown_kv(fwb, vwb):
    parts = []
    for ws in vwb:
        g = grid(ws)
        h = headers(g[0])
        out = [f"# {ws.title}"]
        for i, row in enumerate(g[1:], 1):
            kv = [f"{k}: {fmt(v, escape=False)}" for k, v in zip(h, row) if v is not None]
            if kv:
                out.append(f"## Record {i}\n```\n" + "\n".join(kv) + "\n```")
        parts.append("\n\n".join(out))
    return "\n\n".join(parts)


def enc_toon(fwb, vwb):
    data = {}
    for ws in vwb:
        g = grid(ws)
        h = headers(g[0])
        recs = []
        for row in g[1:]:
            rec = {}
            for k, v in zip(h, row):
                if isinstance(v, (dt.date, dt.datetime)):
                    v = fmt(v)
                elif isinstance(v, float) and not v.is_integer():
                    v = float("%.10g" % v)
                rec[k] = v
            recs.append(rec)
        data[ws.title] = recs
    r = subprocess.run(["node", str(ROOT / "toon_encode.mjs")], input=json.dumps(data, default=str),
                       capture_output=True, text=True, check=True, cwd=ROOT)
    return r.stdout


def enc_markitdown(path):
    """Microsoft MarkItDown's own output for the workbook (the pinned version in pyproject.toml; `pip install -e ".[bench]"`).
    Unlike `markdown` above, which only imitates it, this is the real converter, so the baseline is what a user who runs
    `markitdown book.xlsx` gets: pandas reads cached values (formulas are lost), one table per sheet under `## <sheet>`."""
    from markitdown import MarkItDown
    return MarkItDown(enable_plugins=False).convert(str(path)).text_content


# ------------------------------------------------------------ Sheetmark
def regions(ws):
    cells = {(c.row, c.column) for row in ws.iter_rows() for c in row if c.value is not None}
    seen, comps = set(), []
    for start in sorted(cells):
        if start in seen:
            continue
        stack, comp = [start], []
        seen.add(start)
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    n = (r + dr, c + dc)
                    if n in cells and n not in seen:
                        seen.add(n); stack.append(n)
        rs = [p[0] for p in comp]; cs = [p[1] for p in comp]
        comps.append([min(rs), min(cs), max(rs), max(cs), len(comp)])
    merged = True
    while merged:  # merge overlapping bounding boxes
        merged = False
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                a, b = comps[i], comps[j]
                if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                    comps[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]]
                    comps.pop(j); merged = True
                    break
            if merged:
                break
    boxes = sorted(comps)
    return [b[:4] for b in boxes if b[4] > 1], [b[:4] for b in boxes if b[4] == 1]


def is_formula(v):
    return isinstance(v, str) and v.startswith("=")


def fill_ranges(cells, same):
    """Greedy row-major grouping of {(r,c): x} into rectangles where same(anchor, cell) holds."""
    left, out = dict(cells), []
    for (r, c) in sorted(cells):
        if (r, c) not in left:
            continue
        a = left[(r, c)]
        c2 = c
        while (r, c2 + 1) in left and same(a, (r, c), left[(r, c2 + 1)], (r, c2 + 1)):
            c2 += 1
        r2 = r
        while all((r2 + 1, k) in left and same(a, (r, c), left[(r2 + 1, k)], (r2 + 1, k)) for k in range(c, c2 + 1)):
            r2 += 1
        for rr in range(r, r2 + 1):
            for cc in range(c, c2 + 1):
                left.pop((rr, cc))
        rng = f"{L(c)}{r}" if (r, c) == (r2, c2) else f"{L(c)}{r}:{L(c2)}{r2}"
        out.append((rng, a))
    return out


def formula_same(fa, pa, fb, pb):
    try:
        return Translator(fa, origin=f"{L(pa[1])}{pa[0]}").translate_formula(f"{L(pb[1])}{pb[0]}") == fb
    except Exception:
        return False


def enc_sheetmark(fwb, vwb, mode="block", values_only=False):
    out = ["---", "sheetmark: 0.1", "profile: full",
           "sheets: [" + ", ".join(ws.title for ws in fwb) + "]", "not_preserved: [styles]", "---", ""]
    for fws in fwb:
        vws = vwb[fws.title]
        out += [f"# Sheet: {fws.title}", ""]
        regs, loose = regions(fws)
        for (r1, c1, r2, c2) in regs:
            out += [f"## Range {L(c1)}{r1}:{L(c2)}{r2}", ""]
            body_r1 = r1
            if mode == "labels" and r2 > r1:
                hdr = []
                for c in range(c1, c2 + 1):
                    lab = vws.cell(row=r1, column=c).value
                    hdr.append(f"{L(c)}: {fmt(lab)}" if lab is not None else L(c))
                body_r1 = r1 + 1
            else:
                hdr = [L(c) for c in range(c1, c2 + 1)]
            out.append("| # | " + " | ".join(hdr) + " |")
            out.append("|---|" + "---|" * len(hdr))
            for r in range(body_r1, r2 + 1):
                cells = []
                for c in range(c1, c2 + 1):
                    fv = fws.cell(row=r, column=c).value
                    vv = vws.cell(row=r, column=c).value
                    if mode == "inline" and is_formula(fv) and not values_only:
                        cells.append(f"{fv} → {fmt(vv) or '?'}".replace("|", "\\|"))
                    else:
                        cells.append(fmt(vv) if not (is_formula(fv) and vv is None) else "?")
                out.append(f"| {r} | " + " | ".join(cells) + " |")
            out.append("")
            if values_only:
                continue
            if mode != "inline":
                fcells = {(r, c): fws.cell(row=r, column=c).value for r in range(r1, r2 + 1)
                          for c in range(c1, c2 + 1) if is_formula(fws.cell(row=r, column=c).value)}
                if fcells:
                    out.append("```formulas")
                    out += [f"{rng} = {f[1:]}" for rng, f in fill_ranges(fcells, formula_same)]
                    out += ["```", ""]
            fmts = {(r, c): fws.cell(row=r, column=c).number_format for r in range(r1, r2 + 1)
                    for c in range(c1, c2 + 1)
                    if fws.cell(row=r, column=c).value is not None and fws.cell(row=r, column=c).number_format != "General"}
            if fmts:
                out.append("```formats")
                out += [f'{rng} = "{f}"' for rng, f in fill_ranges(fmts, lambda a, pa, b, pb: a == b)]
                out += ["```", ""]
        if loose:
            out.append("```cells")
            for (r, c, _, _) in loose:
                fv = fws.cell(row=r, column=c).value
                vv = vws.cell(row=r, column=c).value
                addr = f"{L(c)}{r}"
                if is_formula(fv) and not values_only:
                    out.append(f"{addr} = {fv[1:]}  # {fmt(vv)}")
                else:
                    out.append(f"{addr}: {fmt(vv)}")
            out += ["```", ""]
    names = list(fwb.defined_names.items())
    if names and not values_only:
        out += ["# Names", "", "```names"] + [f"{n} = {d.attr_text}" for n, d in sorted(names)] + ["```", ""]
    return "\n".join(out).rstrip() + "\n"


def fmt_lean(v, is_f):
    """Formula results are display values (recomputable), so 6 significant figures; typed values stay exact."""
    if is_f and isinstance(v, float) and not v.is_integer():
        r = float("%.6g" % v)  # 6 significant figures, but never scientific notation for ordinary sizes
        if 1e-4 <= abs(r) < 1e15:
            return str(int(r)) if r.is_integer() else format(r, "f").rstrip("0").rstrip(".")
        return "%.6g" % v
    return fmt(v)


def csv_cell(s):
    return '"' + s.replace('"', '""') + '"' if any(ch in s for ch in ',"\n') else s


def enc_lean(fwb, vwb, gfm=False):
    out = ["---", "sheetmark: 0.1", "---", ""]
    for fws in fwb:
        vws = vwb[fws.title]
        out += [f"# Sheet: {fws.title}", ""]
        regs, loose = regions(fws)
        for (r1, c1, r2, c2) in regs:
            cols = [L(c) for c in range(c1, c2 + 1)]
            if gfm:  # compact GFM table: renders on GitHub, no padding spaces
                out += [f"## {L(c1)}{r1}:{L(c2)}{r2}", "", "|#|" + "|".join(cols) + "|", "|-" * (len(cols) + 1) + "|"]
            else:
                out += [f"## {L(c1)}{r1}:{L(c2)}{r2}", "```grid", "#," + ",".join(cols)]
            for r in range(r1, r2 + 1):
                cells = []
                for c in range(c1, c2 + 1):
                    fv = fws.cell(row=r, column=c).value
                    vv = vws.cell(row=r, column=c).value
                    f = is_formula(fv)
                    if gfm:
                        cells.append("?" if f and vv is None else fmt_lean(vv, f))
                    else:
                        cells.append("?" if f and vv is None else csv_cell(fmt_lean(vv, f).replace("\\|", "|")))
                if gfm:
                    out.append(f"|{r}|" + "|".join(cells) + "|")
                else:
                    out.append(f"{r}," + ",".join(cells).rstrip(","))
            out.append("" if gfm else "```")
            fcells = {(r, c): fws.cell(row=r, column=c).value for r in range(r1, r2 + 1)
                      for c in range(c1, c2 + 1) if is_formula(fws.cell(row=r, column=c).value)}
            if fcells:
                out.append("```formulas")
                out += [f"{rng} = {f[1:]}" for rng, f in fill_ranges(fcells, formula_same)]
                out.append("```")
            fmts = {(r, c): fws.cell(row=r, column=c).number_format for r in range(r1, r2 + 1)
                    for c in range(c1, c2 + 1)
                    if fws.cell(row=r, column=c).value is not None and fws.cell(row=r, column=c).number_format != "General"}
            if fmts:
                out.append("```formats")
                out += [f"{rng} = {f}" for rng, f in fill_ranges(fmts, lambda a, pa, b, pb: a == b)]
                out.append("```")
            out.append("")
        if loose:
            out.append("```cells")
            for (r, c, _, _) in loose:
                fv = fws.cell(row=r, column=c).value
                vv = vws.cell(row=r, column=c).value
                addr = f"{L(c)}{r}"
                out.append(f"{addr} = {fv[1:]}  # {fmt_lean(vv, True)}" if is_formula(fv) else f"{addr}: {fmt(vv)}")
            out += ["```", ""]
    names = list(fwb.defined_names.items())
    if names:
        out += ["# Names", "```names"] + [f"{n} = {d.attr_text}" for n, d in sorted(names)] + ["```", ""]
    return "\n".join(out).rstrip() + "\n"


def drop_outer_pipes(text):
    """`|2|Units|1200||` -> `2|Units|1200`. GFM makes the outer pipes optional and pads short rows with empty cells,
    so the rendered table is unchanged. Only grid lines (outside code fences, starting with `|`) are touched; an empty
    row keeps one pipe (`5|`) so it stays a table row."""
    out, fence = [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fence = not fence
        elif not fence and line.startswith("|"):
            line = line[1:-1]
            while line.endswith("|") and not line.endswith("\\|") and line.count("|") > 1:
                line = line[:-1]
            if "|" not in line:
                line += "|"
        out.append(line)
    return "\n".join(out)


def add_fill_hints(text):
    """Append `  # <last cell> = <its formula>` to each fill range in `formulas` blocks whose formula shifts. A range whose
    formula has no relative reference (`B3:E3 = Price`) repeats itself, so a hint would add tokens and no information."""
    out, fence = [], None
    for line in text.split("\n"):
        if line.startswith("```"):
            fence = None if fence else line[3:]
        elif fence == "formulas" and " = " in line and ":" in line.split(" = ", 1)[0]:
            rng, f = line.split(" = ", 1)
            first, last = rng.split(":")
            try:
                shown = Translator("=" + f, origin=first).translate_formula(last)[1:]
            except Exception:
                shown = f
            if shown != f:
                line = f"{line}  # {last} = {shown}"
        out.append(line)
    return "\n".join(out)


def enc_v03(path):
    """The shipped v0.3 writer (src/cellprose/writer.py), not a benchmark-local encoder."""
    import sys
    sys.path.insert(0, str(ROOT.parent / "src"))
    from cellprose import writer
    fwb, vwb = writer.load_pair(path)
    return writer.dumps_workbook(fwb, vwb, writer.Options(legend=False))      # v0.3.0 text: earlier runs stay comparable


def enc_v031(path):
    """The shipped writer with the SPEC 3.1 row-number legend (experiments/E31)."""
    import sys
    sys.path.insert(0, str(ROOT.parent / "src"))
    from cellprose import writer
    fwb, vwb = writer.load_pair(path)
    return writer.dumps_workbook(fwb, vwb)


def encode(path, kind):
    kind = canon(kind)
    fwb, vwb = load(path)
    return {
        "csv": lambda: enc_csv(fwb, vwb),
        "markdown": lambda: enc_markdown(fwb, vwb),
        "markdown_kv": lambda: enc_markdown_kv(fwb, vwb),
        "toon": lambda: enc_toon(fwb, vwb),
        "grid_values": lambda: enc_sheetmark(fwb, vwb, values_only=True),
        "sheetmark": lambda: enc_sheetmark(fwb, vwb),
        "sheetmark_inline": lambda: enc_sheetmark(fwb, vwb, mode="inline"),
        "sheetmark_labels": lambda: enc_sheetmark(fwb, vwb, mode="labels"),
        "sheetmark_lean": lambda: enc_lean(fwb, vwb),
        "sheetmark_lean_gfm": lambda: enc_lean(fwb, vwb, gfm=True),
        "sheetmark_lean_gfm_nopipe": lambda: drop_outer_pipes(enc_lean(fwb, vwb, gfm=True)),
        "markitdown": lambda: enc_markitdown(path),
        "cellprose_v03_nolegend": lambda: enc_v03(path),
        "cellprose_v03": lambda: enc_v031(path),
        HINT_ENCODING: lambda: add_fill_hints(enc_lean(fwb, vwb, gfm=True)),
    }[kind]()


if __name__ == "__main__":
    import sys
    outdir = ROOT / "encoded"
    outdir.mkdir(exist_ok=True)
    for p in sorted((ROOT / "workbooks").glob("*.xlsx")):
        sizes = {}
        for k in ENCODINGS + [HINT_ENCODING]:
            t = encode(p, k)
            (outdir / f"{p.stem}.{k}.txt").write_text(t)
            sizes[k] = len(t)
        print(p.stem, sizes)
