"""Write a workbook as Cellprose v0.3 text.

Layout (see docs/DESIGN.md, "Format v0.2 at a glance"):

    ---                       front matter
    cellprose: 0.3
    ---
    # Sheet: <name>           one per sheet, workbook order
    ## A1:F9                  one per rectangular region of non-empty cells
    #|A|B|...                 GFM table without outer pipes: row numbers + column letters
    ```formulas               fill ranges: `B4:E4 = B2*B3`
    ```formats                non-General number formats, same range syntax
    ```cells                  loose single cells outside any region
    ```merges                 merged ranges
    ```arrays                 array formulas, `B1:B2 = A1:A2*2`
    ```comments               cell comments, `B7: text`
    ```validation             data validation, `B2:B9 = list: "Yes,No"`
    # Names                   workbook-level defined names

Directly after the front matter, a file with at least one table carries a one-line legend (SPEC §3.1) that says the first
field of a row is its row number, not a column. `Options(legend=False)` omits it (the v0.3.0 text used by earlier benchmark runs).

Formula results are display values rounded to 6 significant figures (they are recomputed on decode);
typed-in values are written exactly. Output is canonical: same workbook, same bytes.
"""
from __future__ import annotations

import datetime as dt
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
from openpyxl.formula.translate import Translator
from openpyxl.utils import get_column_letter as L
from openpyxl.utils import range_boundaries
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula

VERSION = "0.3"
# SPEC §3.1 (revision 0.3.1): the first field of every table row is its row number. Haiku 5.5 counted that field as column A
# and answered one column too far right (experiments/E31). The legend costs about 28 tokens.
LEGEND_A = "Note: the first field of each table row is its row number, not a cell; column A is the second field."
LEGEND_OTHER = "Note: the first field of each table row is its row number, not a cell; the second field is the first column letter in the header."
NUMLIKE = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$|^\d{4}-\d{2}-\d{2}|^\d{2}:\d{2}:\d{2}|^(TRUE|FALSE|\?)$|^#[A-Z/0!?]+")


# ------------------------------------------------------------------ values
def fmt_value(v, *, computed: bool = False, error: bool = False) -> str:
    """Render one cell value. `computed` = the cell holds a formula; `error` = an Excel error value."""
    if v is None:
        return ""
    if error:
        return str(v)
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        if computed:  # display precision: 6 significant figures, no scientific notation for ordinary sizes
            r = float("%.6g" % v)
            if 1e-4 <= abs(r) < 1e15:
                return str(int(r)) if r.is_integer() else repr(r)  # (format(r, "f") would keep 6 decimals, not 6 figures)
            return "%.6g" % v
        return repr(v)  # shortest exact round-trip form
    if isinstance(v, dt.datetime):
        return v.date().isoformat() if v.time() == dt.time(0) else v.isoformat(timespec="seconds")
    if isinstance(v, (dt.date, dt.time)):
        return v.isoformat()
    s = str(v)
    if NUMLIKE.match(s) or s.startswith(("=", "'")):  # text that would read as another type
        s = "'" + s
    s = escape_text(s)
    if s != s.strip() or s.startswith('"'):  # quoted text is always text; inner quotes are doubled
        s = '"' + s.replace('"', '""') + '"'
    return s


def escape_text(s: str) -> str:
    """Make text safe inside a pipe-table cell: \\ and | are backslash-escaped, a literal <br> is written \\<br>,
    and every line break becomes the <br> token (so CRLF and CR read back as LF)."""
    s = s.replace("\\", "\\\\").replace("|", "\\|").replace("<br>", "\\<br>")
    return s.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def is_formula(v) -> bool:
    return isinstance(v, str) and v.startswith("=")


def is_array_anchor(c) -> bool:
    """The top-left cell of an array formula. Its formula goes in the `arrays` block (SPEC §8); the other cells of the
    array hold only their results."""
    return isinstance(c.value, ArrayFormula)


def is_table_cell(c) -> bool:
    """A data-table formula (Excel's what-if `{=TABLE(...)}`). Cellprose has no syntax for these: the cached value is
    written as a typed value and the writer warns (see docs/SPEC.md, "Known limits")."""
    return isinstance(c.value, DataTableFormula)


def array_cells(ws) -> set[tuple[int, int]]:
    """(row, column) of every cell inside an array formula's range, anchor included."""
    out = set()
    for row in ws.iter_rows():
        for c in row:
            if is_array_anchor(c) and c.value.ref:
                c1, r1, c2, r2 = range_boundaries(c.value.ref)
                out.update((r, k) for r in range(r1, r2 + 1) for k in range(c1, c2 + 1))
    return out


