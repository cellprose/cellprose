"""Agent-mode benchmark through the APIs: the workbook is a file, the model has `bash` and `read_file` tools and explores
until it answers. This replaces `run_agent.py` (Claude CLI) for the publishable run; pinned models, explicit reasoning
settings, no prompt caching, tokens recorded for every turn.

  python api_agent.py --sample --models haiku55 --estimate-only
  python api_agent.py --models haiku55,gpt6luna --variants agent_xlsx --reps 2 --final

Variants:
  agent_xlsx       ./book.xlsx (cached values present); python3 + openpyxl are available to the bash tool
  agent_xlsx_viewer  as agent_xlsx, plus a `view_xlsx` tool (formulas next to cached values, as in SpreadsheetBench 2);
                   opt-in, a benchmark arm
  agent_xlsx_cellprose  as agent_xlsx, plus the Cellprose tools outline, read_range, find and trace
                   (src/cellprose/tools.py); opt-in, experiments/E33
  agent_xlsx_cellprose_idx  as agent_xlsx_cellprose, with `outline` cut to an index of regions (E33 follow-up)
  agent_cellprose_lean  E34: the index in the prompt; tools read_range (several ranges), find, trace (ranges); no shell
  agent_cellprose_v03   ./book.sheet.md (the shipped v0.3 text, read through the same tools); the default
  agent_sheetmark  ./book.sheet.md (the v0.2 text); opt-in, kept so earlier runs stay comparable
  agent_sheetmark_hint  as agent_sheetmark, with each fill range's last-cell formula as a comment (opt-in; backlog B20)
Raw files land beside the one-shot ones (<out>/raw/<alias>/<workbook>.<variant>[.rN].json) and score.py / analyze.py read
them unchanged. Split, --final, failure records, checksums and run manifests work as in api_run.py. A call that uses all
--max-turns turns or reaches --max-call-usd is a failure and scores 0; its tokens still count.

The bash tool runs model-written commands on this machine. Run this inside a container or VM (see runner/agent.py).
"""
import argparse
import dataclasses
import glob
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from runner import agent as agentmod, models, split as splitmod
from runner.prompts import AGENT_FILES, AGENT_SYSTEM, CORPUS, LEAN_SYSTEM, agent_prompt, agent_source, lean_prompt
from runner.pilot import measured
from runner.providers import get_provider
from runner.ids import LEGACY, canon
from runner.runmeta import check_prices_date, input_checksums, make_meta, resume_meta, write_manifest
from runner.store import (build_failure, build_raw, git_dirty, infra_failure, infrastructure, raw_path, recordable,
                          write_raw)
from runner.types import InfraFailure

INFRA_STOP = 5      # consecutive infrastructure failures from one vendor that stop new calls to it

ROOT = Path(__file__).parent
SAMPLE_WORKBOOKS = ["01_sales_log", "04_saas_model", "11_forecast_overrides"]
DEFAULT_VARIANTS = ["agent_xlsx", "agent_cellprose_v03"]
VARIANTS = DEFAULT_VARIANTS + ["agent_xlsx_viewer", "agent_sheetmark", "agent_sheetmark_hint", "agent_cellprose_v03_nolegend", "agent_xlsx_cellprose", "agent_xlsx_cellprose_idx", "agent_cellprose_lean"]    # opt-in variants
XLSX_VARIANTS = {v for v in VARIANTS if v.startswith("agent_xlsx")} | {"agent_cellprose_lean"}   # these read book.xlsx
DEFAULT_MAX_USD = 5.0
# Used only when no earlier agent-mode file is on disk to average: mean tokens per call from the earlier CLI runs.
FALLBACK_TOKENS = {"agent_xlsx": (28_300, 3_250), "agent_sheetmark": (8_500, 780), "agent_sheetmark_hint": (9_000, 780),
                   "agent_cellprose_v03_nolegend": (8_300, 780), "agent_cellprose_v03": (8_300, 780)}


