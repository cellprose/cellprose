import pytest
from langchain_cellprose import CellproseLoader, split_sheets


def test_workbook_mode(book):
    docs = CellproseLoader(book).load()
    assert len(docs) == 1
    assert docs[0].page_content.startswith("---\ncellprose: 0.3")
    assert "D2:D3 = B2*C2" in docs[0].page_content
    assert docs[0].metadata == {"source": str(book), "filename": "plan.xlsx", "format": "cellprose",
                                "cellprose_version": "0.3", "profile": "full", "sheet_count": 2}


def test_sheet_mode(book):
    docs = CellproseLoader(book, mode="sheet").load()
    assert [d.metadata.get("sheet") for d in docs] == ["Plan", "Q#2", None]
    assert docs[-1].metadata["section"] == "names"
    assert [d.metadata.get("sheet_index") for d in docs] == [0, 1, None]
    assert docs[0].metadata["sheet_count"] == 2 and docs[0].metadata["filename"] == "plan.xlsx"
    for d in docs:
        assert d.page_content.startswith("---\ncellprose: 0.3")
    assert "# Sheet: Plan" in docs[0].page_content and "Q#2" not in docs[0].page_content
    assert docs[-1].page_content.split("---\n")[-1].lstrip().startswith("# Names")


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


def test_compact_profile_is_reported(tmp_path):
    p = tmp_path / "log.sheet.md"
    p.write_text("---\ncellprose: 0.3\nprofile: compact\n---\n\n# Sheet: Log\n\n## A1:B2\n\n#|A|B\n-|-|-\n1|a|b\n",
                 encoding="utf-8")
    meta = CellproseLoader(p).load()[0].metadata
    assert meta["profile"] == "compact" and meta["filename"] == "log.sheet.md"