def array_lines(ws, bounds=None) -> list[str]:
    """`RANGE = formula`, one per array formula, in row-major order of the anchor."""
    out = []
    for row in ws.iter_rows():
        for c in row:
            if is_array_anchor(c) and c.value.ref and _in_range(c.row, c.column, bounds):
                text = (c.value.text or "").lstrip("=")
                out.append(f"{c.value.ref} = {text}")
    return out


def is_formula_cell(c) -> bool:
    """A formula cell, not a text cell that happens to start with "=" (those have data_type "s"). A lone "=" is an
    empty formula (LibreOffice writes `<f></f>` for one) and has nothing to recompute: it is kept as the text "="."""
    return c.data_type == "f" and is_formula(c.value) and len(c.value) > 1


def is_blank(v) -> bool:
    """No value. Empty text is an empty cell (SPEC.md §6), so a cell holding "" is not part of any region."""
    return v is None or v == ""


def quote_sheet(name: str) -> str:
    return f'"{name}"' if ("#" in name or "\n" in name) else name


# ------------------------------------------------------------------ structure
def detect_regions(ws) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int]]]:
    """Rectangles of 8-connected non-empty cells (merged where boxes overlap), plus loose single cells."""
    cells = {(c.row, c.column) for row in ws.iter_rows() for c in row if not is_blank(c.value)}
    seen, boxes = set(), []
    for start in sorted(cells):
        if start in seen:
            continue
        stack, n = [start], 0
        seen.add(start)
        r1 = r2 = start[0]
        c1 = c2 = start[1]
        while stack:
            r, c = stack.pop()
            n += 1
            r1, r2, c1, c2 = min(r1, r), max(r2, r), min(c1, c), max(c2, c)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    nb = (r + dr, c + dc)
                    if nb in cells and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
        boxes.append([r1, c1, r2, c2, n])
    merged = True
    while merged:
        merged = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                    boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]]
                    boxes.pop(j)
                    merged = True
                    break
            if merged:
                break
    boxes.sort()
    regions = [tuple(b[:4]) for b in boxes if b[4] > 1]
    loose = [(b[0], b[1]) for b in boxes if b[4] == 1]
    return regions, loose


def _same_formula(fa, pa, fb, pb) -> bool:
    try:
        return Translator(fa, origin=f"{L(pa[1])}{pa[0]}").translate_formula(f"{L(pb[1])}{pb[0]}") == fb
    except Exception:
        return False


def fill_ranges(cells: dict, same) -> list[tuple[str, object]]:
    """Greedy row-major grouping of {(row, col): x} into rectangles where `same(anchor, pos, other, pos)` holds."""
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
        out.append((f"{L(c)}{r}" if (r, c) == (r2, c2) else f"{L(c)}{r}:{L(c2)}{r2}", a))
    return out


# ------------------------------------------------------------------ writer
@dataclass
class Options:
    sheets: list[str] | None = None        # only these sheets (all when None)
    cell_range: str | None = None          # only this A1 range, e.g. "A1:F40" (applies to every selected sheet)
    max_rows: int | None = None            # per region; longer regions are elided (compact profile)
    keep_tail: int = 3                     # rows kept at the end of an elided region
    source: str | None = None
    elided: list[str] = field(default_factory=list)
    dropped_tables: list[str] = field(default_factory=list)   # data-table cells written as a value
    legend: bool = True                    # the row-number legend after the front matter (SPEC §3.1)


def _in_range(r, c, bounds):
    if not bounds:
        return True
    c1, r1, c2, r2 = bounds
    return r1 <= r <= r2 and c1 <= c <= c2


