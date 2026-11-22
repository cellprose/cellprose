"""Targeted reads of a workbook for agents: outline, read_range, find and trace (experiments/E33).

Each returns plain text in Cellprose notation, so an agent can map a large workbook first and then read only the cells
a question needs, instead of loading the whole file or writing openpyxl code. The MCP server and the benchmark's
`agent_cellprose_tools` arm call these same functions.

    outline(path)                      index of every region + the compact profile (long regions elided)
    read_range(path, "Sheet!A1:F40")   that rectangle as Cellprose (values, formulas, formats)
    find(path, "Net Income")           cells whose text contains the words, with the values to their right
    trace(path, "Sheet!E12")           a formula's direct precedents, or (dependents=True) every cell that reads it
    index(path)                        the region map only (headings, sizes, header rows), no values
    read_ranges(path, [refs])          several rectangles in one call, formats blocks left out by default
    whatif(path, "Sheet!B3", factor=1.1)  set one cell, recalculate with LibreOffice, list the cells whose value changes

The lean agent of experiments/E34 uses index, read_ranges, find, trace(compact=True) and whatif.
"""
from __future__ import annotations

import shutil
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.utils import get_column_letter as L
from openpyxl.utils import range_boundaries

from .writer import Options, detect_regions, dumps_workbook, fmt_value, is_formula_cell, load_pair, quote_sheet

OUTLINE_ROWS = 6          # rows kept per region in the outline (head + tail), before the rest is elided
MAX_HITS = 30
MAX_EXPAND = 50_000       # cells a single range reference may expand to when tracing (whole-column refs are clipped)


@lru_cache(maxsize=4)
def _pair(path: str, mtime: float):
    return load_pair(path)


def _load(path):
    p = Path(path)
    return _pair(str(p), p.stat().st_mtime)


def _sheet(fwb, name: str):
    name = name.strip().strip("'")
    for ws in fwb.worksheets:
        if ws.title == name or ws.title.lower() == name.lower():
            return ws
    raise ValueError(f"no sheet {name!r}; sheets are {fwb.sheetnames}")


def split_ref(ref: str, fwb, default: str | None = None) -> tuple[str, str]:
    ref = ref.replace("$", "").strip()
    if "!" in ref:
        sh, rng = ref.rsplit("!", 1)
    else:
        sh, rng = default or fwb.worksheets[0].title, ref
    return _sheet(fwb, sh).title, rng.upper()


def _shown(fws, vws, r, c) -> str:
    fc, vc = fws.cell(row=r, column=c), vws.cell(row=r, column=c)
    f = is_formula_cell(fc)
    v = vc.value if f else fc.value
    return "?" if v is None and f else fmt_value(v, computed=f)


# ------------------------------------------------------------------ outline

def index_lines(fwb, vwb, max_rows: int = OUTLINE_ROWS) -> list[str]:
    """Per sheet: used range, region and formula counts. Then each region longer than `max_rows` rows (the ones the
    outline elides): `Sheet!A1:F900 rows=900 formulas=12 | first row: Date|Units|Price`."""
    out = []
    for fws in fwb.worksheets:
        vws = vwb[fws.title]
        regions, loose = detect_regions(fws)
        nf = sum(1 for row in fws.iter_rows() for c in row if is_formula_cell(c))
        out.append(f"{quote_sheet(fws.title)}: used {fws.dimensions}, {len(regions)} regions, {len(loose)} loose cells, "
                   f"{nf} formulas")
        for (r1, c1, r2, c2) in regions:
            if r2 - r1 + 1 <= max_rows:
                continue
            n = sum(1 for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if is_formula_cell(fws.cell(row=r, column=c)))
            first = [x for x in (_shown(fws, vws, r1, c) for c in range(c1, c2 + 1)) if x][:8]
            label = "|".join(first)
            label = label if len(label) <= 80 else label[:77] + "..."
            out.append(f"  {quote_sheet(fws.title)}!{L(c1)}{r1}:{L(c2)}{r2} rows={r2 - r1 + 1} formulas={n} | first row: {label}")
    return out


def outline(path, max_rows: int = OUTLINE_ROWS) -> str:
    """The region index, then the workbook in the compact profile: regions longer than `max_rows` rows show their
    first and last rows only (the formulas and formats blocks still cover every row). Read the elided rows with
    read_range."""
    fwb, vwb = _load(path)
    text = dumps_workbook(fwb, vwb, Options(max_rows=max_rows, keep_tail=2))
    idx = ["```index", *index_lines(fwb, vwb, max_rows), "```", ""]
    head, sep, body = text.partition("\n# ")
    return head + "\n".join(idx) + sep + body if sep else text + "\n" + "\n".join(idx)


