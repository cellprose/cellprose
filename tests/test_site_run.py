"""site/data/run.json (written by benchmarks/site_run.py) agrees with benchmarks/RESULTS.md, table by table."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))
RUN = json.loads((ROOT / "site" / "data" / "run.json").read_text())
TXT = (ROOT / "benchmarks" / "RESULTS.md").read_text()
NAMES = {v: k for k, v in RUN["models"].items()}
BASE = {"MarkItDown": "markitdown", "CSV": "csv", "Agent + shell": "agent_xlsx", "Agent + viewer": "agent_xlsx_viewer"}


def section(head):
    return TXT.split(head, 1)[1].split("\n#", 1)[0]


def test_every_arm_table_matches():
    n = 0
    for corpus, head in (("realworld", "### Real-world: every arm"), ("spreadsheetbench", "### SpreadsheetBench: every arm")):
        arms = {(a["model"], a["arm"]): a for a in RUN["corpora"][corpus]["arms"]}
        for m in re.finditer(r"^\| (.+?) \| `(\w+)` \| ([\d.]+)% \| ([\d,]+) \| \$([\d.]+) \| \$([\d.]+) \| ([\d.]+) \|",
                             section(head), re.M):
            a = arms[(NAMES[m.group(1)], m.group(2))]
            assert (a["acc"], a["tokens"], a["cost"], a["cost_per_correct"], a["turns"]) == (
                float(m.group(3)), int(m.group(4).replace(",", "")), float(m.group(5)), float(m.group(6)),
                float(m.group(7))), m.group(0)
            n += 1
    assert n == 2 * 4 * 6


def _check_verdicts(head, verdicts, arm):
    got = {(v["model"], v["baseline"]): v for v in verdicts if v["arm"] == arm}
    n = 0
    for m in re.finditer(r"^\| (.+?) \| (MarkItDown|CSV|Agent \+ shell|Agent \+ viewer) \| ([\d.]+)% / ([\d.]+)% \| "
                         r"([\d.]+) \[([\d.]+), ([\d.]+)\] \| (win|loss|no difference) \|", section(head), re.M):
        v = got[(NAMES[m.group(1)], BASE[m.group(2)])]
        assert (v["acc"], v["acc_baseline"], v["ratio"], v["lo"], v["hi"], v["verdict"]) == (
            float(m.group(3)), float(m.group(4)), float(m.group(5)), float(m.group(6)), float(m.group(7)),
            m.group(8)), m.group(0)
        n += 1
    return n


def test_verdict_tables_match():
    assert _check_verdicts("### Real-world: verdicts", RUN["corpora"]["realworld"]["verdicts"], "cellprose_v03") == 16
    assert _check_verdicts("### SpreadsheetBench: verdicts", RUN["corpora"]["spreadsheetbench"]["verdicts"],
                           "cellprose_v03") == 16
    views = RUN["addendum"]["views"]
    assert _check_verdicts("#### Real-world, primary verdict", views["realworld_primary"]["verdicts"],
                           "agent_cellprose_lean") == 8


def test_run_json_is_rebuilt_from_results():
    from site_run import build  # benchmarks/ is not a package; CI does not put the repo root on sys.path
    assert build() == RUN


def test_nothing_is_a_loss_and_intervals_are_ordered():
    every = [v for c in RUN["corpora"].values() for v in c["verdicts"]]
    every += [v for view in RUN["addendum"]["views"].values() for v in view["verdicts"]]
    assert every and all(v["verdict"] != "loss" for v in every)
    assert all(v["lo"] <= v["ratio"] <= v["hi"] for v in every)