def dumps_workbook(fwb, vwb, opts: Options | None = None) -> str:
    """Serialize openpyxl workbooks (formulas view `fwb`, cached-values view `vwb`) as Cellprose."""
    opts = opts or Options()
    bounds = range_boundaries(opts.cell_range) if opts.cell_range else None
    body: list[str] = []
    missing_values = False
    table_starts = set()
    dropped: dict[str, int] = {}
    for fws in fwb.worksheets:
        if opts.sheets and fws.title not in opts.sheets:
            continue
        vws = vwb[fws.title]
        in_array = array_cells(fws)
        body += [f"# Sheet: {quote_sheet(fws.title)}", ""]
        meta = []
        if fws.sheet_state != "visible":
            meta.append(f"hidden: {fws.sheet_state == 'hidden' and 'true' or fws.sheet_state}")
        if fws.freeze_panes:
            meta.append(f"freeze: {fws.freeze_panes}")
        if meta:
            body += ["```meta", *meta, "```", ""]
        regions, loose = detect_regions(fws)
        for (r1, c1, r2, c2) in regions:
            if bounds:  # clip the region to the requested range
                br1, bc1, br2, bc2 = bounds[1], bounds[0], bounds[3], bounds[2]
                r1, c1, r2, c2 = max(r1, br1), max(c1, bc1), min(r2, br2), min(c2, bc2)
                if r1 > r2 or c1 > c2:
                    continue
            rows = list(range(r1, r2 + 1))
            hidden_rows: list[int] = []
            if opts.max_rows and len(rows) > opts.max_rows:
                head = max(opts.max_rows - opts.keep_tail, 1)
                hidden_rows = rows[head:len(rows) - opts.keep_tail]
                rows = rows[:head] + rows[len(rows) - opts.keep_tail:]
            cols = [L(c) for c in range(c1, c2 + 1)]
            table_starts.add(c1)
            body += [f"## {L(c1)}{r1}:{L(c2)}{r2}", "", "#|" + "|".join(cols), "|".join("-" * (len(cols) + 1))]
            for r in rows:
                cells = []
                for c in range(c1, c2 + 1):
                    fc, vc = fws.cell(row=r, column=c), vws.cell(row=r, column=c)
                    f = is_formula_cell(fc)
                    if is_table_cell(fc):
                        opts.dropped_tables.append(f"{fws.title}!{fc.coordinate}")
                        cells.append("?" if vc.value is None else fmt_value(vc.value, error=vc.data_type == "e"))
                        missing_values = missing_values or vc.value is None
                        continue
                    if is_array_anchor(fc) or (r, c) in in_array:   # an array's results are formula results (rounded)
                        shown = None if isinstance(vc.value, ArrayFormula) else vc.value
                        if shown is None and is_array_anchor(fc):
                            cells.append("?")
                            missing_values = True
                        else:
                            cells.append(fmt_value(shown, computed=True, error=vc.data_type == "e"))
                        continue
                    if f and vc.value is None and _is_empty_result(vwb, fws, fc.coordinate):
                        cells.append("")  # the formula calculated to "": an empty cell, not a missing value
                    elif f and vc.value is None:
                        cells.append("?")
                        missing_values = True
                    else:
                        cells.append(fmt_value(vc.value if f else fc.value, computed=f, error=(f or fc.data_type == "e") and vc.data_type == "e"))
                while cells and cells[-1] == "":     # trailing empty cells are left out; a short row is padded on read
                    cells.pop()
                body.append("|".join([str(r), *cells]) if cells else f"{r}|")
                if hidden_rows and r == hidden_rows[0] - 1:
                    body.append("|".join("…" for _ in range(len(cols) + 1)))
            body.append("")
            if hidden_rows:
                body += ["```elided", f"rows: {hidden_rows[0]}-{hidden_rows[-1]}  # {len(hidden_rows)} rows not shown",
                         "```", ""]
                opts.elided.append(f"{fws.title}!{hidden_rows[0]}-{hidden_rows[-1]}")
            fcells = {(r, c): fws.cell(row=r, column=c).value for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                      if is_formula_cell(fws.cell(row=r, column=c))}
            if fcells:
                body += ["```formulas", *[f"{rng} = {f[1:]}" for rng, f in fill_ranges(fcells, _same_formula)], "```", ""]
            fmts = {(r, c): fws.cell(row=r, column=c).number_format for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                    if not is_blank(fws.cell(row=r, column=c).value) and fws.cell(row=r, column=c).number_format != "General"}
            if fmts:
                body += ["```formats", *[f"{rng} = {f}" for rng, f in fill_ranges(fmts, lambda a, pa, b, pb: a == b)],
                         "```", ""]
        loose = [p for p in loose if _in_range(p[0], p[1], bounds)]
        if loose:
            body.append("```cells")
            for (r, c) in loose:
                fc, vc = fws.cell(row=r, column=c), vws.cell(row=r, column=c)
                if is_table_cell(fc):
                    opts.dropped_tables.append(f"{fws.title}!{fc.coordinate}")
                    body.append(f"{L(c)}{r}: {fmt_value(vc.value, error=vc.data_type == 'e')}")
                elif is_array_anchor(fc) or (r, c) in in_array:
                    shown = None if isinstance(vc.value, ArrayFormula) else vc.value
                    body.append(f"{L(c)}{r}: " + ("?" if shown is None else fmt_value(shown, computed=True, error=vc.data_type == "e")))
                    missing_values = missing_values or shown is None
                elif is_formula_cell(fc):
                    shown = '""' if _is_empty_result(vwb, fws, fc.coordinate) else "?" if vc.value is None else fmt_value(vc.value, computed=True, error=vc.data_type == "e")
                    body.append(f"{L(c)}{r} = {fc.value[1:]}  # {shown}")
                else:
                    body.append(f"{L(c)}{r}: {fmt_value(fc.value, error=fc.data_type == 'e')}")
            body += ["```", ""]
            lfmts = {(r, c): fws.cell(row=r, column=c).number_format for (r, c) in loose
                     if fws.cell(row=r, column=c).number_format != "General"}
            if lfmts:   # loose cells keep their number formats in a sheet-level formats block after the cells block
                body += ["```formats", *[f"{rng} = {f}" for rng, f in fill_ranges(lfmts, lambda a, pa, b, pb: a == b)],
                         "```", ""]
        merges = sorted(str(m) for m in fws.merged_cells.ranges)
        if merges:
            body += ["```merges", *merges, "```", ""]
        arrays = array_lines(fws, bounds)
        if arrays:
            body += ["```arrays", *arrays, "```", ""]
        comments = [f"{c.coordinate}: {escape_text(c.comment.text)}" for row in fws.iter_rows() for c in row
                    if c.comment is not None and (c.comment.text or "").strip() and _in_range(c.row, c.column, bounds)]
        if comments:
            body += ["```comments", *comments, "```", ""]
        validations = validation_lines(fws)
        if validations:
            body += ["```validation", *validations, "```", ""]
        for k, n in count_dropped(fws).items():
            dropped[k] = dropped.get(k, 0) + n
    # a name with no target (LibreOffice leaves `_xlfn_*` placeholders like this) names nothing: it is left out
    names = sorted((n, d.attr_text) for n, d in fwb.defined_names.items() if d.attr_text)
    local = sorted((ws.title, n, d.attr_text) for ws in fwb.worksheets for n, d in ws.defined_names.items() if d.attr_text)
    if names or local:
        body += ["# Names", "", "```names", *[f"{n} = {t}" for n, t in names],
                 *[f"{s}!{n} = {t}" for s, n, t in local], "```", ""]
    if opts.dropped_tables:
        warnings.warn(f"data-table formulas are not supported; wrote their cached values as typed values: "
                      f"{', '.join(opts.dropped_tables)}", stacklevel=2)
    head = ["---", f"cellprose: {VERSION}"]
    if opts.elided:
        head.append("profile: compact")
    if opts.source:
        head.append(f"source: {opts.source}")
    notes = []
    if missing_values:
        notes.append("? = formula with no cached value; open and save in Excel or LibreOffice to compute")
    if opts.dropped_tables:
        notes.append("data-table formulas are not supported; their cached values are written as typed values")
    if any(dropped.values()):
        notes.append("not carried: " + ", ".join(
            f"{n} {name if n != 1 else name[:-1]}" for name, n in dropped.items() if n))
    if notes:
        head.append(f"note: '{'; '.join(notes)}'")
    head += ["---", ""]
    if opts.legend and table_starts:
        head += [LEGEND_A if table_starts == {1} else LEGEND_OTHER, ""]
    return "\n".join(head + body).rstrip() + "\n"


