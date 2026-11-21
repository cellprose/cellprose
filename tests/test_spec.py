"""Golden tests for docs/SPEC.md: every example in the spec is a fixture in tests/golden/spec/.

Three things are checked for each fixture:
  1. the example in SPEC.md is byte-for-byte the fixture (so the spec and the tests cannot drift);
  2. the reader accepts it (or rejects it, for the compact profile);
  3. the writer reproduces the fixture exactly from the workbook the reader builds (canonical form).
"""
import datetime as dt
import re
import warnings
from pathlib import Path

import openpyxl
import pytest

import cellprose
from cellprose.writer import Options, dumps_workbook

ROOT = Path(__file__).parent
SPEC = (ROOT.parent / "docs" / "SPEC.md").read_text(encoding="utf-8")
GOLDEN = ROOT / "golden" / "spec"
FILES = sorted(p.name for p in GOLDEN.glob("*.sheet.md"))
EXAMPLE = re.compile(r"<!-- golden: (\S+) -->\n````markdown\n(.*?)\n````\n", re.S)
NON_COMPACT = [f for f in FILES if "compact" not in f]


def read(name):
    return (GOLDEN / name).read_text(encoding="utf-8")


def values_only(text):
    """The same file without formulas, so the reader yields the cached values shown in the grid."""
    text = re.sub(r"```formulas\n.*?```\n\n?", "", text, flags=re.S)
    text = re.sub(r"```arrays\n.*?```\n\n?", "", text, flags=re.S)
    return re.sub(r"^([A-Z]+\d+) = .*  # (.*)$", r"\1: \2", text, flags=re.M)


# ---- the spec and the fixtures agree ---------------------------------------------------------------

def test_spec_examples_are_the_fixtures():
    examples = dict(EXAMPLE.findall(SPEC))
    assert sorted(examples) == FILES, "every fixture needs a '<!-- golden: NAME -->' example in SPEC.md, and vice versa"
    for name, body in examples.items():
        assert body + "\n" == read(name), f"SPEC.md example {name} differs from tests/golden/spec/{name}"


def test_spec_is_v03():
    assert SPEC.startswith("# Cellprose v0.3")
    assert "cellprose: 0.1" not in SPEC


# ---- reader and writer on every fixture ---------------------------------------------------------------

@pytest.mark.parametrize("name", NON_COMPACT)
def test_fixture_parses_without_warnings(name):
    assert cellprose.load(read(name)).warnings == []


@pytest.mark.parametrize("name", NON_COMPACT)
def test_fixture_is_canonical(name):
    text = read(name)
    fwb = cellprose.load(text).to_openpyxl()
    vwb = cellprose.load(values_only(text)).to_openpyxl()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert dumps_workbook(fwb, vwb) == text


def test_compact_fixture_is_written_by_the_writer_and_refused_by_the_reader():
    text = read("06_compact.sheet.md")
    with pytest.raises(cellprose.CompactProfileError):
        cellprose.load(text)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Log"
    ws.append(["Day", "Visits"])
    for i in range(1, 13):
        ws.append([f"D{i:02d}", i * 10])
    assert dumps_workbook(wb, wb, Options(max_rows=6)) == text


# ---- what the spec says each example means ----------------------------------------------------------

def test_fill_range_after_a_gap_is_formulas_including_its_anchor():
    """SPEC.md "Reading fill ranges": G2:H2 = F2*(1+$B$4) means G2 and H2 both hold formulas. F2 is typed in."""
    cells = cellprose.load(read("03_override_gap.sheet.md")).sheet("Forecast").cells
    assert cells[(2, 6)].formula is None and cells[(2, 6)].value == 117000            # F2: the typed-in override
    assert cells[(2, 7)].formula == "F2*(1+$B$4)"                                   # G2: anchor of the second range
    assert cells[(2, 8)].formula == "G2*(1+$B$4)"                                   # H2: shifted
    assert [cells[(2, c)].formula for c in (3, 4, 5)] == ["B2*(1+$B$4)", "C2*(1+$B$4)", "D2*(1+$B$4)"]
    assert cells[(2, 2)].formula is None                                            # B2 typed in


def test_value_examples_decode_to_the_types_the_spec_lists():
    cells = cellprose.load(read("04_values.sheet.md")).sheet("Types").cells
    got = {cells[(r, 1)].value: cells[(r, 2)] for r in range(2, 22) if (r, 1) in cells and (r, 2) in cells}
    assert got["Integer"].value == 1200 and isinstance(got["Integer"].value, int)
    assert got["Decimal"].value == 0.125 and got["Small"].value == -3.2e-07
    assert got["Boolean"].value is True
    assert got["Date"].value == dt.datetime(2026, 10, 7) and got["Date-time"].value == dt.datetime(2026, 10, 7, 14, 30, 5)
    assert got["Time"].value == dt.time(9, 5, 0)
    assert got["Error"].value == "#DIV/0!" and got["Error"].error
    assert "Empty" not in got
    for kind, text in {"Looks numeric": "00123", "Looks like a formula": "=not a formula", "Looks boolean": "TRUE",
                       "Pipe": "a|b", "Backslash": "C:\\dir\\", "Line break": "line1\nline2", "Literal tag": "1 <br> 2",
                       "Padded": " padded ", "Quoted": '"hello"', "Leading apostrophe": "'quoted"}.items():
        assert got[kind].value == text and not got[kind].error, kind


