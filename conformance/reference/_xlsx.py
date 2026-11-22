"""Reference-implementation glue (Python + openpyxl): the kit's JSON workbook <-> the cellprose package.

This file is NOT part of the kit's contract. It only lets the Python reference implementation be driven through the
same command-line interface that any other implementation must offer (see ../README.md).
"""
import datetime as dt

from openpyxl import Workbook
from openpyxl.chart import BarChart
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import coordinate_to_tuple
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.formula import ArrayFormula

ERROR_TYPES = {"error"}


def value_of(cell):
    """The Python value for a kit cell's `v`/`t` pair."""
    v, t = cell.get("v"), cell.get("t")
    if t == "date":
        return dt.datetime.fromisoformat(v)
    if t == "datetime":
        return dt.datetime.fromisoformat(v)
    if t == "time":
        return dt.time.fromisoformat(v)
    return v


def build_pair(doc):
    """(formulas workbook, cached-values workbook) as the writer expects them."""
    fwb, vwb = Workbook(), Workbook()
    for wb in (fwb, vwb):
        wb.remove(wb.active)
    for sh in doc["sheets"]:
        fws, vws = fwb.create_sheet(sh["name"]), vwb.create_sheet(sh["name"])
        for addr, cell in sh.get("cells", {}).items():
            r, c = coordinate_to_tuple(addr)
            fx, vx = fws.cell(row=r, column=c), vws.cell(row=r, column=c)
            has_value = "v" in cell
            if "array" in cell:
                fx.value = ArrayFormula(cell["array"], "=" + cell["f"])
            elif "f" in cell:
                fx.value = "=" + cell["f"]
            elif has_value:
                fx.value = value_of(cell)
            if has_value:
                vx.value = value_of(cell)
            for x in (fx, vx):
                x.number_format = cell.get("fmt", "General")
                if cell.get("t") == "error" and (has_value or "f" not in cell):
                    x.data_type = "e"
                elif isinstance(x.value, str) and "f" not in cell and "array" not in cell:
                    x.data_type = "s"       # text that starts with "=" or looks like an error stays text
            if cell.get("t") == "error" and "f" in cell:
                fx.data_type = "f"
        for rng in sh.get("merges", []):
            fws.merge_cells(rng)
        for addr, text in sh.get("comments", {}).items():
            fws[addr].comment = Comment(text, "")
        for v in sh.get("validations", []):
            dv = DataValidation(type=v["type"], operator=v.get("operator"), formula1=v["formula1"], formula2=v.get("formula2"),
                                sqref=v["sqref"])
            fws.add_data_validation(dv)
        for kind, n in sh.get("dropped", {}).items():     # features the format does not carry, built so the writer can count them
            for i in range(n):
                if kind == "charts":
                    fws.add_chart(BarChart(), f"Z{1 + 20 * i}")
                elif kind == "conditional formats":
                    fws.conditional_formatting.add(f"Y{1 + i}", CellIsRule(operator="greaterThan", formula=["0"]))
                elif kind == "hyperlinks":
                    fws[f"X{1 + i}"].hyperlink = "https://example.com"
                    fws[f"X{1 + i}"].value = None         # (setting a hyperlink also sets the cell's text)
                else:
                    raise ValueError(f"cannot build {kind!r}")
        if sh.get("freeze"):
            fws.freeze_panes = sh["freeze"]
        fws.sheet_state = sh.get("state", "visible")
        for n, text in sh.get("names", {}).items():
            fws.defined_names[n] = DefinedName(n, attr_text=text)
    for n, text in doc.get("names", {}).items():
        fwb.defined_names[n] = DefinedName(n, attr_text=text)
    return fwb, vwb


def decoded_json(wb):
    """The kit's decoded form of a cellprose.reader.Workbook."""
    from openpyxl.utils import get_column_letter as L
    sheets = []
    for sh in wb.sheets:
        cells = {}
        for (r, c), cell in sorted(sh.cells.items()):
            out = {}
            if cell.formula is not None:
                out["f"] = cell.formula
                if cell.array_ref:
                    out["array"] = cell.array_ref
            elif cell.value is None:
                continue
            else:
                v = cell.value
                if cell.error:
                    out["t"], out["v"] = "error", v
                elif isinstance(v, dt.datetime):
                    midnight = v.time() == dt.time(0)
                    out["t"], out["v"] = ("date", v.date().isoformat()) if midnight else \
                        ("datetime", v.isoformat(timespec="seconds"))
                elif isinstance(v, dt.time):
                    out["t"], out["v"] = "time", v.isoformat()
                else:
                    out["v"] = v
            if cell.number_format != "General":
                out["fmt"] = cell.number_format
            cells[f"{L(c)}{r}"] = out
        entry = {"name": sh.name, "state": sh.state, "freeze": sh.freeze, "merges": sorted(sh.merges),
                 "names": dict(sorted(sh.names.items())), "cells": cells}
        if sh.comments:
            entry["comments"] = {f"{L(c)}{r}": t for (r, c), t in sorted(sh.comments.items())}
        if sh.validations:
            entry["validations"] = [{k: v for k, v in zip(("sqref", "type", "operator", "formula1", "formula2"), row)
                                     if v is not None} for row in sh.validations]
        sheets.append(entry)
    return {"sheets": sheets, "names": dict(sorted(wb.names.items()))}
