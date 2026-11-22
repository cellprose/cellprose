"""Reproduce the numbers in docs/DESIGN.md.

Uses only repeats r1 and r2, which ran in the same session for every format. Repeat r0 is excluded because
Haiku's first-session runs spent ~5x more reasoning tokens on identical prompts. Cost prices every input
token as uncached (see analyze.usage) so prompt-cache hits on repeated prompts don't distort it.
Run score.py first.
"""
import json
import os
from pathlib import Path

import pandas as pd

from analyze import df, table
from limitations import block

ROOT = Path(__file__).parent
RESULTS = Path(os.environ.get("RESULTS_DIR") or ROOT / "results")
REPS = ["r1", "r2"]
FORMATS = ["csv", "markdown", "toon", "sheetmark", "sheetmark_lean_gfm"]  # sheetmark_lean_gfm = v0.2

d = df[df.rep.isin(REPS)]
res = {}
pd.set_option("display.width", 250)
cols = ["model", "encoding", "n", "acc", "tokens", "tokens_vs", "tout_vs", "cost", "cost_vs", "cost_per_correct_vs"]
for st in ("standard", "hard", "all"):
    sub = d[d.encoding.isin(FORMATS)]
    if st != "all":
        sub = sub[sub.set == st]
    res[st] = table(sub, "csv")
    print(f"\n== one-shot, {st} workbooks, vs CSV\n", res[st][cols].round(4).to_string(index=False))
ag = d[d.encoding.isin(["agent_xlsx", "agent_sheetmark", "sheetmark_lean_gfm"])]
res["agent"] = table(ag, "agent_xlsx")
print("\n== agent mode, vs raw .xlsx with tools\n", res["agent"][cols + ["turns"]].round(4).to_string(index=False))

s = pd.read_csv(RESULTS / "scores.csv")
s = s[s.rep.isin(REPS) & s.encoding.isin(FORMATS + ["agent_xlsx", "agent_sheetmark"])]
print("\n== accuracy by task (%), both models\n", s.groupby(["encoding", "task"]).score.mean().unstack().mul(100).round(1))

print("\n" + block())

(RESULTS / "headline_r1r2.json").write_text(
    json.dumps({k: v.to_dict(orient="records") for k, v in res.items()}, indent=1, default=float))
