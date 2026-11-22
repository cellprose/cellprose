"""Read Cellprose v0.2 and v0.3 text back into a workbook (the inverse of writer.py).

    wb = cellprose.load(text)         # parse; raises ParseError with a line number
    wb.to_xlsx("book.xlsx")           # values, formulas, number formats, merges, names, sheet state

Formula results in the grid are display values and are ignored: formulas are rewritten from the
`formulas` blocks (fill ranges are expanded by shifting relative references, as Excel does), and a
spreadsheet app recomputes them. Typed-in values are read back exactly. Compact-profile files drop rows
and cannot be turned back into a workbook (`CompactProfileError`).
"""
from __future__ import annotations

import datetime as dt
import math
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl.formula.translate import Translator
from openpyxl.utils import column_index_from_string, range_boundaries
from openpyxl.utils import get_column_letter as L

LEGEND_PREFIX = "Note: the first field of each table row is its row number, not a cell;"
SUPPORTED = ("0.2", "0.3")     # 0.2 grids have outer pipes on every row, 0.3 grids have none
NUMBER = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")
DATETIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}):(\d{2}))?$")
TIME = re.compile(r"^(\d{2}):(\d{2}):(\d{2})$")
ERROR = re.compile(r"^#[A-Z/0!?]+$")
RANGE = re.compile(r"^[A-Z]{1,3}[0-9]+(:[A-Z]{1,3}[0-9]+)?$")
EXTERNAL = re.compile(r"\[\d+\][^!]*!")   # a reference into another workbook: 'file'!A1 is stored as '[1]Sheet'!A1
MAX_RANGE_CELLS = 1_000_000     # largest range one block line may name
MAX_LINKS = 1000                # highest [n] external-link index written
MAX_CELLS = 5_000_000           # cells a whole file may define
ESCAPES = {"\\": "\\", "|": "|", "<": "<"}


class ParseError(ValueError):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(f"line {line}: {message}" if line else message)


class CompactProfileError(ParseError):
    """The file is a compact-profile excerpt; it omits data and cannot become a workbook."""


# ------------------------------------------------------------------ model
@contextmanager
def _exact_floats():
    """openpyxl writes numbers with "%.16g", which cuts 17-digit floats (53.779999999999994 -> 53.77999999999999).
    Use repr, the shortest string that reads back as the same float, while a workbook is saved."""
    import openpyxl.cell._writer as cell_writer
    original = cell_writer.safe_string

    def safe_string(value):
        if isinstance(value, float) and math.isfinite(value):
            return repr(value)
        return original(value)

    cell_writer.safe_string = safe_string
    try:
        yield
    finally:
        cell_writer.safe_string = original


