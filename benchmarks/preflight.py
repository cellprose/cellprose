"""Preflight for the benchmark run (docs/PROTOCOL.md section 8): one call per model and arm on one small development
workbook, before the paid run starts. It checks that every key works and has credit, that every model answers in
every arm, that the returned model is the one requested, and that Anthropic agent turns read from the prompt cache.
Its results are never scored with the benchmark; they go to their own directory.

    python preflight.py --estimate-only      # what it would cost
    python preflight.py                      # run it (a few dollars at most; --max-usd guards it)
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import api_agent
import api_run

ROOT = Path(__file__).parent
MODELS = "haiku55,sonnet55,gpt6luna,gpt61sol"
WORKBOOK = "01_sales_log"                       # small, development data (benchmarks/split.json)
ONE_SHOT = "cellprose_v03,markitdown,csv"       # `none` needs no check beyond what these give
AGENT = "agent_xlsx,agent_xlsx_viewer,agent_cellprose_v03"


def check(out: Path) -> list[str]:
    """Problems found in the raw files of a preflight; an empty list means it passed."""
    problems = []
    expected = {(m, arm) for m in MODELS.split(",") for arm in ONE_SHOT.split(",") + AGENT.split(",")}
    seen = set()
    for f in sorted((out / "raw").rglob("*.json")):
        d = json.loads(f.read_text())
        key = (d["model"], d["encoding"])
        seen.add(key)
        name = f"{d['model']}/{d['encoding']}"
        if d.get("failed"):
            problems.append(f"{name}: failed ({d['failure']['kind']}: {d['failure']['message'][:120]})")
        if d["run"].get("returned_model") and not str(d["run"]["returned_model"]).startswith(d["run"]["requested_model"]):
            problems.append(f"{name}: asked for {d['run']['requested_model']}, got {d['run']['returned_model']}")
        if d["provider"] == "anthropic" and d["encoding"].startswith("agent_") and d.get("num_turns", 0) >= 3:
            if not d["usage"]["cache_read_input_tokens"]:
                problems.append(f"{name}: {d['num_turns']} turns and no cache reads; caching is not working")
    problems += [f"{m}/{arm}: no result" for m, arm in sorted(expected - seen)]
    for log in sorted((out / "runs").glob("*.infra.jsonl")):
        problems += [f"infrastructure failure: {json.loads(line)['model']}/{json.loads(line)['arm']}: "
                     f"{json.loads(line)['message'][:120]}" for line in log.read_text().splitlines()]
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("--out", help="default results/preflight/<UTC time>")
    ap.add_argument("--max-usd", type=float, default=5.0)
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else ROOT / "results" / "preflight" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    common = ["--models", MODELS, "--workbooks", WORKBOOK, "--out", str(out), "--max-usd", str(a.max_usd)]
    extra = ["--estimate-only"] if a.estimate_only else []
    api_run.main(common + ["--encs", ONE_SHOT] + extra)
    api_agent.main(common + ["--variants", AGENT] + extra)
    if a.estimate_only:
        return 0
    problems = check(out)
    print(f"preflight in {out}: " + ("passed" if not problems else f"{len(problems)} problems"))
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