def historic_tokens(variant: str, raw_dir: Path = ROOT / "results" / "raw") -> tuple[float, float, int]:
    """(mean input tokens, mean output tokens, files) per call for `variant` from earlier runs on disk. The legacy CLI
    runs carry the CLI's own prompt overhead, so this is a rough guide, not a measurement of the API loop."""
    ins, outs = [], []
    names = [variant] + [old for old, new in LEGACY.items() if new == variant]      # raw files from before the rename
    files = [f for n in names for pat in (f"*.{n}.json", f"*.{n}.r*.json") for f in glob.glob(str(raw_dir / "*" / pat))]
    for f in files:
        d = json.loads(Path(f).read_text())
        usage = list((d.get("modelUsage") or {}).values())
        if not usage:
            continue
        u = max(usage, key=lambda x: x.get("inputTokens", 0) + x.get("cacheReadInputTokens", 0) + x.get("cacheCreationInputTokens", 0))
        ins.append(u.get("inputTokens", 0) + u.get("cacheReadInputTokens", 0) + u.get("cacheCreationInputTokens", 0))
        outs.append(u.get("outputTokens", 0))
    if not ins and variant == "agent_sheetmark_hint":     # no runs yet: the plain v0.2 file's history, 6% more input (E22)
        tin, tout, n = historic_tokens("agent_sheetmark", raw_dir)
        return tin * 1.06, tout, n
    if not ins and variant in ("agent_xlsx_viewer", "agent_xlsx_cellprose", "agent_xlsx_cellprose_idx", "agent_cellprose_lean"):   # no runs yet: the plain-shell history (a guess; fewer turns may make it cheaper)
        return historic_tokens("agent_xlsx", raw_dir)
    if not ins and variant == "agent_cellprose_v03":      # no runs yet: the no-legend file plus the 28-token legend
        tin, tout, n = historic_tokens("agent_cellprose_v03_nolegend", raw_dir)
        return tin + 28, tout, n
    if not ins and variant == "agent_cellprose_v03_nolegend":      # no runs yet: the v0.2 file's history, 2.8% less input (E28)
        tin, tout, n = historic_tokens("agent_sheetmark", raw_dir)
        return tin * 0.972, tout, n
    if not ins:
        return (*FALLBACK_TOKENS[variant], 0)
    return sum(ins) / len(ins), sum(outs) / len(outs), len(ins)


def estimate(todo, max_call_usd):
    """(expected usd, ceiling usd, lines). The ceiling is the per-call cap times the calls (plus at most one turn each:
    the cap is checked before a turn starts); the expectation prices earlier agent-mode token averages."""
    expected = 0.0
    notes = {}
    pilot = {}
    for cfg, wb, variant, rep in todo:
        m = measured(cfg.alias, variant)
        if m:       # the API pilot's mean list-price cost per call for this model and arm (runner/pilot.py)
            pilot[(cfg.alias, variant)] = m
            expected += min(m[1], max_call_usd)
            continue
        tin, tout, n = historic_tokens(variant)
        notes[variant] = (tin, tout, n)
        expected += min((tin * cfg.price_in + tout * cfg.price_out) / 1e6, max_call_usd)
    ceiling = len(todo) * max_call_usd
    lines = [f"calls: {len(todo)}"]
    for (alias, v), (_, usd, n) in sorted(pilot.items()):
        lines.append(f"{alias}/{v}: about ${usd:.4f} per call (mean of {n} API pilot calls, E32, uncached list price)")
    for v, (tin, tout, n) in sorted(notes.items()):
        src = f"mean of {n} earlier CLI runs" if n else "fallback constants from the CLI runs"
        lines.append(f"{v}: about {tin:,.0f} input and {tout:,.0f} output tokens per call ({src}; not measured on the API loop)")
    lines += [f"expected cost: ${expected:.2f}", f"worst case (every call reaches the ${max_call_usd:.2f} cap, plus one turn): ${ceiling:.2f}"]
    return expected, ceiling, lines


ANTHROPIC_CACHE = True      # automatic prompt caching on Anthropic agent turns (docs/PROTOCOL.md section 5); priced uncached


def agent_cfg(cfg):
    """The model as the agent runner calls it: Anthropic agent turns use the prompt cache, and the raw file says so."""
    if cfg.provider == "anthropic" and ANTHROPIC_CACHE:
        return dataclasses.replace(cfg, prompt_caching="agent turns: automatic, 5-minute TTL; priced uncached, billed_usd recorded")
    return cfg


def plan(aliases, workbooks, variants, rep, out):
    todo, cached = [], 0
    for alias in aliases:
        cfg = agent_cfg(models.get(alias))
        for wb in workbooks:
            for v in variants:
                if raw_path(out, cfg, wb, v, rep).exists():
                    cached += 1
                else:
                    todo.append((cfg, wb, v, rep))
    return todo, cached