def _patch_external(path: Path, cells: dict[int, dict[str, tuple[str, object, bool]]]) -> None:
    """Make formulas that refer to another workbook open cleanly, and keep what they showed.

    The link behind `[1]` is not part of the format, and a spreadsheet app cannot recompute these formulas: it would
    show #NAME?, and Excel would report a damaged file for a `[1]` with no link part. So, in the saved .xlsx,
    - each such cell is rewritten as its formula (exactly as in the file) plus the result shown in the grid, as the
      cached value, and
    - an `externalLink` part is added for every `[n]` used, pointing at a placeholder file name (Excel offers to
      update links, as it does for any workbook with them).
    `cells` is {sheet number: {A1 address: (formula, shown, is_error)}}."""
    import zipfile
    from xml.sax.saxutils import escape
    from openpyxl.utils.datetime import to_excel

    def cached(v, error: bool) -> tuple[str, str] | None:
        if v is None:
            return None
        if error:
            return "e", escape(str(v))
        if isinstance(v, bool):
            return "b", "1" if v else "0"
        if isinstance(v, (int, float)):
            return "", repr(v)
        if isinstance(v, (dt.datetime, dt.time)):
            return "", repr(to_excel(v))
        return "str", escape(str(v))

    links: dict[int, set[str]] = {}
    for per_sheet in cells.values():
        for formula, _, _ in per_sheet.values():
            for m in re.finditer(r"\[(\d+)\]([^!]*)!", formula):
                links.setdefault(int(m.group(1)), set()).add(m.group(2).strip("'"))
    if any(n > MAX_LINKS for n in links):
        raise ValueError(f"external link index above {MAX_LINKS}")
    top = max(links, default=0)
    main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    attr = {'"': "&quot;"}

    def patch_sheet(xml: str, per_sheet: dict) -> str:
        def put(m):
            addr = m.group(1)
            if addr not in per_sheet:
                return m.group(0)
            formula, shown, err = per_sheet[addr]
            style = re.search(r'\bs="(\d+)"', m.group(2))
            hit = cached(shown, err)
            t = f' t="{hit[0]}"' if hit and hit[0] else ""
            v = f"<v>{hit[1]}</v>" if hit else ""
            s = f' s="{style.group(1)}"' if style else ""
            return f'<c r="{addr}"{s}{t}><f>{escape(formula)}</f>{v}</c>'
        return re.sub(r'<c r="([A-Z]+\d+)"([^>]*?)(?:/>|>.*?</c>)', put, xml, flags=re.S)

    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            m = re.fullmatch(r"xl/worksheets/sheet(\d+)\.xml", item.filename)
            if m and int(m.group(1)) in cells:
                data = patch_sheet(data.decode("utf-8"), cells[int(m.group(1))]).encode("utf-8")
            elif top and item.filename == "xl/workbook.xml":
                refs = "".join(f'<externalReference xmlns:r="{rel}" r:id="rIdExt{n}"/>' for n in range(1, top + 1))
                data = data.decode("utf-8").replace("</sheets>", f"</sheets><externalReferences>{refs}</externalReferences>", 1).encode("utf-8")
            elif top and item.filename == "xl/_rels/workbook.xml.rels":
                rels = "".join(f'<Relationship Id="rIdExt{n}" Type="{rel}/externalLink" Target="externalLinks/externalLink{n}.xml"/>'
                               for n in range(1, top + 1))
                data = data.decode("utf-8").replace("</Relationships>", rels + "</Relationships>", 1).encode("utf-8")
            elif top and item.filename == "[Content_Types].xml":
                over = "".join(f'<Override PartName="/xl/externalLinks/externalLink{n}.xml" ContentType="application/'
                               f'vnd.openxmlformats-officedocument.spreadsheetml.externalLink+xml"/>' for n in range(1, top + 1))
                data = data.decode("utf-8").replace("</Types>", over + "</Types>", 1).encode("utf-8")
            zout.writestr(item, data)
        for n in range(1, top + 1):
            names = "".join(f'<sheetName val="{escape(x, attr)}"/>' for x in sorted(links.get(n, ()))) or '<sheetName val="Sheet1"/>'
            zout.writestr(f"xl/externalLinks/externalLink{n}.xml",
                          f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<externalLink xmlns="{main}">'
                          f'<externalBook xmlns:r="{rel}" r:id="rId1"><sheetNames>{names}</sheetNames></externalBook></externalLink>')
            zout.writestr(f"xl/externalLinks/_rels/externalLink{n}.xml.rels",
                          f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/'
                          f'package/2006/relationships"><Relationship Id="rId1" Type="{rel}/externalLinkPath" '
                          f'Target="external-{n}.xlsx" TargetMode="External"/></Relationships>')
    tmp.replace(path)


@dataclass
class Cell:
    value: object = None            # typed value (None for formula cells)
    formula: str | None = None      # without the leading "="
    number_format: str = "General"
    error: bool = False             # value is an Excel error literal, not text
    array_ref: str | None = None    # set on the anchor of an array formula: the range it fills
    shown: object = None            # a formula cell's displayed result (used for external-link formulas only)
    shown_error: bool = False


@dataclass
class Sheet:
    name: str
    state: str = "visible"
    freeze: str | None = None
    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)
    merges: list[str] = field(default_factory=list)
    names: dict[str, str] = field(default_factory=dict)
    comments: dict[tuple[int, int], str] = field(default_factory=dict)
    validations: list[tuple[str, str, str | None, str, str | None]] = field(default_factory=list)  # range, type, operator, f1, f2


