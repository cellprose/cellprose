"""The agent tool kit (src/cellprose/tools.py, experiments/E33)."""
import openpyxl
import pytest

from cellprose import tools


@pytest.fixture
def book(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Model"
    ws.append(["Item", "Q1", "Q2"])
    for i in range(2, 21):
        ws.append([f"Line {i}", i, f"=B{i}*2"])
    ws["A22"], ws["B22"] = "Total", "=SUM(B2:B20)"
    p = tmp_path / "b.xlsx"
    wb.save(p)
    from cellprose.recalc import recalc_copy, soffice
    return recalc_copy(p) if soffice() else p


def test_outline_indexes_long_regions_and_elides_rows(book):
    o = tools.outline(book)
    assert "```index" in o and "Model!A1:C20 rows=20" in o
    assert "```elided" in o and "10|" not in o            # middle rows left out
    assert "C2:C20 = B2*2" in o                           # formulas still cover every row


def test_read_range_returns_only_that_rectangle(book):
    t = tools.read_range(book, "Model!A10:C11")
    assert "## A10:C11" in t and "10|Line 10|10" in t and "12|" not in t and "---" not in t


def test_find_shows_the_row_a_label_names(book):
    assert tools.find(book, "line 7").startswith("Model!A7: Line 7 -> B7: 7")
    assert tools.find(book, "nothing here") == "no cell contains 'nothing here'"


def test_trace_precedents_and_dependents(book):
    t = tools.trace(book, "Model!B22")
    assert "19 direct precedents" in t and t.index("Model!B2:") < t.index("Model!B10:")
    d = tools.trace(book, "Model!B5", dependents=True)
    assert "2 direct dependents" in d and "Model!C5" in d and "Model!B22" in d


def test_index_lists_regions_without_values(book):
    t = tools.index(book)
    assert "Model: used A1:C22" in t and "A1:C20 rows=20 formulas=19 | Item|Q1|Q2" in t
    assert "Line 7" not in t and "read_range" in t


def test_compact_trace_merges_ranges_and_read_ranges_drops_formats(book):
    t = tools.trace(book, "Model!B22", compact=True)
    assert t.endswith("19 direct precedents: Model!B2:B20")
    r = tools.read_ranges(book, ["Model!A2:B3", "Model!A5"])
    assert r.count("## ") == 2 and "```formats" not in r


def test_whatif_lists_cells_whose_value_changes(book):
    from cellprose.recalc import soffice
    if not soffice():
        pytest.skip("LibreOffice not installed")
    t = tools.whatif(book, "Model!B5", factor=1.1)
    assert "2 other cells change value: Model!C5, Model!B22" in t


def test_dependents_index_follows_the_workbook_not_a_reused_id(tmp_path):
    import os
    p = tmp_path / "w.xlsx"
    for i, formula in enumerate(("=A1*2", "=A2*2")):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws["A1"], ws["A2"], ws["B1"] = 1, 2, formula
        wb.save(p)
        os.utime(p, (1_000_000 + i, 1_000_000 + i))      # a new mtime, so the file is loaded again
        out = tools.trace(str(p), "A1", dependents=True)
        assert ("B1" in out) == (i == 0)


def test_trace_names_a_range_too_large_to_list_and_finds_its_readers(tmp_path):
    import openpyxl
    from cellprose import tools
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "D"
    for i in range(1, tools.MAX_EXPAND + 2):
        ws.cell(i, 1, i)
    ws["C1"] = f"=SUM(A1:A{tools.MAX_EXPAND + 1})"
    p = tmp_path / "big.xlsx"
    wb.save(p)
    assert f"D!A1:A{tools.MAX_EXPAND + 1}" in tools.trace(p, "D!C1", compact=True)
    assert "D!C1" in tools.trace(p, "D!A5", dependents=True, compact=True)


def test_tools_accept_the_sheet_spelling_they_print(tmp_path):
    import openpyxl
    from cellprose import tools
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Q1 #2"
    ws["A1"], ws["B1"] = 1, "=A1*2"
    p = tmp_path / "h.xlsx"
    wb.save(p)
    assert 'Q1 #2' in tools.trace(p, '"Q1 #2"!B1')
    assert '"Q1 #2"!B1' in tools.trace(p, '"Q1 #2"!A1', dependents=True)
    assert "B1" in tools.read_range(p, '"Q1 #2"!A1:B1')
