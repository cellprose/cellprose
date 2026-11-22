"""The Sheetmark to Cellprose rename: old files, old extension and the old package name keep working."""
import subprocess
import sys
import warnings
from pathlib import Path

import openpyxl

import cellprose
from cellprose import gitflow
from cellprose.cli import main

ROOT = Path(__file__).parent.parent


def _text(key, tmp_path):
    x = tmp_path / "t.xlsx"
    wb = openpyxl.Workbook()
    wb.active.title = "S"
    wb.active.append(["x", 1])
    wb.active.append(["y", 2])
    wb.save(x)
    return cellprose.dumps(x).replace("cellprose: 0.3", f"{key}: 0.3", 1)


def test_writer_emits_the_cellprose_key(tmp_path):
    p = tmp_path / "b.xlsx"
    wb = openpyxl.Workbook()
    wb.active["A1"] = 1
    wb.save(p)
    text = cellprose.dumps(p)
    assert text.startswith("---\ncellprose: 0.3\n")
    assert "sheetmark" not in text.split("---")[1]


def test_reader_accepts_both_front_matter_keys(tmp_path):
    old = cellprose.load(_text("sheetmark", tmp_path))
    new = cellprose.load(_text("cellprose", tmp_path))
    assert [s.name for s in old.sheets] == [s.name for s in new.sheets] == ["S"]


def test_cli_reads_and_writes_both_extensions(tmp_path):
    for ext in (".sheet.md", ".cellprose.md"):
        src = tmp_path / f"in{ext}"
        src.write_text(_text("cellprose", tmp_path), encoding="utf-8")
        assert main(["check", str(src)]) == 0
        assert main(["decode", str(src)]) == 0
        assert (tmp_path / "in.xlsx").exists()
        (tmp_path / "in.xlsx").unlink()
    x = tmp_path / "w.xlsx"
    openpyxl.Workbook().save(x)
    out = tmp_path / "w.cellprose.md"
    assert main(["encode", str(x), "-o", str(out)]) == 0 and out.exists()
    assert main(["check", str(out)]) == 0
    assert main(["encode", str(x)]) == 0 and (tmp_path / "w.sheet.md").exists()


def test_sidecar_uses_an_existing_cellprose_md(tmp_path):
    x = tmp_path / "m.xlsx"
    assert gitflow.sidecar(x).name == "m.sheet.md"
    (tmp_path / "m.cellprose.md").write_text("x")
    assert gitflow.sidecar(x).name == "m.cellprose.md"
    (tmp_path / "m.sheet.md").write_text("x")
    assert gitflow.sidecar(x).name == "m.sheet.md"


def test_old_package_name_forwards_to_cellprose():
    code = ("import warnings; warnings.simplefilter('ignore'); import sheetmark, sheetmark.reader as r, cellprose;"
            "assert sheetmark.dumps is cellprose.dumps and r.SUPPORTED == ('0.2', '0.3')")
    shim = ROOT / "packaging" / "sheetmark-shim" / "src"
    r = subprocess.run([sys.executable, "-c", code], env={"PYTHONPATH": str(shim), "PATH": ""}, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
