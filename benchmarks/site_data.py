"""Benchmark numbers for the website, as site/data/benchmarks.json.

The same data as report.py (repeats r1 and r2, same session, every input token priced as uncached), plus what the
site shows next to each headline number: the two repeats separately, the 95% paired bootstrap interval of
docs/PROTOCOL.md section 7, and accuracy by task with its question count. Run score.py first.

Importing analyze also rewrites results/headline.json and writes verdicts.json as a side effect; delete both
(neither is tracked) if you only wanted the site data.
"""
import json
import os
from pathlib import Path

import pandas as pd

from analyze import df, table
from stats import comparisons

ROOT = Path(__file__).parent
RESULTS = Path(os.environ.get("RESULTS_DIR") or ROOT / "results")
OUT = ROOT.parent / "site" / "data" / "benchmarks.json"
REPS = ["r1", "r2"]
FORMATS = ["csv", "markdown", "toon", "sheetmark_lean_gfm"]          # sheetmark_lean_gfm = v0.2
LABELS = {"csv": "CSV", "markdown": "Markdown table", "toon": "TOON", "sheetmark_lean_gfm": "Cellprose v0.2",
          "agent_xlsx": "Raw .xlsx with tools", "agent_sheetmark": "Cellprose file with tools"}
MODELS = {"haiku": "Haiku 5.5", "sonnet": "Sonnet 5.5"}


def rows(t, keep):
    out = []
    for r in t.to_dict(orient="records"):
        if r["encoding"] in keep:
            out.append({"model": r["model"], "encoding": r["encoding"], "n": int(r["n"]), "acc": round(float(r["acc"]), 1),
                        "tin": round(float(r["tin"])), "tout": round(float(r["tout"])),
                        "turns": round(float(r["turns"]), 2), "cpc_vs": int(r["cost_per_correct_vs"]),
                        "tokens_vs": int(r["tokens_vs"]), "tout_vs": int(r["tout_vs"])})
    return out


d = df[df.rep.isin(REPS)]
one = d[d.encoding.isin(FORMATS)]
data = {"reps": REPS, "labels": LABELS, "models": MODELS, "sets": {}, "agent": [], "tasks": {}}
for st in ("all", "standard", "hard"):
    sub = one if st == "all" else one[one.set == st]
    entry = {"workbooks": int(sub.workbook.nunique()), "mean": rows(table(sub, "csv"), FORMATS), "by_rep": {}, "interval": []}
    for r in REPS:
        entry["by_rep"][r] = rows(table(sub[sub.rep == r], "csv"), FORMATS)
    for c in comparisons(sub, "sheetmark_lean_gfm", ["csv", "markdown", "toon"]):
        entry["interval"].append({"model": c["model"], "baseline": c["baseline"], "n_workbooks": c["n_workbooks"],
                                  "ratio": round(c["ratio"], 4), "lo": round(c["ratio_lo"], 4), "hi": round(c["ratio_hi"], 4),
                                  "verdict": c["verdict"]})
    data["sets"][st] = entry
ag = d[d.encoding.isin(["agent_xlsx", "agent_sheetmark", "sheetmark_lean_gfm"])]
ag = ag[ag.workbook.isin(d[d.encoding == "agent_xlsx"].workbook)]
data["agent"] = rows(table(ag, "agent_xlsx"), ["agent_xlsx", "agent_sheetmark", "sheetmark_lean_gfm"])

s = pd.read_csv(RESULTS / "scores.csv")
s = s[s.rep.isin(REPS) & s.encoding.isin(FORMATS)]
for (enc, task), g in s.groupby(["encoding", "task"]):
    data["tasks"].setdefault(enc, {})[task] = {"acc": round(100 * g.score.mean(), 1), "n": int(len(g))}

# One recorded call per format for the home page's replay: workbook 11, Haiku 5.5, the question on C4:M5. It was picked
# to show the kind of miss values-only formats make, so the site labels it as one illustrative call, not a typical one.
# Recorded on 2026-11-21 on the v0.3 text (results/e38_replay/, E38): one invocation, one repeat, CSV and cellprose_v03.
REPLAY_DIR = ROOT / "results" / "e38_replay"
REPLAY_WB, REPLAY_Q, REPLAY_ENCS = "11_forecast_overrides", "q3", ("csv", "cellprose_v03")
questions = {q["id"]: q for q in json.loads((ROOT / "questions" / f"{REPLAY_WB}.json").read_text())}
data["replay"] = {"workbook": REPLAY_WB, "model": "haiku", "rep": "r0", "question": questions[REPLAY_Q]["q"],
                  "truth": questions[REPLAY_Q]["truth"], "lanes": []}
rs = pd.read_csv(REPLAY_DIR / "scores.csv")
for enc in REPLAY_ENCS:
    raw = json.loads((REPLAY_DIR / "raw" / "haiku55" / f"{REPLAY_WB}.{enc}.json").read_text())
    u = raw["usage"]
    sc = rs[(rs.workbook == REPLAY_WB) & (rs.model == "haiku55") & (rs.encoding == enc)]
    data["replay"]["lanes"].append({
        "encoding": enc,
        "tin": u["input_tokens"] + u["cache_read_input_tokens"] + u["cache_creation_input_tokens"],
        "tout": u["output_tokens"], "questions_in_call": int(len(sc)),
        "answer": json.loads(sc[sc.qid == REPLAY_Q].answer.iloc[0]),     # as score.py parsed it from the reply
        "score": float(sc[sc.qid == REPLAY_Q].score.iloc[0])})
data["labels"]["cellprose_v03"] = "Cellprose v0.3"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
print(f"wrote {OUT}")
