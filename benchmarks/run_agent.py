"""Agent mode: the model gets a file in an empty folder plus Bash and Read tools, and explores until it answers.

Variants:
  agent_xlsx       — ./book.xlsx (recalculated, cached values present); python3 + openpyxl available
  agent_sheetmark  — ./book.sheet.md (lean Sheetmark)
Same questions and answer rules as run.py. Usage is summed over every turn.
"""
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from run import KIND

ROOT = Path(__file__).parent
RAW = ROOT / "results" / "raw"
WORK = Path(__import__("tempfile").gettempdir()) / "sheetmark_agent_runs"
MODELS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["haiku", "sonnet"]
VARIANTS = {"agent_xlsx": "book.xlsx", "agent_sheetmark": "book.sheet.md"}
SYSTEM = ("You answer questions about a spreadsheet workbook stored as a file in the current folder. "
          "Use the tools to inspect it (python3 with openpyxl is installed). "
          "When done, reply with a single JSON object and nothing else.")


def prompt(wb, fname):
    qs = json.loads((ROOT / "questions" / f"{wb}.json").read_text())
    parts = [f"The workbook is ./{fname}.\n",
             "Answer each question. Rules:\n"
             "- Cell addresses use A1 notation qualified with the sheet name, e.g. Sheet1!B5.\n"
             "- For list questions, return a JSON array of cell addresses; ranges like Sheet1!B2:B9 are allowed. "
             "Return [] if there are none.\n"
             "- For value questions, return a number without units or thousands separators, or a short string.\n"
             "- If the workbook does not give enough information, give your best guess.\n\nQuestions:"]
    for q in qs:
        parts.append(f"{q['id']} ({KIND[q['type']]}): {q['q']}")
    parts.append('\nReturn JSON like {"q1": ..., "q2": ...} with every question id.')
    return "\n".join(parts)


REP = int(__import__("os").environ.get("REP", "0"))


def call(model, wb, variant):
    out = RAW / model / (f"{wb}.{variant}.json" if REP == 0 else f"{wb}.{variant}.r{REP}.json")
    if out.exists():
        return out, "cached"
    fname = VARIANTS[variant]
    d = WORK / f"{model}.{wb}.{variant}.r{REP}"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    if variant == "agent_xlsx":
        shutil.copy(ROOT / "workbooks" / f"{wb}.xlsx", d / fname)
    else:
        shutil.copy(ROOT / "encoded" / f"{wb}.sheetmark_lean_gfm.txt", d / fname)
    err = ""
    for attempt in range(2):
        try:
            r = subprocess.run(["claude", "-p", "--model", model, "--system-prompt", SYSTEM,
                                "--tools", "Bash,Read", "--allowedTools", "Bash,Read",
                                "--permission-mode", "bypassPermissions", "--max-turns", "40",
                                "--no-session-persistence", "--output-format", "json"],
                               input=prompt(wb, fname), capture_output=True, text=True, timeout=1500, cwd=d)
            res = json.loads(r.stdout)
            if res.get("is_error") and res.get("subtype") == "success":
                raise RuntimeError(res.get("result"))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"model": model, "workbook": wb, "encoding": variant,
                                       "result": res.get("result", ""), "usage": res["usage"],
                                       "modelUsage": res.get("modelUsage"), "cost": res.get("total_cost_usd"),
                                       "num_turns": res.get("num_turns"), "subtype": res.get("subtype")}, indent=1))
            return out, f"ok turns={res.get('num_turns')}"
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
    return out, "FAILED " + err


if __name__ == "__main__":
    wbs = sorted(p.stem for p in (ROOT / "questions").glob("*.json"))
    jobs = [(m, w, v) for m in MODELS for w in wbs for v in VARIANTS]
    with ThreadPoolExecutor(6) as ex:
        futs = [ex.submit(call, *j) for j in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            o, s = f.result()
            print(f"[{i}/{len(jobs)}] {o.parent.name}/{o.name} {s}", flush=True)
