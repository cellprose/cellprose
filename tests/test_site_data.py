"""The website's benchmark numbers (site/data/benchmarks.json) agree with the published headline (headline_r1r2.json)."""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
SITE = json.loads((ROOT / "site" / "data" / "benchmarks.json").read_text())
HEAD = json.loads((ROOT / "benchmarks" / "results" / "headline_r1r2.json").read_text())


def test_site_numbers_match_the_headline():
    checked = 0
    for st in ("all", "standard", "hard"):
        head = {(r["model"], r["encoding"]): r for r in HEAD[st]}
        for r in SITE["sets"][st]["mean"]:
            h = head[(r["model"], r["encoding"])]
            assert r["acc"] == round(h["acc"], 1), (st, r)
            assert r["cpc_vs"] == int(h["cost_per_correct_vs"]), (st, r)
            assert r["tokens_vs"] == int(h["tokens_vs"]), (st, r)
            checked += 1
    assert checked == 3 * 2 * 4


def test_site_shows_both_repeats_and_an_interval_per_baseline():
    assert SITE["reps"] == ["r1", "r2"]
    for entry in SITE["sets"].values():
        assert set(entry["by_rep"]) == {"r1", "r2"}
        assert {(i["model"], i["baseline"]) for i in entry["interval"]} == {
            (m, b) for m in ("haiku", "sonnet") for b in ("csv", "markdown", "toon")}
        for i in entry["interval"]:
            assert i["lo"] <= i["ratio"] <= i["hi"]