@dataclass
class Workbook:
    sheets: list[Sheet] = field(default_factory=list)
    names: dict[str, str] = field(default_factory=dict)
    meta: dict[str, str] = field(default_factory=dict)      # front matter
    warnings: list[str] = field(default_factory=list)

    def sheet(self, name: str) -> Sheet:
        return next(s for s in self.sheets if s.name == name)

    def to_openpyxl(self):
        from openpyxl import Workbook as XlWorkbook
        from openpyxl.comments import Comment
        from openpyxl.worksheet.formula import ArrayFormula
        from openpyxl.worksheet.datavalidation import DataValidation
        from openpyxl.workbook.defined_name import DefinedName

        wb = XlWorkbook()
        wb.remove(wb.active)
        for sh in self.sheets:
            ws = wb.create_sheet(sh.name)
            for (r, c), cell in sorted(sh.cells.items()):
                x = ws.cell(row=r, column=c)
                if cell.array_ref:
                    x.value = ArrayFormula(cell.array_ref, "=" + cell.formula)
                elif cell.formula is not None:
                    x.value = "=" + cell.formula
                else:
                    x.value = cell.value
                    if isinstance(cell.value, str) and not cell.error:
                        x.data_type = "s"       # keep "=x" and "#N/A" text as text, not formula or error
                # a date typed in must not pick up openpyxl's default date format unless the file lists one
                x.number_format = cell.number_format
            for rng in sh.merges:
                ws.merge_cells(rng)
            for (r, c), text in sorted(sh.comments.items()):
                ws.cell(row=r, column=c).comment = Comment(text, "")
            for rng, kind, op, f1, f2 in sh.validations:
                ws.add_data_validation(DataValidation(type=kind, operator=op, formula1=f1, formula2=f2, sqref=rng,
                                                      showErrorMessage=True))
            if sh.freeze:
                ws.freeze_panes = sh.freeze
            ws.sheet_state = sh.state
            for n, text in sh.names.items():
                ws.defined_names[n] = DefinedName(n, attr_text=text)
        for n, text in self.names.items():
            wb.defined_names[n] = DefinedName(n, attr_text=text)
        return wb

    def _external_results(self) -> dict[int, dict[str, tuple[str, object, bool]]]:
        """{sheet number: {A1 address: (formula, shown result, is_error)}} for formulas that refer to another workbook."""
        out: dict[int, dict[str, tuple[str, object, bool]]] = {}
        for n, sh in enumerate(self.sheets, start=1):
            for (r, c), cell in sh.cells.items():
                if cell.formula is not None and EXTERNAL.search(cell.formula):
                    out.setdefault(n, {})[f"{L(c)}{r}"] = cell.formula, cell.shown, cell.shown_error
        return out

    def to_xlsx(self, path: str | Path, *, recalc: str = "never") -> Path:
        """Write an .xlsx. recalc="never" keeps exactly what was written (formulas have no cached values, so
        Excel computes them on open); "auto"/"always" pass the file through headless LibreOffice so values are
        cached, which also lets LibreOffice rewrite styles and formats."""
        path = Path(path)
        with _exact_floats():
            self.to_openpyxl().save(path)
        if recalc == "always" or (recalc == "auto" and any(
                c.formula is not None for s in self.sheets for c in s.cells.values())):
            from .recalc import recalc_copy, soffice
            if recalc == "always" or soffice():
                done = recalc_copy(path)
                path.write_bytes(done.read_bytes())
        external = self._external_results()
        if external:
            self.warnings.append("formulas that refer to another workbook keep their shown result as the cached "
                                 "value; the link itself is not carried")
            _patch_external(path, external)
        return path


# ------------------------------------------------------------------ values
def split_row(line: str, n: int) -> list[str]:
    """Split `|a|b|c|` on unescaped pipes. Escapes stay in the returned cells; see decode_cell."""
    if not line.startswith("|"):
        raise ParseError("table row must start with '|'", n)
    cells, cur, i = [], [], 1
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] in ESCAPES:
            cur.append(line[i:i + 2])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    if cur:
        raise ParseError("table row must end with '|'", n)
    return cells


