"""The benchmark real-world set (benchmarks/external/realworld2/, docs/PROTOCOL.md section 3).

The question rules are checked on a small workbook built here. The committed set is checked for form, for a perfect
answer scoring 1, for being held out, and for its pinned sources; recomputing the ground truth needs the source files
(the Enron ones are committed; the Damodaran ones are not, so those are skipped without them)."""
import json
import shutil
import sys
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(BENCH / "external"))
import realworld2 as rw2  # noqa: E402
import score  # noqa: E402
from runner import split as splitmod  # noqa: E402

RW2 = rw2.OUT
HAVE = (RW2 / "selection.json").exists()
SEL = json.loads((RW2 / "selection.json").read_text())["workbooks"] if HAVE else {}
TYPES = {"lookup", "address", "trace", "impact", "hardcode"}


@pytest.fixture
def book(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Model"
    ws.append(["Line", "Y1", "Y2", "Y3", "Y4"])
    ws.append(["Revenue", 100, "=B2*1.1", 125, "=D2*1.1"])
    ws.append(["Costs", 60, "=B3*1.05", "=C3*1.05", "=D3*1.05"])
    ws.append(["Profit", "=B2-B3", "=C2-C3", "=D2-D3", "=E2-E3"])
    ws["A6"], ws["B6"] = "Tax rate", 0.25
    wb.save(tmp_path / "raw.xlsx")
    if not shutil.which("soffice"):
        pytest.skip("LibreOffice is needed for cached values")
    (tmp_path / "calc").mkdir()
    rw2.gt.recalc([tmp_path / "raw.xlsx"], tmp_path / "calc")      # cached values, as in a real file
    return rw2.Book(tmp_path / "calc" / "raw.xlsx")


def test_labels_name_a_cell_by_its_row_and_column(book):
    lab = rw2.Labels(book.v["Model"])
    assert lab.name(2, 2) == ("Revenue", "Y1")
    assert lab.name(6, 2) == ("Tax rate", "Y1")


def test_candidates_follow_the_rules(book):
    c = rw2.candidates(book)
    assert c["address"] is c["lookup"]
    assert "Model!B2" in {x["cell"] for x in c["lookup"]}
    traces = {x["cell"] for x in c["trace"]}
    assert "Model!B4" in traces and "Model!C2" not in traces          # C2 reads one cell only
    assert "Model!B2" in {x["cell"] for x in c["impact"]}             # a typed number some formula reads
    runs = {x["range"]: x["mixed"] for x in c["hardcode"]}
    assert runs["Model!B2:E2"] is True and runs["Model!B4:E4"] is False


def test_hardcode_truth_lists_the_typed_numbers_of_the_run(book, tmp_path):
    cand = next(x for x in rw2.candidates(book)["hardcode"] if x["range"] == "Model!B2:E2")
    q = rw2.question("hardcode", cand, book, None, tmp_path, "t", 1)
    assert q["truth"] == ["Model!B2", "Model!D2"] and score.score(q, q["truth"])["score"] == 1.0


def test_questions_are_reproducible(book, tmp_path):
    a = rw2.make_questions(book, None, "rw2_t", tmp_path, impact=False)
    b = rw2.make_questions(book, None, "rw2_t", tmp_path, impact=False)
    assert a == b and [q["type"] for q in a] == [t for t, n in rw2.PLAN for _ in range(n)]


needs_set = pytest.mark.skipif(not HAVE, reason="the benchmark set is not built yet")


@needs_set
def test_the_set_is_complete_and_its_sources_are_pinned():
    man = json.loads((RW2 / "manifest.json").read_text())["workbooks"]
    assert set(SEL) == set(man) == {p.stem for p in (RW2 / "questions").glob("*.json")}
    assert sum(e["source"] == "enron" for e in SEL.values()) >= 10
    assert sum(e["source"] == "damodaran" for e in SEL.values()) >= 10
    for name, e in SEL.items():
        assert name.startswith("rw2_") and len(e["sha256"]) == 64 and e["licence"]
        if e["source"] == "enron":
            assert rw2.sha256(RW2 / "sources" / e["file"]) == e["sha256"]


@needs_set
@pytest.mark.parametrize("name", sorted(SEL))
def test_questions_are_well_formed_and_a_perfect_answer_scores_one(name):
    qs = json.loads((RW2 / "questions" / f"{name}.json").read_text())
    assert [q["id"] for q in qs] == [f"q{i}" for i in range(1, len(qs) + 1)]
    for q in qs:
        assert q["type"] in TYPES and q["truth"] is not None
        if q["type"] in ("trace", "impact"):
            assert q["truth"] and q["cell"] not in q["truth"]
        assert score.score(q, q["truth"])["score"] == 1.0


@needs_set
def test_the_set_has_the_planned_question_mix():
    qs = [q for n in SEL for q in json.loads((RW2 / "questions" / f"{n}.json").read_text())]
    count = {t: sum(q["type"] == t for q in qs) for t in TYPES}
    assert count["trace"] >= 30 and count["impact"] >= 15 and count["hardcode"] >= 15


@needs_set
def test_benchmark_workbooks_are_held_out():
    sp = splitmod.load()
    names = sorted(SEL)
    with pytest.raises(SystemExit):
        splitmod.select(None, None, names, False, None, 1, sp)
    assert splitmod.select(None, None, names, True, None, 1, sp) == names


@needs_set
@pytest.mark.parametrize("name", sorted(n for n, e in SEL.items() if e["source"] == "enron"))
def test_ground_truth_recomputes_from_the_committed_enron_files(name, tmp_path):
    e = SEL[name]
    src = RW2 / "sources" / e["file"]
    new = rw2.make_questions(rw2.Book(src), src, name, tmp_path, impact=False)
    old = json.loads((RW2 / "questions" / f"{name}.json").read_text())
    for n, o in zip(new, old):       # impact is skipped: without LibreOffice the first candidate stands in for it
        assert n["type"] == o["type"]
        if n["type"] != "impact":
            assert (n["cell"], n["q"], n["truth"]) == (o["cell"], o["q"], o["truth"]), (name, o["id"])


def test_score_empty_truth_needs_a_given_answer():
    """A missing or failed answer must not score 1.0 on a hardcode question whose truth is empty."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))
    import score
    q = {"id": "q6", "type": "hardcode", "cell": "S!D86", "truth": []}
    assert score.score(q, None)["score"] == 0.0
    assert score.score(q, [])["score"] == 1.0


def test_score_quoted_sheet_with_apostrophe():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))
    import score
    q = {"id": "q2", "type": "address", "cell": "Original OBA's!B3", "truth": "Original OBA's!B3"}
    assert score.score(q, "'Original OBA''s'!B3")["score"] == 1.0
    assert score.score(q, "Original OBA's!B3")["score"] == 1.0


@needs_set
def test_set_has_163_questions():
    """The set has 163 questions; ids stay q1..qN in every file."""
    total = sum(len(json.loads(f.read_text())) for f in (RW2 / "questions").glob("*.json"))
    assert total == 163
