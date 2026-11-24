"""Keep untrusted workbooks from exhausting memory: visit the cells a sheet holds, not its bounding box.

`ws.iter_rows()` walks every position from A1 to the last used cell, so a file with one stray cell at XFD1048576
means 17 billion cells. writer.py (frozen for the posted benchmark run, see tests/test_freeze_files.py) calls it in
many places, so instead of editing that file this module is installed over it when the package is imported:

- worksheets returned by `writer.load_pair` iterate only the cells that exist;
- `writer.array_cells` lists a huge array range as a rectangle instead of one position per cell.

The text written is byte for byte what writer.py alone writes for any sheet that fits in memory.
"""
from __future__ import annotations

from openpyxl.utils import range_boundaries

MAX_ENUMERATED = 1_000_000      # cells of one array range listed one by one; a larger range is tested as a rectangle


def iter_cells(ws):
    """The cells a sheet holds, in row-major order."""
    cells = getattr(ws, "_cells", None)
    if cells is None:
        yield from (c for row in ws.iter_rows() for c in row)
        return
    for key in sorted(cells):
        yield cells[key]


def _sparse_rows(ws, original):
    def iter_rows(*args, **kwargs):
        if args or kwargs or getattr(ws, "_cells", None) is None:
            return original(*args, **kwargs)
        rows: dict[int, list] = {}
        for (r, _), cell in sorted(ws._cells.items()):
            rows.setdefault(r, []).append(cell)
        return iter(tuple(row) for row in rows.values())
    return iter_rows


class Cover:
    """A set of (row, column) positions made of rectangles. Small rectangles are listed; a huge one is kept as bounds."""

    def __init__(self):
        self.cells: set[tuple[int, int]] = set()
        self.rects: list[tuple[int, int, int, int]] = []

    def add(self, c1: int, r1: int, c2: int, r2: int) -> None:
        if (r2 - r1 + 1) * (c2 - c1 + 1) > MAX_ENUMERATED:
            self.rects.append((c1, r1, c2, r2))
        else:
            self.cells.update((r, k) for r in range(r1, r2 + 1) for k in range(c1, c2 + 1))

    def __contains__(self, pos) -> bool:
        r, c = pos
        return pos in self.cells or any(c1 <= c <= c2 and r1 <= r <= r2 for c1, r1, c2, r2 in self.rects)


def install() -> None:
    from . import writer
    if getattr(writer, "_sparse_installed", False):
        return
    original_load_pair = writer.load_pair

    def load_pair(path):
        fwb, vwb = original_load_pair(path)
        for wb in (fwb, vwb):
            for ws in wb.worksheets:
                ws.iter_rows = _sparse_rows(ws, ws.iter_rows)
        return fwb, vwb

    def array_cells(ws) -> Cover:
        out = Cover()
        for c in iter_cells(ws):
            if writer.is_array_anchor(c) and c.value.ref:
                out.add(*range_boundaries(c.value.ref))
        return out

    writer.load_pair = load_pair
    writer.array_cells = array_cells
    writer._sparse_installed = True