MAX_REGIONS = 40          # regions listed per sheet by the index-only outline


def index(path, max_regions: int = MAX_REGIONS) -> str:
    """Index-only outline: per sheet its used range and counts, then every region with its size, formula count and
    first row (a label preview, not data). No other cell values: read them with read_range. About 30 tokens a region."""
    fwb, vwb = _load(path)
    out = [f"{len(fwb.worksheets)} sheets. Regions are rectangles of non-empty cells; read any of them with read_range.",
           "```index"]
    for fws in fwb.worksheets:
        vws = vwb[fws.title]
        regions, loose = detect_regions(fws)
        nf = sum(1 for row in fws.iter_rows() for c in row if is_formula_cell(c))
        out.append(f"{quote_sheet(fws.title)}: used {fws.dimensions}, {len(regions)} regions, {len(loose)} loose cells, "
                   f"{nf} formulas")
        for (r1, c1, r2, c2) in regions[:max_regions]:
            n = sum(1 for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if is_formula_cell(fws.cell(row=r, column=c)))
            first = [x for x in (_shown(fws, vws, r1, c) for c in range(c1, c2 + 1)) if x][:5]
            label = "|".join(x if len(x) <= 30 else x[:27] + "..." for x in first)
            out.append(f"  {L(c1)}{r1}:{L(c2)}{r2} rows={r2 - r1 + 1} formulas={n} | {label}")
        if len(regions) > max_regions:
            out.append(f"  ... {len(regions) - max_regions} more regions; read_range {quote_sheet(fws.title)}!{fws.dimensions}")
        if loose:
            out.append("  loose cells: " + ", ".join(f"{L(c)}{r}" for r, c in loose[:12]) + (" ..." if len(loose) > 12 else ""))
    names = sorted(n for n, d in fwb.defined_names.items() if d.attr_text)
    out.append("```")
    if names:
        out.append(f"{len(names)} defined names: " + ", ".join(names[:30]) + (" ..." if len(names) > 30 else ""))
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ read_range

def read_ranges(path, refs: list[str], formats: bool = False) -> str:
    """Several ranges in one call; `formats` blocks left out unless asked."""
    import re
    parts = [read_range(path, r) for r in refs]
    text = "\n".join(parts)
    if not formats:
        text = re.sub(r"```formats\n.*?```\n\n?", "", text, flags=re.S)
    return text


def read_range(path, ref: str) -> str:
    """`Sheet!A1:F40` (or a single cell) as Cellprose: the region table clipped to the range, with its formulas and
    formats blocks. Front matter is left out."""
    fwb, vwb = _load(path)
    sheet, rng = split_ref(ref, fwb)
    if ":" not in rng:
        rng = f"{rng}:{rng}"
    range_boundaries(rng)
    text = dumps_workbook(fwb, vwb, Options(sheets=[sheet], cell_range=rng, legend=False))
    body = text.split("---\n", 2)[-1].lstrip("\n").split("\n# Names\n", 1)[0].rstrip() + "\n"
    return body if "## " in body or "```cells" in body else f"# Sheet: {quote_sheet(sheet)}\n\n(no cells in {rng})\n"


# ------------------------------------------------------------------ find

def find(path, text: str, sheet: str | None = None, limit: int = MAX_HITS) -> str:
    """Cells whose shown text contains `text` (case-insensitive), each with up to 6 non-empty cells to its right
    (`label mode`: the row a label names)."""
    fwb, vwb = _load(path)
    needle = text.strip().lower()
    if not needle:
        raise ValueError("text is empty")
    hits, total = [], 0
    for fws in fwb.worksheets:
        if sheet and fws.title.lower() != sheet.strip("'").lower():
            continue
        vws = vwb[fws.title]
        for row in fws.iter_rows():
            for c in row:
                if c.value is None:
                    continue
                shown = _shown(fws, vws, c.row, c.column)
                if needle not in shown.lower():
                    continue
                shown = shown if len(shown) <= 100 else shown[:97] + "..."
                total += 1
                if len(hits) >= limit:
                    continue
                right = []
                for cc in range(c.column + 1, min(fws.max_column, c.column + 40) + 1):
                    if fws.cell(row=c.row, column=cc).value is not None:
                        rv = _shown(fws, vws, c.row, cc)
                        right.append(f"{L(cc)}{c.row}: {rv if len(rv) <= 40 else rv[:37] + '...'}")
                        if len(right) == 6:
                            break
                hits.append(f"{quote_sheet(fws.title)}!{c.coordinate}: {shown}" + (" -> " + ", ".join(right) if right else ""))
    if not hits:
        return f"no cell contains {text!r}"
    more = f"\n... {total - len(hits)} more; narrow the text or pass sheet" if total > len(hits) else ""
    return "\n".join(hits) + more


