"""Cellprose: a plain-text format for spreadsheet workbooks, with formulas and cell addresses, that GitHub renders."""
from __future__ import annotations

from pathlib import Path

from .reader import CompactProfileError, ParseError, Workbook, load, load_file
from .writer import VERSION, Options, dumps_workbook, load_pair, needs_recalc, restore_external

__all__ = ["dumps", "load", "load_file", "Workbook", "ParseError", "CompactProfileError", "VERSION", "Options"]
__version__ = "0.3.1"


def dumps(path: str | Path, *, sheets: list[str] | None = None, cell_range: str | None = None,
          max_rows: int | None = None, recalc: str = "auto", legend: bool = True) -> str:
    """Return a workbook (.xlsx/.xlsm) as Cellprose text.

    recalc: "auto" recalculates with LibreOffice only when formulas lack cached values and LibreOffice is
    installed; "always" forces it; "never" leaves missing values as `?`.
    legend: write the row-number legend after the front matter (SPEC 3.1); False gives the v0.3.0 text.
    """
    path = Path(path)
    src = path
    if recalc == "always" or (recalc == "auto" and needs_recalc(path)):
        from .recalc import recalc_copy, soffice
        if recalc == "always" or soffice():
            src = recalc_copy(path)
    fwb, vwb = load_pair(src)
    if src != path:
        restore_external(fwb, vwb, path)
    return dumps_workbook(fwb, vwb, Options(sheets=sheets, cell_range=cell_range, max_rows=max_rows,
                                            source=path.name, legend=legend))
