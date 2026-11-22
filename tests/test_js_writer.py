"""The JavaScript writer (js/) against the conformance kit and against the Python writer on a real .xlsx file.

Skipped when node is not installed. The JS package has its own unit tests (`cd js && npm test`).
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from cellprose import dumps

from corpus import edge_workbook

ROOT = Path(__file__).parent.parent
ENCODE = ROOT / "js" / "bin" / "cellprose-encode.js"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")


def test_js_writer_passes_the_kit():
    r = subprocess.run([sys.executable, str(ROOT / "conformance" / "check.py"), "--encoder", f"{NODE} {ENCODE}"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout
    assert "FAIL" not in r.stdout


def test_js_writer_reads_an_xlsx_as_the_python_writer_does(tmp_path):
    path = tmp_path / "edge.xlsx"
    edge_workbook(path)
    js = subprocess.run([NODE, str(ENCODE), str(path)], capture_output=True, check=True)
    assert js.stdout.decode("utf-8") == dumps(path, recalc="never")


def test_js_writer_matches_python_on_empty_string_results(tmp_path):
    import zipfile
    import openpyxl
    raw, path = tmp_path / "raw.xlsx", tmp_path / "empty.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["B1"], ws["C1"], ws["E5"] = 1, '=IF(A1>5,1,"")', "=A1+1", '=IF(A1>5,1,"")'
    wb.save(raw)
    with zipfile.ZipFile(raw) as zin, zipfile.ZipFile(path, "w") as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name == "xl/worksheets/sheet1.xml":
                for coord in ("B1", "E5"):
                    data = data.replace(f'<c r="{coord}"><f>'.encode(), f'<c r="{coord}" t="str"><f>'.encode())
            zout.writestr(name, data)
    js = subprocess.run([NODE, str(ENCODE), str(path)], capture_output=True, check=True).stdout.decode("utf-8")
    py = dumps(path, recalc="never")
    assert js.split("---\n", 2)[2] == py.split("---\n", 2)[2]   # (front matter differs by `source:`)
    assert '# ""' in js


def test_js_writer_matches_python_on_comments_validation_and_dropped_features(tmp_path):
    import openpyxl
    from openpyxl.chart import BarChart
    from openpyxl.comments import Comment
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Budget"
    ws.append(["Item", "Status", "Qty"])
    ws.append(["Pens", "Yes", 5])
    ws.append(["Ink", "No", 120])
    ws["C3"].comment = Comment("Excludes one-offs.\nCheck with | finance", "A")
    ws["A1"].comment = Comment("a\\b <br> c", "A")
    for sqref, kw in (("B2:B3 E5", dict(type="list", formula1='"Yes,No"')),
                      ("C2", dict(type="whole", operator="between", formula1="0", formula2="100")),
                      ("C3", dict(type="decimal", operator="greaterThan", formula1="Budget!$A$1"))):
        dv = DataValidation(sqref=sqref, **kw)
        ws.add_data_validation(dv)
    ws.add_chart(BarChart(), "H2")
    ws.add_chart(BarChart(), "H20")
    ws.conditional_formatting.add("C2:C3", CellIsRule(operator="greaterThan", formula=["50"]))
    ws["A2"].hyperlink = "https://example.com"
    ws.merge_cells("E1:G2")
    ws["E1"] = "merged"
    ws["E1"].hyperlink = "https://example.com/merged"
    path = tmp_path / "extras.xlsx"
    wb.save(path)
    js = subprocess.run([NODE, str(ENCODE), str(path)], capture_output=True, check=True).stdout.decode("utf-8")
    py = dumps(path, recalc="never")
    assert js == py
    assert "```comments" in py and "```validation" in py and "not carried: 2 charts, 1 conditional format, 2 hyperlinks" in py