# ------------------------------------------------------------------ trace

def _refs(fwb, sheet: str, formula: str) -> list[tuple[str, int, int, int, int]]:
    """(sheet, c1, r1, c2, r2) for every range a formula reads; defined names resolved."""
    names = {n.lower(): d.attr_text for n, d in fwb.defined_names.items() if d.attr_text}
    out = []
    for t in Tokenizer(formula).items:
        if t.type != "OPERAND" or t.subtype != "RANGE":
            continue
        v = names.get(t.value.lower(), t.value)
        for part in v.split(","):
            try:
                sh, rng = split_ref(part, fwb, sheet)
                ws = fwb[sh]
                c1, r1, c2, r2 = range_boundaries(rng)
            except Exception:
                continue
            c1, r1 = c1 or 1, r1 or 1
            c2, r2 = min(c2 or ws.max_column, ws.max_column), min(r2 or ws.max_row, ws.max_row)
            out.append((sh, c1, r1, c2, r2))
    return out


def _cells(fwb, refs):
    for sh, c1, r1, c2, r2 in refs:
        n = (c2 - c1 + 1) * (r2 - r1 + 1)
        if n > MAX_EXPAND:
            continue
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                yield f"{quote_sheet(sh)}!{L(c)}{r}"


def _dependents_index(fwb):
    idx = defaultdict(set)
    for ws in fwb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if is_formula_cell(c):
                    me = f"{quote_sheet(ws.title)}!{c.coordinate}"
                    for p in _cells(fwb, _refs(fwb, ws.title, c.value)):
                        idx[p].add(me)
    return idx


def _order(fwb, ref):
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
    sh, coord = ref.rsplit("!", 1)
    col, row = coordinate_from_string(coord)
    return fwb.sheetnames.index(sh.strip("'")) if sh.strip("'") in fwb.sheetnames else 0, row, column_index_from_string(col)


def _value(fwb, vwb, ref):
    sh, coord = ref.rsplit("!", 1)
    sh = sh.strip("'")
    fc, vc = fwb[sh][coord], vwb[sh][coord]
    if is_formula_cell(fc):
        return f"= {fc.value[1:]}  # {'?' if vc.value is None else fmt_value(vc.value, computed=True)}"
    return ": " + ("(empty)" if fc.value is None else fmt_value(fc.value))


def compress(fwb, cells) -> list[str]:
    """Cell addresses as ranges: runs down a column merged first (`daily!D87:D120`), then equal row spans across
    adjacent columns (`daily!D87:F120`)."""
    from openpyxl.utils.cell import column_index_from_string, coordinate_from_string
    by_sheet = defaultdict(list)
    for ref in cells:
        sh, coord = ref.rsplit("!", 1)
        col, row = coordinate_from_string(coord)
        by_sheet[sh].append((column_index_from_string(col), row))
    out = []
    for sh in sorted(by_sheet, key=lambda x: fwb.sheetnames.index(x.strip("'")) if x.strip("'") in fwb.sheetnames else 0):
        runs = []                                   # (col, r1, r2)
        for c, r in sorted(by_sheet[sh]):
            if runs and runs[-1][0] == c and runs[-1][2] == r - 1:
                runs[-1] = (c, runs[-1][1], r)
            else:
                runs.append((c, r, r))
        blocks = []                                 # (c1, c2, r1, r2)
        for c, r1, r2 in sorted(runs, key=lambda x: (x[1], x[2], x[0])):
            if blocks and blocks[-1][2:] == (r1, r2) and blocks[-1][1] == c - 1:
                blocks[-1] = (blocks[-1][0], c, r1, r2)
            else:
                blocks.append((c, c, r1, r2))
        for c1, c2, r1, r2 in sorted(blocks, key=lambda b: (b[2], b[0])):
            a, b = f"{L(c1)}{r1}", f"{L(c2)}{r2}"
            out.append(f"{sh}!{a}" if a == b else f"{sh}!{a}:{b}")
    return out


