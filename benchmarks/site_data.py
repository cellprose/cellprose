"""The home page's replay for the website, as site/data/benchmarks.json.

One recorded call per format (E38, on the v0.3 text), with its token counts, answer and score. Every other benchmark
number on the site comes from the 11 Nov 2026 run, through site_run.py and site/data/run.json. This file used to also
carry the earlier v0.2 tables (E09); nothing on the site showed them any more, so they were dropped.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT.parent / "site" / "data" / "benchmarks.json"
LABELS = {"csv": "CSV", "cellprose_v03": "Cellprose v0.3"}
data = {"labels": LABELS}

# One recorded call per format for the home page's replay: workbook 11, Haiku 5.5, the question on C4:M5. It was picked
# to show the kind of miss values-only formats make, so the site labels it as one illustrative call, not a typical one.
# Recorded on 2026-11-21 on the v0.3 text (results/e38_replay/, E38): one invocation, one repeat, CSV and cellprose_v03.
REPLAY_DIR = ROOT / "results" / "e38_replay"
REPLAY_WB, REPLAY_Q, REPLAY_ENCS = "11_forecast_overrides", "q3", ("csv", "cellprose_v03")
questions = {q["id"]: q for q in json.loads((ROOT / "questions" / f"{REPLAY_WB}.json").read_text())}
data["replay"] = {"workbook": REPLAY_WB, "model": "haiku", "rep": "r0", "question": questions[REPLAY_Q]["q"],
                  "truth": questions[REPLAY_Q]["truth"], "lanes": []}
with open(REPLAY_DIR / "scores.csv", newline="") as f:
    rs = [r for r in csv.DictReader(f) if r["workbook"] == REPLAY_WB and r["model"] == "haiku55"]
for enc in REPLAY_ENCS:
    raw = json.loads((REPLAY_DIR / "raw" / "haiku55" / f"{REPLAY_WB}.{enc}.json").read_text())
    u = raw["usage"]
    sc = [r for r in rs if r["encoding"] == enc]
    q = next(r for r in sc if r["qid"] == REPLAY_Q)
    data["replay"]["lanes"].append({
        "encoding": enc,
        "tin": u["input_tokens"] + u["cache_read_input_tokens"] + u["cache_creation_input_tokens"],
        "tout": u["output_tokens"], "questions_in_call": len(sc),
        "answer": json.loads(q["answer"]),     # as score.py parsed it from the reply
        "score": float(q["score"])})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
print(f"wrote {OUT}")