def split_row_bare(line: str) -> list[str]:
    """Split a v0.3 row (`2|Units|1200`, no outer pipes) on unescaped pipes. A row ending in a pipe has an empty last cell."""
    cells, cur, i = [], [], 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] in ESCAPES:
            cur.append(line[i:i + 2])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur))
    return cells


def unescape(s: str) -> str:
    """Resolve backslash escapes (before a backslash, pipe or <) and turn the <br> token into a newline, in one pass."""
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] in ESCAPES:
            out.append(ESCAPES[s[i + 1]])
            i += 2
        elif s.startswith("<br>", i):
            out.append("\n")
            i += 4
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def decode_cell(raw: str) -> tuple[object, bool]:
    """Raw grid text -> (value, is_error). Inverse of writer.fmt_value for typed values."""
    if raw == "":
        return None, False
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':      # quoted: always text
        inner = unescape(raw[1:-1].replace('""', '"'))
        return (inner[1:] if inner.startswith("'") else inner), False
    if raw.startswith("'"):                                     # apostrophe: text that would read as another type
        return unescape(raw[1:]), False
    if raw in ("TRUE", "FALSE"):
        return raw == "TRUE", False
    if ERROR.match(raw):
        return raw, True
    if NUMBER.match(raw):
        return (float(raw) if any(k in raw for k in ".eE") else int(raw)), False
    m = DATETIME.match(raw)
    if m:
        y, mo, d, hh, mi, ss = m.groups()
        try:
            return dt.datetime(int(y), int(mo), int(d), int(hh or 0), int(mi or 0), int(ss or 0)), False
        except ValueError:
            pass
    m = TIME.match(raw)
    if m:
        try:
            return dt.time(*map(int, m.groups())), False
        except ValueError:
            pass
    return unescape(raw), False


# ------------------------------------------------------------------ parsing
def _cells_in(rng: str, n: int):
    try:
        c1, r1, c2, r2 = range_boundaries(rng)
    except Exception:
        raise ParseError(f"bad range {rng!r}", n) from None
    if None in (c1, r1, c2, r2):
        raise ParseError(f"bad range {rng!r}", n)
    if (r2 - r1 + 1) * (c2 - c1 + 1) > MAX_RANGE_CELLS:
        raise ParseError(f"range {rng!r} covers more than {MAX_RANGE_CELLS} cells", n)
    return [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def _anchor(rng: str) -> str:
    return rng.split(":")[0]


def _split_assign(line: str, n: int) -> tuple[str, str]:
    left, sep, right = line.partition(" = ")
    if not sep:
        raise ParseError(f"expected 'RANGE = ...', got {line!r}", n)
    return left.strip(), right


def _sheet_name(heading: str) -> str:
    name = heading
    if len(name) >= 2 and name[0] == '"' and name[-1] == '"' and "#" in name[1:-1]:
        name = name[1:-1]
    return name


def load(text: str) -> Workbook:
    """Parse Cellprose v0.3 text (or v0.2, which differs only in the grid and arrays) into a Workbook."""
    lines = text.split("\n")
    wb = Workbook()
    i = 0

    # front matter
    if not lines or lines[0].strip() != "---":
        raise ParseError("file must start with '---' front matter", 1)
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        k, sep, v = lines[i].partition(":")
        if sep:
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] == "'":
                v = v[1:-1]
            wb.meta[k.strip()] = v
        i += 1
    if i >= len(lines):
        raise ParseError("front matter is not closed", len(lines))
    i += 1
    version = wb.meta.get("cellprose") or wb.meta.get("sheetmark")      # `sheetmark:` is the key of files written before the rename
    if version not in SUPPORTED:
        raise ParseError(f"unsupported cellprose version {version!r}; this reader handles {', '.join(SUPPORTED)}", 2)
    bare = version != "0.2"
    if wb.meta.get("profile") == "compact":
        raise CompactProfileError("compact-profile files omit rows and cannot be converted back to a workbook", 2)

    sheet: Sheet | None = None
    region: tuple[int, int, int, int] | None = None
    pending_formulas: list[tuple[int, str]] = []
    while i < len(lines):
        line, n = lines[i], i + 1
        if not line.strip():
            i += 1
        elif line.startswith("# Sheet: "):
            sheet = Sheet(_sheet_name(line[len("# Sheet: "):]))
            wb.sheets.append(sheet)
            region = None
            i += 1
        elif line.strip() == "# Names":
            sheet, region = None, None
            i += 1
        elif line.startswith("## "):
            if sheet is None:
                raise ParseError("region heading outside a sheet", n)
            rng = line[3:].strip()
            if not RANGE.match(rng):
                raise ParseError(f"bad region heading {rng!r}", n)
            c1, r1, c2, r2 = range_boundaries(rng)
            region = (r1, c1, r2, c2)
            i += 1
        elif line.startswith("#|") if bare else line.startswith("|"):
            if sheet is None:
                raise ParseError("table outside a sheet", n)
            start = i
            while i < len(lines) and (lines[i].strip() if bare else lines[i].startswith("|")):
                i += 1
            _read_table(sheet, lines[start:i], start + 1, wb, bare)
        elif line.startswith("```"):
            kind = line[3:].strip()
            start = i + 1
            j = start
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            if j >= len(lines):
                raise ParseError(f"unclosed ```{kind} block", n)
            body = [(k + 1, lines[k]) for k in range(start, j)]
            _read_block(wb, sheet, kind, body, n)
            i = j + 1
        elif line.startswith(LEGEND_PREFIX):
            i += 1          # the row-number legend (SPEC §3.1): prose for the model, nothing to read
        else:
            wb.warnings.append(f"line {n}: ignored {line[:60]!r}")
            i += 1
    if sum(len(sh.cells) for sh in wb.sheets) > MAX_CELLS:
        raise ParseError(f"file defines more than {MAX_CELLS} cells")
    return wb


