import io

import openpyxl
import pytest
from markitdown import MarkItDown, StreamInfo

from markitdown_cellprose import CellproseConverter, register_converters


@pytest.fixture
def book(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plan"
    ws.append(["Item", "Units", "Price", "Total"])
    ws.append(["Tea", 3, 2.5, "=B2*C2"])
    ws.append(["Cake", 2, 4, "=B3*C3"])
    p = tmp_path / "plan.xlsx"
    wb.save(p)
    return p


def test_registered_converter_wins_over_builtin(book):
    md = MarkItDown(enable_plugins=False)
    register_converters(md)
    out = md.convert(str(book)).markdown
    assert out.startswith("---\ncellprose: 0.3")
    assert "# Sheet: Plan" in out
    assert "D2:D3 = B2*C2" in out
    assert "source: plan.xlsx" in out


def test_accepts_by_extension_and_mime():
    c = CellproseConverter()
    assert c.accepts(io.BytesIO(), StreamInfo(extension=".XLSX"))
    assert c.accepts(io.BytesIO(), StreamInfo(
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
    assert not c.accepts(io.BytesIO(), StreamInfo(extension=".csv"))


def test_stream_and_options(book):
    md = MarkItDown(enable_plugins=False)
    register_converters(md)
    with open(book, "rb") as f:
        out = md.convert_stream(f, stream_info=StreamInfo(extension=".xlsx", filename="plan.xlsx"),
                                cellprose_options={"legend": False}).markdown
    assert "# Sheet: Plan" in out


def test_entry_point_declared():
    from importlib.metadata import entry_points
    names = [e.value for e in entry_points(group="markitdown.plugin")]
    if "markitdown_cellprose" not in names:
        pytest.skip("package not installed (run pip install -e integrations/markitdown-cellprose)")
