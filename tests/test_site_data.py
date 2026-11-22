"""The home page's replay (site/data/benchmarks.json) is the recorded E38 call, as benchmarks/site_data.py writes it."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
SITE = json.loads((ROOT / "site" / "data" / "benchmarks.json").read_text())
E38 = ROOT / "benchmarks" / "results" / "e38_replay"


def test_replay_is_the_recorded_v03_call():
    r = SITE["replay"]
    assert [l["encoding"] for l in r["lanes"]] == ["csv", "cellprose_v03"]
    with open(E38 / "scores.csv", newline="") as f:
        scores = [s for s in csv.DictReader(f) if s["workbook"] == r["workbook"] and s["qid"] == "q3"]
    for lane in r["lanes"]:
        raw = json.loads((E38 / "raw" / "haiku55" / f"{r['workbook']}.{lane['encoding']}.json").read_text())
        assert lane["tout"] == raw["usage"]["output_tokens"]
        (s,) = [s for s in scores if s["encoding"] == lane["encoding"]]
        assert lane["score"] == float(s["score"]) and lane["answer"] == json.loads(s["answer"])


def test_no_v02_tables_left():
    assert set(SITE) == {"labels", "replay"}
    assert "sheetmark_lean_gfm" not in SITE["labels"]
