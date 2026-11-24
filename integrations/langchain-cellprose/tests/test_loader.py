import pytest

from langchain_cellprose import CellproseLoader, split_sheets


def test_workbook_mode(book):
    docs = CellproseLoader(book).load()
    assert len(docs) == 1
    assert docs[0].page_content.startswith("---\ncellprose: 0.3")
    assert "D2:D3 = B2*C2" in docs[0].page_content
    assert docs[0].metadata == {"source": str(book), "format": "cellprose"}


def test_sheet_mode(book):
    docs = CellproseLoader(book, mode="sheet").load()
    assert [d.metadata.get("sheet") for d in docs] == ["Plan", "Q#2", None]
    assert docs[-1].metadata["section"] == "names"
    for d in docs:
        assert d.page_content.startswith("---\ncellprose: 0.3")
    assert "# Sheet: Plan" in docs[0].page_content and "Q#2" not in docs[0].page_content
    assert "\n# Names" in docs[-1].page_content


def test_sheet_mode_keeps_the_row_number_legend(book):
    for d in CellproseLoader(book, mode="sheet").load():
        assert "Note: the first field of each table row is its row number" in d.page_content


def test_reads_sheet_md(tmp_path, book):
    import cellprose
    p = tmp_path / "plan.sheet.md"
    p.write_text(cellprose.dumps(book, recalc="never"), encoding="utf-8")
    assert CellproseLoader(p).load()[0].page_content == p.read_text(encoding="utf-8")


def test_split_ignores_fenced_headings():
    text = "---\ncellprose: 0.3\n---\n\n# Sheet: A\n\n```formulas\n# Sheet: not a sheet\n```\n"
    parts = split_sheets(text)
    assert [n for n, _ in parts] == ["A"]


def test_bad_mode():
    with pytest.raises(ValueError):
        CellproseLoader("x.xlsx", mode="rows")