def test_loose_cells_keep_their_number_formats():
    cells = cellprose.load(read("05_loose_merges_hidden.sheet.md")).sheet("Q1 #2").cells
    assert cells[(4, 6)].value == dt.datetime(2026, 12, 25) and cells[(4, 6)].number_format == "yyyy-mm-dd"
    assert cells[(6, 6)].formula == "B6*2" and cells[(6, 6)].number_format == "#,##0"
    assert cells[(2, 6)].value == "Prepared by finance" and cells[(2, 6)].number_format == "General"


def test_hidden_sheet_and_sheet_scoped_name():
    wb = cellprose.load(read("05_loose_merges_hidden.sheet.md"))
    assert [s.state for s in wb.sheets] == ["visible", "hidden"]
    assert wb.sheet("Notes").names == {"Local": "Notes!$B$1"} and wb.names == {}
    assert wb.sheet("Q1 #2").merges == ["A1:C1"]


# ---- known limits the spec states ----------------------------------------------------------------------

def test_array_formulas_round_trip(tmp_path):
    from openpyxl.worksheet.formula import ArrayFormula
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["A2"] = 1, 2
    ws["B1"] = ArrayFormula("B1:B2", "=A1:A2*2")
    ws["B2"] = 4
    path = tmp_path / "arr.xlsx"
    wb.save(path)
    text = cellprose.dumps(path, recalc="never")
    assert "```arrays\nB1:B2 = A1:A2*2\n```" in text and "ArrayFormula" not in text
    back = cellprose.load(text).to_openpyxl().active
    assert back["B1"].value.ref == "B1:B2" and back["B1"].value.text == "=A1:A2*2" and back["B2"].value == 4


def test_data_table_formulas_are_written_as_values_with_a_warning(tmp_path):
    from openpyxl.worksheet.formula import DataTableFormula
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["A2"] = 1, 2
    ws["B1"] = DataTableFormula("B1:B2", r1="A1", dt2D=False, dtr=False)
    path = tmp_path / "tbl.xlsx"
    wb.save(path)
    with pytest.warns(UserWarning, match=r"data-table formulas are not supported.*Sheet!B1"):
        text = cellprose.dumps(path, recalc="never")
    assert "DataTableFormula" not in text and "\n1|1|?\n" in text
    assert "data-table formulas are not supported" in text.split("---")[1]


def test_v02_grid_with_outer_pipes_is_still_read():
    text = "---\nsheetmark: 0.2\n---\n\n# Sheet: S\n\n## A1:B2\n\n|#|A|B|\n|-|-|-|\n|1|x|1|\n|2|y||\n"
    cells = cellprose.load(text).sheet("S").cells
    assert cells[(1, 1)].value == "x" and cells[(2, 1)].value == "y" and (2, 2) not in cells


def test_v03_short_rows_are_padded_and_a_trailing_pipe_is_an_empty_cell():
    text = "---\ncellprose: 0.3\n---\n\n# Sheet: S\n\n## A1:C3\n\n#|A|B|C\n-|-|-|-\n1|a|b|c\n2|d\n3|\n"
    cells = cellprose.load(text).sheet("S").cells
    assert {k: v.value for k, v in cells.items()} == {(1, 1): "a", (1, 2): "b", (1, 3): "c", (2, 1): "d"}


# ---- comments, validation and the "not carried" note (SPEC §3, §8) --------------------------------------

def test_comments_and_validation_are_read():
    sh = cellprose.load(read("07_comments_validation.sheet.md")).sheet("Budget")
    assert sh.comments == {(3, 3): "Excludes one-offs.\nCheck with | finance"}
    assert sh.validations == [("B2:B3", "list", None, '"Yes,No"', None), ("C2", "whole", "between", "0", "100")]
    ws = sh and cellprose.load(read("07_comments_validation.sheet.md")).to_openpyxl()["Budget"]
    assert ws["C3"].comment.text == "Excludes one-offs.\nCheck with | finance"
    assert {str(d.sqref): d.type for d in ws.data_validations.dataValidation} == {"B2:B3": "list", "C2": "whole"}


def test_dropped_features_are_counted_in_the_note(tmp_path):
    from openpyxl.chart import BarChart, Reference
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([1, 2])
    ws.append([3, 4])
    for anchor in ("D2", "D20"):
        chart = BarChart()
        chart.add_data(Reference(ws, min_col=1, min_row=1, max_row=2))
        ws.add_chart(chart, anchor)
    ws["A1"].hyperlink = "https://example.com"
    path = tmp_path / "dropped.xlsx"
    wb.save(path)
    head = cellprose.dumps(path, recalc="never").split("---")[1]
    assert "note: 'not carried: 2 charts, 1 hyperlink'" in head