DROPPED = ("charts", "images", "pivot tables", "conditional formats", "hyperlinks")   # order of the note (SPEC §3)


def count_dropped(ws) -> dict[str, int]:
    """How many of each feature the format does not carry sit on this sheet (SPEC §12)."""
    return {"charts": len(getattr(ws, "_charts", ())), "images": len(getattr(ws, "_images", ())),
            "pivot tables": len(getattr(ws, "_pivots", ())),
            "conditional formats": sum(len(cf.rules) for cf in ws.conditional_formatting),
            "hyperlinks": sum(1 for row in ws.iter_rows() for c in row if c.hyperlink is not None)}


def validation_lines(ws) -> list[str]:
    """`RANGE = type[ operator]: formula1[ ; formula2]`, one line per range, sorted as text (SPEC §8)."""
    out = []
    for dv in ws.data_validations.dataValidation:
        if dv.type in (None, "none", "any") or dv.formula1 is None:
            continue
        kind = dv.type + (f" {dv.operator}" if dv.operator else "")
        rule = f"{kind}: {dv.formula1}" + (f" ; {dv.formula2}" if dv.formula2 is not None else "")
        out += [f"{rng} = {rule}" for rng in str(dv.sqref).split()]
    return sorted(out)


def _empty_string_results(path: str) -> set[tuple[str, str]]:
    """(sheet title, A1 address) of formula cells whose cached result is the empty string.

    openpyxl reads such a cached value (`t="str"` with an empty `<v>`) as None, the same as a formula that was never
    calculated, so they are found in the sheet XML."""
    import zipfile
    try:
        from defusedxml import DefusedXmlException
        from defusedxml import ElementTree as ET
    except ImportError:         # the vendored skill copy needs only openpyxl
        from xml.etree import ElementTree as ET
        DefusedXmlException = ET.ParseError
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
          "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
    found: set[tuple[str, str]] = set()
    try:
        with zipfile.ZipFile(path) as z:
            wb = ET.fromstring(z.read("xl/workbook.xml"))
            rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
            for sh in wb.findall("m:sheets/m:sheet", ns):
                target = rels.get(sh.get("{%s}id" % ns["r"]), "")
                part = target.lstrip("/") if target.startswith("/") else "xl/" + target
                if part not in z.namelist():
                    continue
                for c in ET.fromstring(z.read(part)).iter("{%s}c" % ns["m"]):
                    if c.get("t") != "str" or c.find("m:f", ns) is None:
                        continue
                    v = c.find("m:v", ns)
                    if v is None or not (v.text or ""):
                        found.add((sh.get("name"), c.get("r")))
    except (KeyError, ET.ParseError, zipfile.BadZipFile, DefusedXmlException):
        pass
    return found


