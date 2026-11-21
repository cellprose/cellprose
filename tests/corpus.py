"""Edge-case workbooks for the round-trip tests, built in code so the corpus needs no binary fixtures."""
import datetime as dt

import openpyxl
from openpyxl.workbook.defined_name import DefinedName

ERRORS = ["#DIV/0!", "#N/A", "#REF!", "#VALUE!"]
LOOKALIKES = ["00123", "TRUE", "?", "2026-10-07 plan", "=not a formula", "'quoted", "#REF! was here", "12:30:00",
              "1e5", "a|b", "back\\slash\\", "pipe at end|", "<br>", "line1\nline2", " padded ", '"hello"', "x…y"]


def edge_workbook(path):
    """Every feature the writer emits: regions, fills, formats, merges, loose cells, meta, names."""
    wb = openpyxl.Workbook()
    a = wb.active
    a.title = "Assumptions"
    a["A1"], a["B1"] = "Driver", "Value"
    a["A2"], a["B2"] = "Growth", 0.12
    a["A3"], a["B3"] = "Price", 45
    a["A4"], a["B4"] = "Start", dt.datetime(2026, 1, 31)
    a["A5"], a["B5"] = "Stamp", dt.datetime(2026, 10, 7, 14, 30, 5)
    a["B2"].number_format = "0%"
    a["B4"].number_format = "yyyy-mm-dd"
    a["B5"].number_format = "yyyy-mm-dd hh:mm:ss"
    a["A7"] = "Flag"
    a["B7"] = True

    p = wb.create_sheet("P&L")
    p.append([None, "Q1", "Q2", "Q3", "Q4", "Total"])
    p.append(["Units", 1200] + [f"=B2*(1+Growth)" if False else None] * 3)
    for col, prev in zip("CDE", "BCD"):
        p[f"{col}2"] = f"={prev}2*(1+Growth)"
    p["F2"] = "=SUM(B2:E2)"
    p.append(["Price", "=Assumptions!$B$3", "=Assumptions!$B$3", "=Assumptions!$B$3", 51.5])   # typed-in override in E3
    p.append(["Revenue"] + [f"={c}2*{c}3" for c in "BCDE"] + ["=SUM(B4:E4)"])
    for c in "BCDEF":
        p[f"{c}4"].number_format = "$#,##0"
    p["A6"] = "Margin"
    p["B6"] = "=IF(B4>0,B4/B2,0)"
    p["B6"].number_format = "0.0%"
    p.freeze_panes = "B2"

    t = wb.create_sheet("Q1 #2")                      # name with a space and '#'
    t["A1"], t["B1"], t["C1"] = "Title spanning", None, None
    t.merge_cells("A1:C1")
    t["A3"], t["B3"] = "Look-alikes", "Value"
    for i, v in enumerate(LOOKALIKES, start=4):
        t.cell(row=i, column=1).value = v
        t.cell(row=i, column=1).data_type = "s"
        t.cell(row=i, column=2).value = i
    r = 4 + len(LOOKALIKES) + 1
    for i, e in enumerate(ERRORS):
        t.cell(row=r + i, column=1).value = e           # error constants
        t.cell(row=r + i, column=2).value = i
    t["H20"] = "loose note"                              # single cells away from every region
    t["J22"] = "=Assumptions!B3*2"
    t["K24"] = dt.datetime(2026, 12, 25)

    h = wb.create_sheet("Hidden")
    h["A1"], h["B1"] = "secret", 1
    h.sheet_state = "hidden"
    wb.defined_names["Growth"] = DefinedName("Growth", attr_text="Assumptions!$B$2")
    wb.defined_names["Price"] = DefinedName("Price", attr_text="Assumptions!$B$3")
    p.defined_names["LocalTax"] = DefinedName("LocalTax", attr_text="'P&L'!$B$6")
    wb.save(path)
    return path


def content(path):
    """Everything a round trip must keep, read straight from an .xlsx: per-sheet cells (formulas as text, typed
    values, number formats for cells inside regions), merges, state, freeze panes, and names."""
    from cellprose.writer import detect_regions, is_formula_cell
    wb = openpyxl.load_workbook(path)
    out = {"names": sorted((n, d.attr_text) for n, d in wb.defined_names.items() if d.attr_text), "sheets": {}}
    for ws in wb.worksheets:
        regions, _ = detect_regions(ws)
        in_region = lambda r, c: any(r1 <= r <= r2 and c1 <= c <= c2 for r1, c1, r2, c2 in regions)  # noqa: E731
        cells = {}
        for row in ws.iter_rows():
            for c in row:
                if c.value is None or c.value == "":      # empty text is an empty cell
                    continue
                v = c.value
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    v = float(v)
                fmt = c.number_format if in_region(c.row, c.column) else None
                cells[c.coordinate] = (("formula" if is_formula_cell(c) else "s" if c.data_type == "f" else c.data_type), v, fmt)  # lone "=": text
        out["sheets"][ws.title] = {
            "cells": cells, "merges": sorted(str(m) for m in ws.merged_cells.ranges), "state": ws.sheet_state,
            "freeze": ws.freeze_panes, "names": sorted((n, d.attr_text) for n, d in ws.defined_names.items() if d.attr_text)}
    return out
