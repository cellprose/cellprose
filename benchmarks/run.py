"""Run every (model, workbook, encoding) combination through the Claude CLI, headless, no tools.

Each call holds one encoded workbook and all of that workbook's questions; the
model returns one JSON object. Raw results land in results/raw/<model>/.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from encoders import ENCODINGS
from runner.prompts import KIND, LABEL, SYSTEM, prompt  # noqa: F401  # shared with the API runner)

ROOT = Path(__file__).parent
RAW = ROOT / "results" / "raw"
MODELS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["haiku", "sonnet", "opus"]
ENCS = __import__("os").environ["ENCS"].split(",") if "ENCS" in __import__("os").environ else ENCODINGS + ["none"]


REP = int(__import__("os").environ.get("REP", "0"))


def call(model, wb, enc):
    out = RAW / model / (f"{wb}.{enc}.json" if REP == 0 else f"{wb}.{enc}.r{REP}.json")
    if out.exists():
        return out, "cached"
    p = prompt(wb, enc)
    for attempt in range(3):
        try:
            r = subprocess.run(["claude", "-p", "--model", model, "--system-prompt", SYSTEM, "--tools", "",
                                "--no-session-persistence", "--output-format", "json"],
                               input=p, capture_output=True, text=True, timeout=600,
                               cwd=__import__("tempfile").gettempdir())
            d = json.loads(r.stdout)
            if d.get("is_error"):
                raise RuntimeError(d.get("result"))
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"model": model, "workbook": wb, "encoding": enc, "prompt_chars": len(p),
                                       "result": d["result"], "usage": d["usage"],
                                       "modelUsage": d.get("modelUsage"), "cost": d.get("total_cost_usd")}, indent=1))
            return out, "ok"
        except Exception as e:
            err = f"{type(e).__name__}: {e} | {r.stderr[-300:] if 'r' in dir() else ''}"
    return out, "FAILED " + err


if __name__ == "__main__":
    wbs = sorted(p.stem for p in (ROOT / "questions").glob("*.json"))
    jobs = [(m, w, e) for m in MODELS for w in wbs for e in ENCS]
    done = 0
    with ThreadPoolExecutor(8) as ex:
        futs = [ex.submit(call, *j) for j in jobs]
        for f in as_completed(futs):
            out, status = f.result()
            done += 1
            print(f"[{done}/{len(jobs)}] {out.parent.name}/{out.name} {status}", flush=True)
