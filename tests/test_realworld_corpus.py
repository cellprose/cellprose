"""Backlog B9: the real-world question set (benchmarks/external/realworld/).

Checks that run everywhere: the questions are well formed, a perfect answer scores 1, the workbooks are fenced as held
out, and the manifest matches the pinned source hashes. Checks that need the source workbooks recompute the ground
truth from the files (lookup, address, trace) and compare it with what is committed; the Damodaran models are not in git,
so those are skipped unless CELLPROSE_REAL_FILES (or the project folder) has them."""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "benchmarks"
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(BENCH / "external"))
import realworld  # noqa: E402
import score  # noqa: E402
from runner import split as splitmod  # noqa: E402

RW = BENCH / "external" / "realworld"
SPEC = json.loads((RW / "spec.json").read_text())["workbooks"]
MANIFEST = json.loads((RW / "manifest.json").read_text())["workbooks"]
SOURCES = realworld.source_manifest()
TYPES = {"lookup", "address", "trace", "impact"}


def questions(name):
    return json.loads((RW / "questions" / f"{name}.json").read_text())


def test_every_workbook_has_questions_a_manifest_entry_and_a_pinned_source():
    assert set(SPEC) == set(MANIFEST) == {p.stem for p in (RW / "questions").glob("*.json")}
    assert 10 <= len(SPEC) <= 20, "docs/PROTOCOL.md section 3 asks for 10-20 real-world workbooks"
    for name, entry in MANIFEST.items():
        src = SOURCES[SPEC[name]["file"]]
        assert entry["sha256"] == src["sha256"] and entry["licence"] == src["licence"]
        assert entry["committed_in_git"] == (ROOT / "tests" / "real" / SPEC[name]["file"]).exists()


@pytest.mark.parametrize("name", sorted(SPEC))
def test_questions_are_well_formed_and_a_perfect_answer_scores_one(name):
    qs = questions(name)
    assert [q["id"] for q in qs] == [f"q{i}" for i in range(1, len(qs) + 1)]
    assert len({q["q"] for q in qs}) == len(qs)
    for q in qs:
        assert q["type"] in TYPES and q["truth"] not in (None, [], "")
        assert "!" in q["cell"]
        if q["type"] == "impact":
            assert q["factor"] > 0 and q["cell"] not in q["truth"]
        if q["type"] == "address":
            assert q["truth"] == q["cell"]
        assert score.score(q, q["truth"])["score"] == 1.0


def test_the_set_covers_every_question_type_and_mixes_formula_and_data_workbooks():
    types = {q["type"] for n in SPEC for q in questions(n)}
    assert types == TYPES
    assert sum(1 for e in MANIFEST.values() if e["formula_cells"] > 50) >= 4      # formula-heavy models
    assert sum(1 for e in MANIFEST.values() if e["formula_cells"] == 0) >= 8      # plain data tables
    assert sum(len(questions(n)) for n in SPEC) >= 60


def test_real_world_workbooks_are_held_out():
    sp = splitmod.load()
    allwb = sorted(p.stem for p in (RW / "questions").glob("*.json"))
    with pytest.raises(SystemExit):
        splitmod.select(None, None, allwb, False, None, 1, sp)           # no --final: refused
    assert splitmod.select(None, None, allwb, True, None, 1, sp) == allwb


def available(name):
    entry = SOURCES[SPEC[name]["file"]]
    try:
        realworld.find_source(entry, None, Path("/nonexistent"))
        return True
    except SystemExit:
        return False


@pytest.mark.parametrize("name", sorted(SPEC))
def test_ground_truth_recomputes_from_the_workbook(name, tmp_path):
    if not available(name):
        pytest.skip(f"source file for {name} not available (set CELLPROSE_REAL_FILES)")
    src = realworld.find_source(SOURCES[SPEC[name]["file"]], None, tmp_path)
    old = questions(name)
    new = realworld.make_questions(realworld.Book(src), SPEC[name], src, name, tmp_path, with_impact=False)
    assert len(new) == len(old)
    for n, o in zip(new, old):
        assert (n["type"], n["q"], n["cell"]) == (o["type"], o["q"], o["cell"])
        if n["truth"] is not None:
            assert n["truth"] == o["truth"], (name, o["id"])
