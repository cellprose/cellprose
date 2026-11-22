"""Direct-API benchmark runner: pinned models, explicit settings, no prompt caching, usage recorded per call.

  python api_run.py --sample --models haiku55          # 3 workbooks x 2 encodings, one model, cheap check
  python api_run.py --models haiku45,haiku55,sonnet55  # full grid
  python api_run.py --sample --models haiku55 --estimate-only

Raw files land in <out>/raw/<alias>/<workbook>.<encoding>[.rN].json (default out: results/, or
results/sample/ with --sample). Point score.py and analyze.py at it with RESULTS_DIR=<out>.
Every call in one invocation shares a run id; run everything you intend to compare in one invocation.

Workbooks are split into development and held-out sets by split.json. Held-out workbooks need --final, which also
refuses a dirty working tree (--allow-dirty overrides it, and the run records the flag either way). A call that
fails (API error after retries, truncation, refusal) is written as a failure record that score.py scores 0.
Each run writes <out>/runs/<run id>.json with the git state and a SHA-256 of every question and encoded file.
"""
import argparse
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from runner import models, split as splitmod
from runner.ids import canon
from runner.cost import estimate
from runner.pilot import measured
from runner.prompts import CORPUS, SYSTEM, prompt
from runner.providers import get_provider
from runner.runmeta import check_prices_date, input_checksums, make_meta, resume_meta, write_manifest
from runner.store import (build_failure, build_raw, git_dirty, infra_failure, infrastructure, raw_path, recordable,
                          write_raw)
from runner.types import InfraFailure

INFRA_STOP = 5      # consecutive infrastructure failures from one vendor that stop new calls to it

ROOT = Path(__file__).parent
SAMPLE_WORKBOOKS = ["01_sales_log", "04_saas_model", "11_forecast_overrides"]   # small, mid-size, hard
SAMPLE_ENCS = ["csv", "cellprose_v03"]
DEFAULT_MAX_USD = 5.0


class CapReached(RuntimeError):
    """The vendor's spend reached --vendor-cap-usd, so this call was not made."""


def plan(aliases, workbooks, encs, rep, out):
    """Jobs still to run, and how many are already on disk."""
    todo, cached = [], 0
    for alias in aliases:
        cfg = models.get(alias)
        for wb in workbooks:
            for enc in encs:
                if raw_path(out, cfg, wb, enc, rep).exists():
                    cached += 1
                else:
                    todo.append((cfg, wb, enc))
    return todo, cached


def run_one(provider, cfg, wb, enc, rep, out, meta):
    """One call. A provider failure is written as a failure record (scored 0) instead of dropping out of the results;
    anything else (a bug in the runner itself) propagates and writes nothing."""
    user = prompt(wb, enc)
    t0 = datetime.now(timezone.utc)
    try:
        res = provider.complete(cfg, SYSTEM, user)
        build, arg = build_raw, res
    except Exception as e:
        if not recordable(e):
            raise
        if infrastructure(e):
            raise infra_failure(out, meta, cfg, wb, enc, rep, build_failure(cfg, wb, enc, user, e, {})) from e
        build, arg = build_failure, e
    data = build(cfg, wb, enc, user, arg, {**meta, "rep": rep, "wall_seconds":
                                           round((datetime.now(timezone.utc) - t0).total_seconds(), 1)})
    path = raw_path(out, cfg, wb, enc, rep)
    write_raw(path, data)
    return path, data


