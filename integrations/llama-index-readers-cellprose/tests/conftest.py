import openpyxl
import pytest


@pytest.fixture
def book(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plan"
    ws.append(["Item", "Units", "Price", "Total"])
    ws.append(["Tea", 3, 2.5, "=B2*C2"])
    ws.append(["Cake", 2, 4, "=B3*C3"])
    s = wb.create_sheet("Q#2")
    s.append(["Total", "=SUM(Plan!D2:D3)"])
    from openpyxl.workbook.defined_name import DefinedName
    wb.defined_names["Units"] = DefinedName("Units", attr_text="Plan!$B$2:$B$3")
    p = tmp_path / "plan.xlsx"
    wb.save(p)
    return p
