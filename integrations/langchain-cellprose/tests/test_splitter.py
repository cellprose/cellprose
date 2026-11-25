import openpyxl
import pytest
from langchain_cellprose import CellproseLoader, CellproseSplitter
from langchain_core.documents import Document
from openpyxl.comments import Comment
from openpyxl.workbook.defined_name import DefinedName

import cellprose


@pytest.fixture
def model(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plan"
    ws.append(["Item", "Units", "Price", "Total"])
    for i in range(2, 41):
        ws.append([f"i{i}", i, 2.5, f"=B{i}*C{i}*Rate"])
    ws["A50"], ws["B50"] = "Rate note", 0.2
    ws["B50"].comment = Comment("the rate", "x")
    ws["B51"] = "=B50*2"
    ws["F60"] = "loose"
    ws.merge_cells("A70:B70")
    wb.defined_names["Rate"] = DefinedName("Rate", attr_text="Plan!$B$50")
    wb.defined_names["Unused"] = DefinedName("Unused", attr_text="Plan!$Z$1")
    wb.create_sheet("Notes").append(["Total", "=SUM(Plan!D2:D40)"])
    wb.create_sheet("Hidden").sheet_state = "hidden"
    wb["Hidden"].append(["h", 1])
    p = tmp_path / "model.xlsx"
    wb.save(p)
    return p


@pytest.fixture
def text(model):
    return cellprose.dumps(model, recalc="never")


def test_one_chunk_per_region_with_its_formulas(text):
    chunks = CellproseSplitter().split_chunks(text)
    regions = [c for c in chunks if c.metadata["chunk_kind"] == "region"]
    first = next(c for c in regions if c.metadata["region"] == "A1:D40")
    assert "D2:D40 = B2*C2*Rate" in first.text and "1|Item|Units|Price|Total" in first.text
    assert "40|i40" in first.text and "B51 = B50*2" not in first.text
    second = next(c for c in regions if c.metadata["region"] == "A50:B51")
    assert "B51 = B50*2" in second.text and "B50: the rate" in second.text    # its comment came along
    assert "D2:D40" not in second.text


def test_every_chunk_reads_alone(text):
    for c in CellproseSplitter().split_chunks(text):
        assert c.text.startswith("---\ncellprose: 0.3")
        if c.metadata["chunk_kind"] == "region":
            assert "Note: the first field of each table row" in c.text
            assert "# Sheet: " in c.text and "## " in c.text


def test_relevant_names_only(text):
    chunks = CellproseSplitter().split_chunks(text)
    plan = next(c for c in chunks if c.metadata.get("region") == "A1:D40")
    assert "Rate = Plan!$B$50" in plan.text and "Unused" not in plan.text      # used by its formulas
    target = next(c for c in chunks if c.metadata.get("region") == "A50:B51")
    assert "Rate = Plan!$B$50" in target.text                                   # points into the region
    notes = next(c for c in chunks if c.metadata.get("sheet") == "Notes")
    assert "# Names" not in notes.text
    last = chunks[-1]
    assert last.metadata["chunk_kind"] == "names" and "Unused" in last.text      # the full list is kept too
    assert "# Names" not in CellproseSplitter(include_names=False).split_chunks(text)[0].text


def test_loose_cells_and_merges_get_their_own_chunk(text):
    loose = [c for c in CellproseSplitter().split_chunks(text) if c.metadata["chunk_kind"] == "loose"]
    assert len(loose) == 1 and "F60: loose" in loose[0].text and "A70:B70" in loose[0].text


def test_by_sheet(text):
    chunks = CellproseSplitter(by="sheet").split_chunks(text)
    assert [c.metadata["sheet"] for c in chunks if "sheet" in c.metadata] == ["Plan", "Notes", "Hidden"]
    assert chunks[-1].metadata["chunk_kind"] == "names"
    plan = chunks[0].text
    assert "## A1:D40" in plan and "## A50:B51" in plan and "F60: loose" in plan
    assert "```meta\nhidden: true" in chunks[2].text                              # sheet meta survives


def test_by_sheet_falls_back_to_regions_when_too_big(text):
    chunks = CellproseSplitter(by="sheet", chunk_size=1000).split_chunks(text)
    assert {c.metadata["chunk_kind"] for c in chunks if c.metadata.get("sheet") == "Plan"} == {"region", "loose"}


def test_large_region_is_cut_into_bands_that_keep_the_formula(text):
    s = CellproseSplitter(chunk_size=900)
    chunks = [c for c in s.split_chunks(text) if c.metadata.get("region") == "A1:D40"]
    assert len(chunks) > 1 and all(c.metadata["parts"] == len(chunks) for c in chunks)
    for k, c in enumerate(chunks):
        assert c.metadata["part"] == k and "profile: compact" in c.text
        assert "1|Item|Units|Price|Total" in c.text                    # header row repeated
        assert "D2:D40 = B2*C2*Rate" in c.text                         # the anchor travels with every band
        assert "Rate = Plan!$B$50" in c.text and "```elided" in c.text
    assert all(s.length(c.text) <= 900 + 200 for c in chunks)          # near the limit; the fixed head is not cut


def test_bands_cover_rows_once(text):
    chunks = [c for c in CellproseSplitter(chunk_size=900).split_chunks(text) if c.metadata.get("region") == "A1:D40"]
    seen = []
    for c in chunks:
        seen += [int(ln.split("|")[0]) for ln in c.text.splitlines() if ln[:1].isdigit() and ln.split("|")[1:2] and
                 ln.split("|")[1].startswith("i")]
    assert sorted(seen) == list(range(2, 41))


def test_compact_input_stays_compact():
    compact = ("---\ncellprose: 0.3\nprofile: compact\n---\n\n# Sheet: Log\n\n## A1:B13\n\n#|A|B\n-|-|-\n1|Day|Visits\n"
               "2|D01|10\n…|…|…\n13|D12|120\n\n```elided\nrows: 3-12  # 10 rows not shown\n```\n")
    (chunk,) = CellproseSplitter().split_chunks(compact)
    assert chunk.text.count("profile: compact") == 1 and "rows: 3-12" in chunk.text


def test_documents_keep_loader_metadata(model):
    docs = CellproseLoader(model).load()
    out = CellproseSplitter().split_documents(docs)
    assert out[0].metadata["filename"] == "model.xlsx" and out[0].metadata["cellprose_version"] == "0.3"
    assert out[0].metadata["region"] == "A1:D40" and out[0].metadata["sheet_index"] == 0
    sheet_docs = CellproseLoader(model, mode="sheet").load()
    out = CellproseSplitter().transform_documents(sheet_docs)
    notes = next(d for d in out if d.metadata.get("sheet") == "Notes")
    assert notes.metadata["sheet_index"] == 1 and notes.metadata["profile"] == "full"


def test_text_without_structure_comes_back_whole():
    assert CellproseSplitter().split_text("just some text") == ["just some text"]
    assert CellproseSplitter().split_documents([Document(page_content="x", metadata={"a": 1})])[0].metadata["a"] == 1


def test_bad_options():
    with pytest.raises(ValueError):
        CellproseSplitter(by="row")
    with pytest.raises(ValueError):
        CellproseSplitter(chunk_size=0)