def trace(path, ref: str, dependents: bool = False, transitive: bool = False, limit: int = 200,
          compact: bool = False) -> str:
    """Precedents: the cells the formula at `ref` reads directly (ranges expanded). Dependents: the formula cells
    that read `ref` directly, or with transitive=True every cell whose value depends on it."""
    fwb, vwb = _load(path)
    sheet, coord = split_ref(ref, fwb)
    me = f"{quote_sheet(sheet)}!{coord}"
    head = f"{me}{_value(fwb, vwb, me)}"
    if not dependents:
        fc = fwb[sheet][coord]
        if not is_formula_cell(fc):
            return head + "\n(not a formula: no precedents)"
        cells = sorted(set(_cells(fwb, _refs(fwb, sheet, fc.value))), key=lambda x: _order(fwb, x))
        title = f"{len(cells)} direct precedents"
    else:
        idx = _pair_index(fwb)
        seen, todo = set(), [me]
        while todo:
            cur = todo.pop()
            for d in idx.get(cur, ()):
                if d not in seen:
                    seen.add(d)
                    if transitive:
                        todo.append(d)
        cells = sorted(seen, key=lambda x: _order(fwb, x))
        title = f"{len(cells)} {'cells that depend on it' if transitive else 'direct dependents'}"
    if compact:                 # addresses only, merged into ranges; read values with read_range
        return "\n".join([head, f"{title}: " + ", ".join(compress(fwb, cells))])
    lines = [head, title + (f" (first {limit})" if len(cells) > limit else "") + ":"]
    lines += [f"{c}{_value(fwb, vwb, c)}" for c in cells[:limit]]
    return "\n".join(lines)


def _pair_index(fwb):
    """The dependents index, stored on the workbook object itself so it lives and dies with that object (an id()-keyed
    cache could hand a freed workbook's index to a new one that reuses the id)."""
    idx = getattr(fwb, "_cellprose_dependents", None)
    if idx is None:
        idx = _dependents_index(fwb)
        fwb._cellprose_dependents = idx
    return idx


# ------------------------------------------------------------------ whatif

def _all_values(path) -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    return {f"{quote_sheet(ws.title)}!{c.coordinate}": c.value for ws in wb.worksheets for row in ws.iter_rows()
            for c in row if c.value is not None}


def _same(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= 1e-9 * max(abs(a), abs(b), 1)
    return a == b


def _saved_recalc(path: Path, edit=None, timeout: int = 300) -> dict:
    """Values after an openpyxl save (with `edit` = (sheet, coord, value) applied) and a LibreOffice recalculation.
    The unchanged baseline goes through the same round trip, so what the round trip itself changes cancels out."""
    import openpyxl
    import tempfile
    from .recalc import recalc_copy
    wb = openpyxl.load_workbook(path)
    if edit:
        wb[edit[0]][edit[1]].value = edit[2]
    tmp = Path(tempfile.mkdtemp(prefix="cellprose-whatif-")) / path.name
    out = None
    try:
        wb.save(tmp)
        out = recalc_copy(tmp, timeout=timeout)
        return _all_values(out)
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)
        if out is not None:
            shutil.rmtree(out.parent, ignore_errors=True)


_BASE_CACHE: dict = {}


def _base_values(path: str, mtime: float, timeout: int = 300):
    """Baseline values, cached per (path, mtime) only: the timeout does not change the result."""
    key = (path, mtime)
    if key not in _BASE_CACHE:
        if len(_BASE_CACHE) >= 4:
            _BASE_CACHE.pop(next(iter(_BASE_CACHE)))
        _BASE_CACHE[key] = _saved_recalc(Path(path), timeout=timeout)
    return _BASE_CACHE[key]


def whatif(path, cell: str, value=None, factor: float | None = None, timeout: int = 300) -> str:
    """Set `cell` to `value` (or multiply it by `factor`), recalculate with LibreOffice, and list every other cell whose
    value changes, as ranges. The file itself is not changed. `timeout` (seconds) bounds each of the two LibreOffice runs."""
    import openpyxl
    p = Path(path)
    fwb, _ = _load(p)
    sheet, coord = split_ref(cell, fwb)
    wb = openpyxl.load_workbook(p)
    old = wb[sheet][coord].value
    if factor is not None:
        if not isinstance(old, (int, float)) or isinstance(old, bool):
            raise ValueError(f"{sheet}!{coord} holds {old!r}, not a number")
        new = old * float(factor)
    else:
        new = value
    after = _saved_recalc(p, (sheet, coord, new), timeout)
    base = _base_values(str(p), p.stat().st_mtime, timeout)
    me = f"{quote_sheet(sheet)}!{coord}"
    changed = sorted((k for k in set(base) | set(after) if k != me and not _same(base.get(k), after.get(k))),
                     key=lambda x: _order(fwb, x))
    head = f"{me}: {old!r} -> {new!r}; {len(changed)} other cells change value"
    return head + (": " + ", ".join(compress(fwb, changed)) if changed else "")
