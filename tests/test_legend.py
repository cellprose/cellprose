"""SPEC 3.1: the row-number legend after the front matter."""
import openpyxl

import cellprose
from cellprose.writer import LEGEND_A, LEGEND_OTHER


def book(tmp_path, cells, name="b.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    for ref, v in cells.items():
        ws[ref] = v
    p = tmp_path / name
    wb.save(p)
    return p


def test_legend_for_tables_starting_at_a(tmp_path):
    text = cellprose.dumps(book(tmp_path, {"A1": "x", "B1": 1}))
    head, _, rest = text.partition("---\n\n")
    assert rest.startswith(LEGEND_A + "\n\n# Sheet: ")


def test_other_legend_when_a_table_starts_elsewhere(tmp_path):
    text = cellprose.dumps(book(tmp_path, {"C3": "x", "D3": 1}))
    assert LEGEND_OTHER in text and LEGEND_A not in text
    assert "## C3:D3" in text


def test_no_legend_without_a_table_or_when_switched_off(tmp_path):
    assert "Note: the first field" not in cellprose.dumps(book(tmp_path, {}, "e.xlsx"))
    assert "Note: the first field" not in cellprose.dumps(book(tmp_path, {"A1": 1}, "o.xlsx"), legend=False)


def test_reader_ignores_the_legend_silently(tmp_path):
    text = cellprose.dumps(book(tmp_path, {"A1": "x", "B1": 1}))
    wb = cellprose.load(text)
    assert wb.warnings == []
    assert cellprose.load(text.replace(LEGEND_A + "\n\n", "")).sheets[0].cells == wb.sheets[0].cells
