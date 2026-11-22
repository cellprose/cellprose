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