def load_file(path: str | Path) -> Workbook:
    return load(Path(path).read_text(encoding="utf-8"))


def _read_table(sheet: Sheet, rows: list[str], first_line: int, wb: Workbook, bare: bool = False) -> None:
    if len(rows) < 2:
        raise ParseError("table needs a header and a separator row", first_line)
    split = (lambda row, _n: split_row_bare(row)) if bare else split_row
    head = split(rows[0], first_line)
    if not head or head[0] != "#":
        raise ParseError("grid header must start with '#'", first_line)
    try:
        cols = [column_index_from_string(h) for h in head[1:]]
    except ValueError:
        raise ParseError(f"bad column letters in {rows[0]!r}", first_line) from None
    sep = split(rows[1], first_line + 1)
    if len(sep) != len(head) or not all(re.fullmatch(r"-+", s) for s in sep):
        raise ParseError("second table row must be the '|-|-|' separator", first_line + 1)
    for k, row in enumerate(rows[2:], start=first_line + 2):
        cells = split(row, k)
        if cells and cells[0] == "…":
            continue                       # elision marker: only appears in compact files, which are rejected
        if bare and len(cells) < len(head):
            cells += [""] * (len(head) - len(cells))     # trailing empty cells are left out of a v0.3 row
        if len(cells) != len(head):
            raise ParseError(f"expected {len(head)} cells, found {len(cells)}", k)
        try:
            r = int(cells[0])
        except ValueError:
            raise ParseError(f"row label {cells[0]!r} is not a number", k) from None
        for c, raw in zip(cols, cells[1:]):
            v, err = decode_cell(raw)
            if v is not None:
                sheet.cells[(r, c)] = Cell(value=v, error=err)


