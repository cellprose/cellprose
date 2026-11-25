from llama_index.core import SimpleDirectoryReader

from llama_index.readers.cellprose import CellproseReader


def test_workbook_mode(book):
    docs = CellproseReader().load_data(book, extra_info={"team": "fp&a"})
    assert len(docs) == 1
    assert "D2:D3 = B2*C2" in docs[0].text
    assert docs[0].metadata["file_name"] == "plan.xlsx" and docs[0].metadata["team"] == "fp&a"


def test_sheet_mode(book):
    docs = CellproseReader(mode="sheet").load_data(book)
    assert [d.metadata.get("sheet") for d in docs] == ["Plan", "Q#2", None]
    assert all(d.text.startswith("---\ncellprose: 0.3") for d in docs)


def test_simple_directory_reader(book):
    docs = SimpleDirectoryReader(input_files=[str(book)], file_extractor={".xlsx": CellproseReader()}).load_data()
    assert len(docs) == 1 and "# Sheet: Plan" in docs[0].text


def test_sheet_mode_keeps_the_row_number_legend(book):
    from llama_index.readers.cellprose import CellproseReader
    for d in CellproseReader(mode="sheet").load_data(book):
        assert "Note: the first field of each table row is its row number" in d.text