def run_one(provider, cfg, wb, variant, rep, out, meta, max_turns, max_call_usd):
    fname, src = agent_source(wb, variant)
    lean = variant == "agent_cellprose_lean"
    user = lean_prompt(wb) if lean else agent_prompt(wb, variant)
    t0 = datetime.now(timezone.utc)
    backend = agentmod.get_agent(cfg, provider, cache=ANTHROPIC_CACHE)
    with agentmod.Sandbox({fname: src}, index_outline=variant == "agent_xlsx_cellprose_idx", lean=lean) as sb:
        try:
            tools = {"agent_xlsx_viewer": agentmod.VIEWER_TOOLS,
                     "agent_xlsx_cellprose": agentmod.CELLPROSE_TOOLS,
                     "agent_xlsx_cellprose_idx": agentmod.CELLPROSE_IDX_TOOLS,
                     "agent_cellprose_lean": agentmod.LEAN_TOOLS}.get(variant, agentmod.TOOLS)
            run = agentmod.run_agent(cfg, backend, LEAN_SYSTEM if lean else AGENT_SYSTEM, user, sb, max_turns, max_call_usd, tools)
            data, trace = build_raw(cfg, wb, variant, user, run.result, {}), run.trace
            turns = run.turns
        except Exception as e:
            if not recordable(e):
                raise
            data = build_failure(cfg, wb, variant, user, e, {})
            if infrastructure(e):
                raise infra_failure(out, meta, cfg, wb, variant, rep, data) from e
            trace = []
            turns = (e.result.raw_usage.get("turns", []) if getattr(e, "result", None) else [])
    data["run"].update({**meta, "rep": rep, "max_turns": max_turns, "max_call_usd": max_call_usd,
                        "wall_seconds": round((datetime.now(timezone.utc) - t0).total_seconds(), 1)})
    data["num_turns"] = len(turns)
    data["tool_trace"] = trace
    path = raw_path(out, cfg, wb, variant, rep)
    write_raw(path, data)
    return path, data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", default="haiku55", help=f"comma list of: {', '.join(models.REGISTRY)} (Anthropic or OpenAI)")
    ap.add_argument("--variants", default=",".join(DEFAULT_VARIANTS), help=f"comma list of: {', '.join(VARIANTS)}")
    ap.add_argument("--sample", action="store_true", help="3 workbooks, for cheap checks")
    ap.add_argument("--workbooks", help="comma list; default every development workbook")
    ap.add_argument("--rep", type=int, default=int(os.environ.get("REP", "0")))
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--max-turns", type=int, default=agentmod.MAX_TURNS)
    ap.add_argument("--max-call-usd", type=float, default=agentmod.MAX_CALL_USD,
                    help="stop a call that has spent this much at list price; it is recorded as a failure (score 0)")
    ap.add_argument("--vendor-cap-usd", type=float, help="stop starting new calls once a vendor's spend reaches this")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--subset", type=int)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out")
    ap.add_argument("--max-usd", type=float, default=DEFAULT_MAX_USD)
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("--prices-checked", metavar="YYYY-MM-DD",
                    help="day the list prices in runner/models.py were checked; required with --final")
    ap.add_argument("--resume", metavar="RUN_ID", help="continue that run under the same id (same commit and inputs, "
                    "within 48 h of its start); only calls with no record on disk are made")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-anthropic-cache", action="store_true",
                    help="send no cache_control on Anthropic agent turns (any cache activity is then an error)")
    a = ap.parse_args(argv)
    global ANTHROPIC_CACHE
    ANTHROPIC_CACHE = not a.no_anthropic_cache

    aliases, variants = a.models.split(","), [canon(v) for v in a.variants.split(",")]
    bad = [v for v in variants if v not in VARIANTS]
    if bad:
        print(f"unknown variant {bad}; known: {VARIANTS}")
        return 2
    cfgs = [models.get(x) for x in aliases]
    unsupported = [c.alias for c in cfgs if c.provider not in ("anthropic", "openai")]
    if unsupported:
        print(f"agent mode supports Anthropic and OpenAI models only; not {unsupported}")
        return 2
    allwb = sorted(p.stem for p in (CORPUS / "questions").glob("*.json"))
    sp = splitmod.load()
    seed = a.seed if a.seed is not None else sp["subset"]["seed"]
    try:
        workbooks = splitmod.select(a.workbooks, SAMPLE_WORKBOOKS if a.sample else None, allwb, a.final, a.subset, seed, sp)
        splitmod.require_clean_for_final(a.final, git_dirty(), a.allow_dirty)
    except SystemExit as e:
        print(e)
        return 2
    out = Path(a.out) if a.out else ROOT / "results" / ("sample" if a.sample else "")
    todo, cached = [], 0
    for rep in range(a.rep, a.rep + a.reps):
        t, c = plan(aliases, workbooks, variants, rep, out)
        todo += t
        cached += c
    print(f"{len(todo)} calls to run, {cached} already on disk in {out}")
    if not todo:
        return 0
    expected, ceiling, lines = estimate(todo, a.max_call_usd)
    print("\n".join(lines))
    if expected > a.max_usd:
        print(f"\nExpected cost ${expected:.2f} is above the ${a.max_usd:.2f} limit. "
              f"Get approval, then rerun with --max-usd {expected * 1.2:.0f}.")
        return 2
    if a.estimate_only:
        return 0
    if err := check_prices_date(a.final, a.prices_checked):
        print(err)
        return 2

    providers = {c.alias: get_provider(c) for c in cfgs}
    text_encs = sorted({AGENT_FILES[v][2].split(".", 1)[1].removesuffix(".txt") for v in variants if v not in XLSX_VARIANTS})
    sums = input_checksums(CORPUS, workbooks, text_encs, agent_files=bool(XLSX_VARIANTS & set(variants)))
    invocation = {"argv": list(argv if argv is not None else sys.argv[1:]), "models": aliases, "workbooks": workbooks,
                  "variants": variants, "reps": a.reps, "first_rep": a.rep, "max_turns": a.max_turns,
                  "max_call_usd": a.max_call_usd, "anthropic_agent_cache": ANTHROPIC_CACHE,
                  "prices_checked": a.prices_checked}
    if a.resume:
        try:
            meta = resume_meta(out, a.resume, sums, invocation)
        except SystemExit as e:
            print(e)
            return 2
        print(f"resuming run id {meta['run_id']}: {len(todo)} calls left")
    else:
        meta = make_meta(CORPUS, ROOT, a.final, sums, {"split_seed": seed, "subset_size": a.subset, "mode": "agent"})
        manifest = write_manifest(out, meta, sums, invocation)
        print(f"run id {meta['run_id']} (manifest {manifest})")
    spend, lock = {}, threading.Lock()
    failed = recorded = skipped = infra = 0
    streak, stopped = {}, set()

    def guarded(cfg, wb, v, rep):
        with lock:
            if cfg.provider in stopped:
                return None
            if a.vendor_cap_usd is not None and spend.get(cfg.provider, 0.0) >= a.vendor_cap_usd:
                return None
        try:
            path, d = run_one(providers[cfg.alias], cfg, wb, v, rep, out, meta, a.max_turns, a.max_call_usd)
        except InfraFailure as e:
            with lock:
                spend[cfg.provider] = spend.get(cfg.provider, 0.0) + e.cost
                streak[cfg.provider] = streak.get(cfg.provider, 0) + 1
                if streak[cfg.provider] >= INFRA_STOP and cfg.provider not in stopped:
                    stopped.add(cfg.provider)
                    print(f"{cfg.provider}: {INFRA_STOP} infrastructure failures in a row; no new calls to it", flush=True)
            raise
        with lock:
            streak[cfg.provider] = 0
            spend[cfg.provider] = spend.get(cfg.provider, 0.0) + d["cost"]
        return path, d

    with ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(guarded, *j): j for j in todo}
        for i, f in enumerate(as_completed(futs), 1):
            cfg, wb, v, rep = futs[f]
            try:
                r = f.result()
            except InfraFailure as e:
                infra += 1
                print(f"[{i}/{len(todo)}] {cfg.alias}/{wb}.{v} NOT RECORDED (infrastructure, stays to do) {e}", flush=True)
                continue
            except Exception as e:
                failed += 1
                print(f"[{i}/{len(todo)}] {cfg.alias}/{wb}.{v} FAILED (not recorded) {type(e).__name__}: {e}", flush=True)
                continue
            if r is None:
                skipped += 1
                continue
            path, d = r
            if d.get("failed"):
                recorded += 1
                print(f"[{i}/{len(todo)}] {cfg.alias}/{path.name} FAILURE RECORDED (scores 0) {d['failure']['kind']} "
                      f"turns={d['num_turns']} cost=${d['cost']:.4f}", flush=True)
            else:
                print(f"[{i}/{len(todo)}] {cfg.alias}/{path.name} ok turns={d['num_turns']} cost=${d['cost']:.4f}", flush=True)
    print("spend by vendor: " + ", ".join(f"{v} ${x:.2f}" for v, x in sorted(spend.items())))
    if skipped or infra:
        print(f"{skipped + infra} calls not made or not recorded ({infra} infrastructure failures, {skipped} skipped "
              f"after a vendor stop or cap). Fix the cause, then rerun the same command with --resume {meta['run_id']}")
    print(f"done, {recorded} failures recorded, {failed} not recorded (runner errors)")
    return 1 if failed or recorded or skipped or infra else 0


if __name__ == "__main__":
    sys.exit(main())
