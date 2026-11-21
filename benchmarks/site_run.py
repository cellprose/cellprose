"""The 11 Nov 2026 benchmark run and Addendum A, for the website, as site/data/run.json.

Reads only committed result files (no recomputation): each corpus's verdicts.json (paired bootstrap verdicts),
headline.json (mean per call over the 3 repeats) and summary.csv (accuracy by question type), and the same for the
addendum. Every number on the site's benchmark page comes from here; tests/test_site_run.py checks the file against
the result files and against the tables in benchmarks/RESULTS.md.

    python3 site_run.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent
RES = ROOT / "results"
OUT = ROOT.parent / "site" / "data" / "run.json"

MODELS = {"haiku55": "Claude Haiku 5.5", "sonnet55": "Claude Sonnet 5.5", "gpt6luna": "GPT-6 Luna", "gpt61sol": "GPT-6.1 Sol"}
LABELS = {"cellprose_v03": "Cellprose in the prompt", "markitdown": "MarkItDown", "csv": "CSV",
          "agent_xlsx": "Agent + shell on .xlsx", "agent_xlsx_viewer": "Agent + formula viewer",
          "agent_cellprose_v03": "Agent + shell on Cellprose file", "agent_cellprose_lean": "Cellprose with its own tools",
          "none": "No workbook (guess)"}
ARMS = ["cellprose_v03", "markitdown", "csv", "agent_xlsx", "agent_xlsx_viewer", "agent_cellprose_v03"]
TASKS = ["lookup", "address", "trace", "impact", "hardcode"]
CORPORA = {
    "realworld": {"label": "Real-world", "dir": "run_rw2", "workbooks": 30, "questions": 163,
                  "about": "15 Damodaran valuation models and 15 Enron trading workbooks; five question types"},
    "spreadsheetbench": {"label": "SpreadsheetBench", "dir": "run_sb", "workbooks": 28, "questions": 111,
                         "about": "SpreadsheetBench tasks restated as value questions; no formulas to trace"},
}
ADDENDUM = {"realworld_primary": ("addendum_rw2_noimpact", "Real-world, primary (impact questions left out)"),
            "realworld_all": ("addendum_rw2", "Real-world, all questions"),
            "spreadsheetbench": ("addendum_sb", "SpreadsheetBench")}


def load(d: str, name: str):
    return json.loads((RES / d / name).read_text())


def verdicts(d: str) -> list[dict]:
    out = []
    for v in load(d, "verdicts.json"):
        if v["set"] != "held_out":
            continue
        out.append({"model": v["model"], "arm": v["encoding"], "baseline": v["baseline"],
                    "acc": round(100 * v["acc"], 1), "acc_baseline": round(100 * v["acc_baseline"], 1),
                    "ratio": round(v["ratio"], 2), "lo": round(v["ratio_lo"], 2), "hi": round(v["ratio_hi"], 2),
                    "verdict": v["verdict"]})
    return out


def question_acc(d: str) -> dict:
    """Question-averaged accuracy per (model, arm), as in RESULTS.md's arm tables (verdicts are workbook-averaged)."""
    p = RES / d / "summary.csv"
    if not p.exists():
        return {}
    with open(p) as f:
        return {(r["model"], r["encoding"]): float(r["all"]) for r in csv.DictReader(f) if r["set"] == "all"}


def arms(d: str) -> list[dict]:
    h, qa = load(d, "headline.json"), question_acc(d)
    seen, out = set(), []
    for r in h.get("agent", []) + h.get("oneshot_all", []):
        k = (r["model"], r["encoding"])
        if k in seen:
            continue
        seen.add(k)
        acc = qa.get(k, r["acc"])
        out.append({"model": r["model"], "arm": r["encoding"], "acc": round(acc, 1), "tokens": round(r["tokens"]),
                    "cost": round(r["cost"], 4), "cost_per_correct": round(r["cost"] / (acc / 100), 4) if acc else None,
                    "turns": round(r.get("turns", 1.0), 1)})
    return out


def tasks(d: str) -> tuple[list[dict], dict]:
    rows, none = [], {}
    with open(RES / d / "summary.csv") as f:
        for r in csv.DictReader(f):
            if r["set"] != "all":
                continue
            if r["encoding"] == "none":
                none[r["model"]] = float(r["all"])
                continue
            rows.append({"model": r["model"], "arm": r["encoding"],
                         **{t: (float(r[t]) if r.get(t) else None) for t in TASKS}})
    return rows, none


def build() -> dict:
    data = {"date": "2026-11-11", "models": MODELS, "model_order": list(MODELS), "labels": LABELS, "arms": ARMS, "tasks": TASKS, "repeats": 3,
            "corpora": {}, "addendum": {"repeats": 2, "views": {}}}
    for key, c in CORPORA.items():
        t, none = tasks(c["dir"])
        data["corpora"][key] = {k: v for k, v in c.items() if k != "dir"} | {
            "verdicts": verdicts(c["dir"]), "arms": arms(c["dir"]), "by_task": t, "none": none}
    for key, (d, label) in ADDENDUM.items():
        data["addendum"]["views"][key] = {"label": label, "verdicts": verdicts(d), "arms": arms(d)}
    return data


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT}")