def _read_block(wb: Workbook, sheet: Sheet | None, kind: str, body, n: int) -> None:
    if kind == "names":
        for k, line in body:
            if not line.strip():
                continue
            left, right = _split_assign(line, k)
            if "!" in left:
                sh, name = left.rsplit("!", 1)
                try:
                    wb.sheet(sh).names[name] = right
                except StopIteration:
                    raise ParseError(f"name {left!r} refers to unknown sheet {sh!r}", k) from None
            else:
                wb.names[left] = right
        return
    if sheet is None:
        raise ParseError(f"```{kind} block outside a sheet", n)
    if kind == "meta":
        for k, line in body:
            key, sep, val = line.partition(":")
            if not sep:
                raise ParseError(f"bad meta line {line!r}", k)
            key, val = key.strip(), val.strip()
            if key == "hidden":
                sheet.state = "hidden" if val == "true" else val
            elif key == "freeze":
                sheet.freeze = val
    elif kind == "formulas":
        for k, line in body:
            if not line.strip():
                continue
            rng, formula = _split_assign(line, k)
            anchor = _anchor(rng)
            for (r, c) in _cells_in(rng, k):
                dest = f"{L(c)}{r}"
                f = formula if dest == anchor else Translator("=" + formula, origin=anchor).translate_formula(dest)[1:]
                cell = sheet.cells.setdefault((r, c), Cell())
                cell.shown, cell.shown_error = cell.value, cell.error
                cell.formula, cell.value = f, None
    elif kind == "formats":
        for k, line in body:
            if not line.strip():
                continue
            rng, fmt = _split_assign(line, k)
            for pos in _cells_in(rng, k):
                sheet.cells.setdefault(pos, Cell()).number_format = fmt
    elif kind == "cells":
        for k, line in body:
            if not line.strip():
                continue
            m = re.match(r"^([A-Z]{1,3}[0-9]+)(: | = )(.*)$", line)
            if not m:
                raise ParseError(f"bad cells line {line!r}", k)
            addr, sep, rest = m.groups()
            c, r = range_boundaries(addr)[:2]
            if sep == " = ":
                formula, hash_sep, _shown = rest.rpartition("  # ")      # trailing comment = cached display value
                f = formula if hash_sep else rest
                shown = _shown.strip() if hash_sep else ""
                v, err = (None, False) if shown in ("", "?") else ("", False) if shown == '""' else decode_cell(shown)
                sheet.cells[(r, c)] = Cell(formula=f, shown=v, shown_error=err)
            else:
                v, err = decode_cell(rest)
                # the cells block carries no number formats, so keep dates and times readable as dates
                fmt = ("hh:mm:ss" if isinstance(v, dt.time) else
                       "yyyy-mm-dd" if isinstance(v, dt.datetime) and v.time() == dt.time(0) else
                       "yyyy-mm-dd hh:mm:ss" if isinstance(v, dt.datetime) else "General")
                sheet.cells[(r, c)] = Cell(value=v, error=err, number_format=fmt)
    elif kind == "merges":
        sheet.merges += [line.strip() for _, line in body if line.strip()]
    elif kind == "arrays":
        for k, line in body:
            if not line.strip():
                continue
            rng, formula = _split_assign(line, k)
            anchor = sheet.cells.setdefault(_cells_in(rng, k)[0], Cell())
            anchor.shown, anchor.shown_error = anchor.value, anchor.error
            anchor.formula, anchor.value, anchor.array_ref = formula, None, rng
    elif kind == "comments":
        for k, line in body:
            if not line.strip():
                continue
            m = re.match(r"^([A-Z]{1,3}[0-9]+): (.*)$", line)
            if not m:
                raise ParseError(f"bad comments line {line!r}", k)
            c, r = range_boundaries(m.group(1))[:2]
            sheet.comments[(r, c)] = unescape(m.group(2))
    elif kind == "validation":
        for k, line in body:
            if not line.strip():
                continue
            rng, rule = _split_assign(line, k)
            head, sep, formulas = rule.partition(": ")
            kind_op = head.split(" ")
            if not sep or not RANGE.match(rng) or len(kind_op) > 2:
                raise ParseError(f"bad validation line {line!r}", k)
            f1, has2, f2 = formulas.partition(" ; ")
            sheet.validations.append((rng, kind_op[0], kind_op[1] if len(kind_op) == 2 else None, f1, f2 if has2 else None))
    elif kind == "elided":
        raise CompactProfileError("compact-profile files omit rows and cannot be converted back to a workbook", n)
    else:
        wb.warnings.append(f"line {n}: unknown block ```{kind}")
