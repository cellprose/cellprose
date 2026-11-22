import datetime as dt
from pathlib import Path

import openpyxl
import pytest

import cellprose
from cellprose.writer import fmt_value

BENCH = Path(__file__).parent.parent / "benchmarks" / "workbooks"


@pytest.mark.parametrize("value,computed,expected", [
    (1515987.648, True, "1515990"),
    (0.2466666667, True, "0.246667"),
    # 6 significant figures, not 6 decimals, below 0.1 too (SPEC section 5.3)
    (0.0296862123, True, "0.0296862"),
    (0.000123456789, True, "0.000123457"),
    (9.9999995e-05, True, "0.0001"),
    (-0.0588235294, True, "-0.0588235"),
    (1.234567e-05, True, "1.23457e-05"),
    (0.1, False, "0.1"),
    (45, False, "45"),
    (True, False, "TRUE"),
    (dt.datetime(2026, 10, 7), False, "2026-10-07"),
    ("00123", False, "'00123"),
    ("=not a formula", False, "'=not a formula"),
    ("a|b", False, "a\\|b"),
    ("line1\nline2", False, "line1<br>line2"),
    (" padded ", False, '" padded "'),
    # v0.2 escaping, added with the decoder so every cell reads back exactly (see docs/SPEC.md section 5.2)
    ('"hello"', False, '"""hello"""'),
    ("say \"hi\"", False, 'say "hi"'),
    ("C:\\dir\\", False, "C:\\\\dir\\\\"),
    ("a\\|b", False, "a\\\\\\|b"),
    ("1 <br> 2", False, "1 \\<br> 2"),
    ("a\r\nb\rc", False, "a<br>b<br>c"),
    ("12:30:00", False, "'12:30:00"),
    ("10:30", False, "10:30"),
    ("12:30:00 pm", False, "'12:30:00 pm"),
])
def test_fmt_value(value, computed, expected):
    assert fmt_value(value, computed=computed) == expected


def test_canonical_and_deterministic():
    p = BENCH / "11_forecast_overrides.xlsx"
    a, b = cellprose.dumps(p), cellprose.dumps(p)
    assert a == b and a.endswith("\n") and "\r" not in a


def test_overrides_visible_as_gaps():
    text = cellprose.dumps(BENCH / "11_forecast_overrides.xlsx")
    assert "C2:E2 = B2*(1+$B$7)" in text and "G2:I2 = F2*(1+$B$7)" in text  # F2 typed in
    assert "\n2|Bookings|100000|" in text


def test_sheet_and_range_filters():
    text = cellprose.dumps(BENCH / "05_multisheet_model.xlsx", sheets=["Costs"], cell_range="A1:B4")
    assert "# Sheet: Costs" in text and "# Sheet: Revenue" not in text
    assert "## A1:B4" in text and "|C|" not in text


def test_missing_cached_values_marked(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["A2"], ws["A3"] = 2, 3, "=A1*A2"
    p = tmp_path / "raw.xlsx"
    wb.save(p)
    text = cellprose.dumps(p, recalc="never")
    assert "\n3|?\n" in text and "A3 = A1*A2" in text


def _cache_empty_string(src, dst, coords):
    """Copy an .xlsx, marking the given formula cells as calculated to "" (`t="str"`, empty `<v>`), as Excel does."""
    import zipfile
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name == "xl/worksheets/sheet1.xml":
                for coord in coords:
                    data = data.replace(f'<c r="{coord}"><f>'.encode(), f'<c r="{coord}" t="str"><f>'.encode())
            zout.writestr(name, data)


def test_empty_string_result_is_an_empty_cell_not_missing(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["B1"], ws["C1"], ws["E5"] = 1, '=IF(A1>5,1,"")', "=A1+1", '=IF(A1>5,1,"")'
    raw = tmp_path / "raw.xlsx"
    wb.save(raw)
    p = tmp_path / "cached.xlsx"
    _cache_empty_string(raw, p, ["B1", "E5"])
    text = cellprose.dumps(p, recalc="never")
    assert "\n1|1||?\n" in text                      # B1 is empty, C1 (never calculated) is still ?
    assert 'E5 = IF(A1>5,1,"")  # ""' in text
    assert "note:" in text                         # C1 still needs recalculation

    ws["C1"] = 2
    wb.save(raw)
    _cache_empty_string(raw, p, ["B1", "E5"])
    text = cellprose.dumps(p, recalc="never")
    assert "|?|" not in text and "note:" not in text
    assert not cellprose.needs_recalc(p)


def test_lone_equals_is_text_not_an_empty_formula(tmp_path):
    """LibreOffice writes `<f></f>` (cached #VALUE!) for a cell that holds just "="; there is nothing to recompute."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["B1"], ws["A2"], ws["B2"] = "a", "b", "=", 2
    ws["A2"].data_type = "f"
    path = tmp_path / "eq.xlsx"
    wb.save(path)
    text = cellprose.dumps(path, recalc="never")
    assert "\n2|'=|2\n" in text and "```formulas" not in text and "?" not in text


def test_empty_text_cells_are_not_part_of_a_region(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["B1"], ws["A2"], ws["B2"], ws["A3"], ws["B3"], ws["D6"] = "a", "b", 1, 2, "", "", ""
    ws["A3"].number_format = "0.00"
    path = tmp_path / "blank.xlsx"
    wb.save(path)
    text = cellprose.dumps(path, recalc="never")
    assert "## A1:B2" in text and "\n3|" not in text and "D6" not in text and "```formats" not in text
    assert cellprose.dumps(cellprose.load(text).to_xlsx(tmp_path / "back.xlsx"), recalc="never").split("---\n", 2)[2] \
        == text.split("---\n", 2)[2]


def test_defined_name_with_no_target_is_left_out(tmp_path):
    from openpyxl.workbook.defined_name import DefinedName
    wb = openpyxl.Workbook()
    wb.active["A1"] = 1
    wb.defined_names["Real"] = DefinedName("Real", attr_text="Sheet!$A$1")
    wb.defined_names["_xlfn_SINGLE"] = DefinedName("_xlfn_SINGLE", attr_text="")
    path = tmp_path / "n.xlsx"
    wb.save(path)
    text = cellprose.dumps(path, recalc="never")
    assert "Real = Sheet!$A$1" in text and "_xlfn_SINGLE" not in text