MAX_UNZIPPED = 512 * 1024 * 1024      # total bytes an .xlsx may expand to
MAX_RATIO = 1000                       # per-part expansion (a spreadsheet part compresses ~10-50x)


def check_zip(path: str | Path) -> None:
    """Refuse a zip bomb before openpyxl inflates it. Raises ValueError (the MCP server shows it to the model)."""
    import zipfile
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
    except zipfile.BadZipFile:
        return                          # not a zip: openpyxl reports it
    total = sum(i.file_size for i in infos)
    if total > MAX_UNZIPPED:
        raise ValueError(f"{Path(path).name} expands to {total // 2**20} MB, over the {MAX_UNZIPPED // 2**20} MB limit")
    for i in infos:
        if i.file_size > 1_000_000 and i.file_size > MAX_RATIO * max(i.compress_size, 1):
            raise ValueError(f"{Path(path).name}: part {i.filename} expands more than {MAX_RATIO}x; refusing to read it")


def load_pair(path: str | Path):
    check_zip(path)
    path = str(path)
    fwb, vwb = openpyxl.load_workbook(path), openpyxl.load_workbook(path, data_only=True)
    vwb._cellprose_empty = _empty_string_results(path)  # formulas that calculated to "" (read as None by openpyxl)
    return fwb, vwb


def _is_empty_result(vwb, ws, coord: str) -> bool:
    """True when the formula at `coord` calculated to the empty string."""
    return vwb[ws.title][coord].value == "" or (ws.title, coord) in getattr(vwb, "_cellprose_empty", ())


def needs_recalc(path: str | Path) -> bool:
    """True when some formula cell has no cached value (typical for files written by code, not Excel)."""
    fwb, vwb = load_pair(path)
    for ws in fwb.worksheets:
        vws = vwb[ws.title]
        for row in ws.iter_rows():
            for c in row:
                if is_formula_cell(c) and vws[c.coordinate].value is None and not _is_empty_result(vwb, ws, c.coordinate):
                    return True
    return False


def restore_external(fwb, vwb, original) -> None:
    """After a LibreOffice pass, put back what `original` holds for formulas that refer to another workbook: the
    formula text as written (LibreOffice changes its case and spelling) and the cached result (it computes #NAME?)."""
    from .reader import EXTERNAL
    ofwb, ovwb = load_pair(original)
    for ows in ofwb.worksheets:
        if ows.title not in fwb.sheetnames:
            continue
        for row in ows.iter_rows():
            for oc in row:
                if is_formula_cell(oc) and EXTERNAL.search(oc.value):
                    fwb[ows.title][oc.coordinate].value = oc.value
                    v = ovwb[ows.title][oc.coordinate].value
                    if v is not None:
                        vwb[ows.title][oc.coordinate].value = v