class _NoCounting:
    """Stand-in provider for --estimate-only when a key or endpoint is missing: counting fails, so the estimate falls
    back to characters. It cannot make a call."""

    def count_tokens(self, cfg, system, user):
        raise RuntimeError("no credentials for this provider")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", default="haiku55", help=f"comma list of: {', '.join(models.REGISTRY)}")
    ap.add_argument("--sample", action="store_true", help="3 workbooks x 2 encodings, for cheap checks")
    ap.add_argument("--workbooks", help="comma list; default all (or the sample set)")
    ap.add_argument("--encs", help="comma list; default all encodings plus none (or the sample set)")
    ap.add_argument("--rep", type=int, default=int(os.environ.get("REP", "0")), help="first repeat number -> .rN.json")
    ap.add_argument("--reps", type=int, default=1, help="number of repeats, all in this one invocation (one run id)")
    ap.add_argument("--vendor-cap-usd", type=float, help="hard stop per vendor (provider): refuse if its expected cost is "
                    "above this, and stop starting new calls once its spend reaches it")
    ap.add_argument("--final", action="store_true", help="the publishable run: allows held-out workbooks, needs a clean tree")
    ap.add_argument("--allow-dirty", action="store_true", help="with --final, run despite uncommitted changes (recorded)")
    ap.add_argument("--subset", type=int, help="use a seeded random subset of this many held-out workbooks")
    ap.add_argument("--seed", type=int, help="seed for --subset (default: the seed in split.json)")
    ap.add_argument("--openweight", action="append", default=[], metavar="ALIAS=MODEL_ID,PRICE_IN,PRICE_OUT",
                    help="register an open-weight model behind an OpenAI-compatible endpoint "
                         "(CELLPROSE_COMPAT_BASE_URL); repeatable")
    ap.add_argument("--openrouter-hosts", metavar="HOST[,HOST...]",
                    help="pin every OpenRouter model to these upstream hosts, in order, with no fallback "
                         "(recorded in each raw file); without it OpenRouter chooses the host per call")
    ap.add_argument("--out", help="results root (default results/, or results/sample/ with --sample)")
    ap.add_argument("--max-usd", type=float, default=DEFAULT_MAX_USD,
                    help="refuse to run if the expected cost is higher; raise only after the owner approves")
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("--prices-checked", metavar="YYYY-MM-DD",
                    help="day the list prices in runner/models.py were checked; required with --final")
    ap.add_argument("--resume", metavar="RUN_ID", help="continue that run under the same id (same commit and inputs, "
                    "within 48 h of its start); only calls with no record on disk are made")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)

    for spec in a.openweight:
        models.register_from_arg(spec)
    if a.openrouter_hosts:
        models.pin_openrouter_hosts(a.openrouter_hosts.split(","))
    aliases = a.models.split(",")
    allwb = sorted(p.stem for p in (CORPUS / "questions").glob("*.json"))
    sp = splitmod.load()
    seed = a.seed if a.seed is not None else sp["subset"]["seed"]
    try:
        workbooks = splitmod.select(a.workbooks, SAMPLE_WORKBOOKS if a.sample else None, allwb, a.final, a.subset, seed, sp)
        splitmod.require_clean_for_final(a.final, git_dirty(), a.allow_dirty)
    except SystemExit as e:
        print(e)
        return 2
    if a.encs:
        encs = [canon(e) for e in a.encs.split(",")]
    elif a.sample:
        encs = SAMPLE_ENCS
    else:
        from encoders import ENCODINGS
        encs = ENCODINGS + ["none"]
    out = Path(a.out) if a.out else ROOT / "results" / ("sample" if a.sample else "")
    todo, cached = [], 0
    for rep in range(a.rep, a.rep + a.reps):      # repeat-major order: a stop leaves whole repeats behind
        t, c = plan(aliases, workbooks, encs, rep, out)
        todo += [(cfg, wb, enc, rep) for cfg, wb, enc in t]
        cached += c
    cfgs = {c.alias: c for c in (models.get(x) for x in aliases)}
    providers = {}
    for alias, c in cfgs.items():
        try:
            providers[alias] = get_provider(c)
        except SystemExit as e:
            if not a.estimate_only:
                raise
            print(f"({alias}: {e}; estimating from characters)")
            providers[alias] = _NoCounting()

    print(f"{len(todo)} calls to run, {cached} already on disk in {out}")
    if not todo:
        return 0
    jobs = [(cfg, SYSTEM, prompt(wb, enc), (measured(cfg.alias, enc) or (None,))[0]) for cfg, wb, enc, _ in todo]
    try:
        est = estimate(jobs, lambda cfg, s, u: providers[cfg.alias].count_tokens(cfg, s, u))
    except Exception as e:      # no key or no network: fall back to a character estimate
        print(f"(exact token counting unavailable: {type(e).__name__}; using a character estimate)")
        est = estimate(jobs)
    print("\n".join(est.lines()))
    if est.expected_usd > a.max_usd:
        print(f"\nExpected cost ${est.expected_usd:.2f} is above the ${a.max_usd:.2f} limit. "
              f"Get approval, then rerun with --max-usd {est.expected_usd * 1.2:.0f}.")
        return 2
    if a.vendor_cap_usd is not None:
        by_vendor = {}
        for job in jobs:
            by_vendor.setdefault(job[0].provider, []).append(job)
        over = []
        for v, js in by_vendor.items():
            e = estimate(js, lambda cfg, s_, u_: providers[cfg.alias].count_tokens(cfg, s_, u_)) if est.exact_input else estimate(js)
            print(f"{v}: expected ${e.expected_usd:.2f}, cap ${a.vendor_cap_usd:.2f}")
            if e.expected_usd > a.vendor_cap_usd:
                over.append(v)
        if over:
            print(f"Expected cost for {', '.join(over)} is above the ${a.vendor_cap_usd:.2f} vendor cap; nothing run.")
            return 2
    if a.estimate_only:
        return 0
    if err := check_prices_date(a.final, a.prices_checked):
        print(err)
        return 2

    sums = input_checksums(CORPUS, workbooks, encs)
    invocation = {"argv": list(argv if argv is not None else sys.argv[1:]), "models": aliases, "workbooks": workbooks,
                  "encodings": encs, "reps": a.reps, "first_rep": a.rep, "prices_checked": a.prices_checked}
    if a.resume:
        try:
            meta = resume_meta(out, a.resume, sums, invocation)
        except SystemExit as e:
            print(e)
            return 2
        print(f"resuming run id {meta['run_id']}: {len(todo)} calls left")
    else:
        meta = make_meta(CORPUS, ROOT, a.final, sums, {"split_seed": seed, "subset_size": a.subset})
        try:
            import anthropic
            meta["anthropic_sdk"] = anthropic.__version__
        except ImportError:
            pass
        manifest = write_manifest(out, meta, sums, invocation)
        print(f"run id {meta['run_id']} (manifest {manifest})")
    failed = recorded = skipped = infra = 0
    kinds = {}
    spend, lock = {}, threading.Lock()
    streak, stopped = {}, set()

    def guarded(c, wb, enc, rep):
        with lock:
            if c.provider in stopped:
                raise CapReached(c.provider)
            if a.vendor_cap_usd is not None and spend.get(c.provider, 0.0) >= a.vendor_cap_usd:
                raise CapReached(c.provider)
        try:
            path, d = run_one(providers[c.alias], c, wb, enc, rep, out, meta)
        except InfraFailure as e:
            with lock:
                spend[c.provider] = spend.get(c.provider, 0.0) + e.cost
                streak[c.provider] = streak.get(c.provider, 0) + 1
                if streak[c.provider] >= INFRA_STOP and c.provider not in stopped:
                    stopped.add(c.provider)
                    print(f"{c.provider}: {INFRA_STOP} infrastructure failures in a row; no new calls to it", flush=True)
            raise
        with lock:
            streak[c.provider] = 0
            spend[c.provider] = spend.get(c.provider, 0.0) + d["cost"]
        return path, d

    with ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(guarded, c, wb, enc, rep): (c, wb, enc) for c, wb, enc, rep in todo}
        for i, f in enumerate(as_completed(futs), 1):
            c, wb, enc = futs[f]
            try:
                path, d = f.result()
                if d.get("failed"):
                    recorded += 1
                    kinds[(c.alias, d["failure"]["kind"])] = kinds.get((c.alias, d["failure"]["kind"]), 0) + 1
                    print(f"[{i}/{len(todo)}] {c.alias}/{path.name} FAILURE RECORDED (scores 0) "
                          f"{d['failure']['type']}: {d['failure']['message']}", flush=True)
                else:
                    print(f"[{i}/{len(todo)}] {c.alias}/{path.name} ok out={d['usage']['output_tokens']} "
                          f"cost=${d['cost']:.4f}", flush=True)
            except CapReached:
                skipped += 1
            except InfraFailure as e:
                infra += 1
                print(f"[{i}/{len(todo)}] {c.alias}/{wb}.{enc} NOT RECORDED (infrastructure, stays to do) {e}", flush=True)
            except Exception as e:
                failed += 1
                print(f"[{i}/{len(todo)}] {c.alias}/{wb}.{enc} FAILED {type(e).__name__}: {e}", flush=True)
    print("spend by vendor: " + ", ".join(f"{v} ${x:.2f}" for v, x in sorted(spend.items())))
    if skipped or infra:
        print(f"{skipped + infra} calls not made or not recorded ({infra} infrastructure failures, {skipped} skipped "
              f"after a vendor stop or cap). Fix the cause, then rerun the same command with --resume {meta['run_id']}")
    if recorded:
        print("failures recorded as score 0: " + ", ".join(f"{m}/{k} x{n}" for (m, k), n in sorted(kinds.items())))
    print(f"done, {recorded} failures recorded, {failed} not recorded (runner errors)")
    return 1 if failed or recorded or skipped or infra else 0


if __name__ == "__main__":
    sys.exit(main())
