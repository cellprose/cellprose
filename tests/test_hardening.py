"""Hostile input must fail fast instead of exhausting memory or writing outside the repository."""
import subprocess
import zipfile

import openpyxl
import pytest

import cellprose
from cellprose import gitflow, reader, writer

HEAD = "---\ncellprose: 0.3\n---\n# Sheet: S\n## A1:A1\n#|A\n-|-\n1|1\n\n"


@pytest.mark.parametrize("block", ["```formats\nA1:XFD1048576 = 0.00\n```\n", "```formulas\nA1:ZZ99999 = 1+1\n```\n"])
def test_huge_range_is_rejected(block):
    with pytest.raises(cellprose.ParseError, match="more than"):
        cellprose.load(HEAD + block)


def test_normal_fill_range_still_loads():
    wb = cellprose.load(HEAD + "```formulas\nA2:A50 = A1+1\n```\n")
    assert len(wb.sheet("S").cells) == 50


def test_external_link_index_is_clamped(tmp_path):
    wb = cellprose.load(HEAD + "```formulas\nA2 = [3000000]S!A1\n```\n")
    with pytest.raises(ValueError, match="external link index"):
        wb.to_xlsx(tmp_path / "x.xlsx")


def test_zip_bomb_is_refused_before_openpyxl(tmp_path, monkeypatch):
    book = tmp_path / "ok.xlsx"
    openpyxl.Workbook().save(book)
    bomb = tmp_path / "bomb.xlsx"
    with zipfile.ZipFile(book) as zi, zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            zo.writestr(it, zi.read(it.filename))
        zo.writestr("xl/padding.xml", b"A" * (20 * 1024 * 1024))       # ~20 KB compressed, ratio > 1000
    with pytest.raises(ValueError, match="expands"):
        writer.load_pair(bomb)
    monkeypatch.setattr(writer, "MAX_UNZIPPED", 1024)
    with pytest.raises(ValueError, match="limit"):
        writer.load_pair(book)


def test_precommit_will_not_write_through_a_symlink(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    openpyxl.Workbook().save(repo / "book.xlsx")
    victim = tmp_path / "victim.txt"
    victim.write_text("precious")
    (repo / "book.sheet.md").symlink_to(victim)
    subprocess.run(["git", "add", "book.xlsx"], cwd=repo, check=True)
    assert gitflow.precommit(repo) == 1
    assert victim.read_text() == "precious"


def test_one_far_cell_does_not_walk_the_whole_sheet(tmp_path):
    """A sheet's bounding box can be 17 billion cells; only the cells that exist may be visited."""
    import time
    import openpyxl
    from cellprose import dumps
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["A2"], ws["XFD1048576"] = 1, 2, "x"
    p = tmp_path / "far.xlsx"
    wb.save(p)
    t = time.time()
    text = dumps(p, recalc="never")
    assert "XFD1048576: x" in text
    assert time.time() - t < 20


BASE = "---\ncellprose: 0.3\n---\n# Sheet: S\n\n## A1:B2\n\n#|A|B\n-|-|-\n"


def _bad(text, needle):
    import pytest
    from cellprose import ParseError, load
    with pytest.raises(ParseError, match=needle):
        load(text)


def test_reader_rejects_numbers_rows_and_characters_it_cannot_store():
    _bad(BASE + "1|" + "9" * 5000 + "|1\n2|1|1\n", "out of range")
    _bad(BASE + "1|1e999|1\n2|1|1\n", "out of range")
    _bad(BASE + "0|1|1\n2|1|1\n", "row 0")
    _bad(BASE + "99999999|1|1\n", "row 99999999")
    _bad(BASE + "1|a\x01b|1\n", "control character")
    _bad(BASE.replace("#|A|B", "#|A|XFE") + "1|1|1\n", "column beyond")
    _bad(BASE + "1|1|1\n\n```formats\nA1:A99999999 = 0\n```\n", "outside the worksheet")


def test_reader_stops_at_the_cell_limit_while_parsing(monkeypatch):
    from cellprose import reader
    monkeypatch.setattr(reader, "MAX_CELLS", 10)
    _bad(BASE + "1|1|1\n2|1|1\n\n```formats\nA1:C9 = 0\nD1:E9 = 0\n```\n", "more than 10 cells")


def test_load_accepts_crlf_text():
    from cellprose import load
    wb = load((BASE + "1|x|1\n2|y|2\n").replace("\n", "\r\n"))
    assert wb.sheets[0].cells[(1, 1)].value == "x"


def test_dumps_leaves_no_recalculated_copy_behind(tmp_path):
    import glob
    import tempfile
    import openpyxl
    import pytest
    from cellprose import dumps
    from cellprose.recalc import soffice
    if not soffice():
        pytest.skip("LibreOffice not installed")
    wb = openpyxl.Workbook()
    wb.active["A1"], wb.active["B1"] = 1, "=A1+1"
    p = tmp_path / "f.xlsx"
    wb.save(p)
    before = set(glob.glob(tempfile.gettempdir() + "/cellprose-*"))
    assert "B1 = A1+1" in dumps(p)
    assert set(glob.glob(tempfile.gettempdir() + "/cellprose-*")) == before


def test_recalc_timeout_raises_and_cleans_up(tmp_path, monkeypatch):
    import subprocess
    import sys
    from cellprose import recalc
    monkeypatch.setattr(recalc, "soffice", lambda: sys.executable)
    f = tmp_path / "-x.xlsx"
    f.write_bytes(b"")
    import pytest
    with pytest.raises((subprocess.TimeoutExpired, subprocess.CalledProcessError)):
        recalc.recalc_copy(f, timeout=1)


def test_cli_reports_a_bad_file_in_one_line(tmp_path, capsys):
    from cellprose.cli import main
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"not a zip")
    assert main(["encode", str(bad)]) == 1
    assert main(["encode", str(tmp_path / "missing.xlsx")]) == 1
    err = capsys.readouterr().err
    assert err.count("error:") == 2 and "Traceback" not in err


def test_hook_does_not_block_commits_when_cellprose_is_missing(tmp_path):
    import shutil
    import subprocess
    from cellprose import gitflow
    sh = shutil.which("sh")
    if not sh:
        return
    hook = tmp_path / "hook"
    hook.write_text("#!/bin/sh\n" + gitflow.HOOK_BODY)
    r = subprocess.run([sh, str(hook)], env={"PATH": "/nonexistent"}, capture_output=True, text=True)
    assert r.returncode == 0 and "not on PATH" in r.stderr


def test_huge_array_range_is_not_enumerated(tmp_path):
    import openpyxl
    from openpyxl.worksheet.formula import ArrayFormula
    from cellprose import dumps
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"] = ArrayFormula("A1:XFD1048576", "=1")
    ws["B1"] = 2
    p = tmp_path / "arr.xlsx"
    wb.save(p)
    assert "A1:XFD1048576 = 1" in dumps(p, recalc="never")
