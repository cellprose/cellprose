"""Free benchmark sample for CI: no API calls, no spend.

Encodes every benchmark workbook with the current writer and compares its token count (tiktoken o200k_base,
offline) with `ci_baseline.json`. The writer must not get more expensive: a workbook that grows by more than
--per-workbook percent, or a total that grows by more than --total percent, fails the run. A writer change that
makes output smaller or larger on purpose refreshes the baseline with `--update`, in the same PR.

This checks cost, not accuracy. Accuracy needs model calls, so it stays a manual step:
`python benchmarks/api_run.py --sample --models haiku55 --estimate-only` prices it, and it asks before spending.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "src"))
from cellprose import stats  # noqa: E402

BASELINE = ROOT / "ci_baseline.json"


def measure():
    out = {}
    for path in sorted((ROOT / "workbooks").glob("*.xlsx")):
        f = stats.compute(path)["formats"]
        out[path.stem] = {k: f[k]["tokens"] for k in ("cellprose", "csv", "markdown")}
    return out


def pct(new, old):
    return (new - old) / old * 100 if old else 0.0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--update", action="store_true", help="rewrite ci_baseline.json from the current writer")
    ap.add_argument("--per-workbook", type=float, default=2.0, help="max %% growth of one workbook (default 2)")
    ap.add_argument("--total", type=float, default=1.0, help="max %% growth of the total (default 1)")
    args = ap.parse_args(argv)
    now = measure()
    if args.update:
        BASELINE.write_text(json.dumps({"tokenizer": stats.TOKENIZER, "workbooks": now}, indent=1) + "\n")
        print(f"wrote {BASELINE.name} for {len(now)} workbooks")
        return 0
    base = json.loads(BASELINE.read_text())["workbooks"]
    if set(base) != set(now):
        print(f"workbook set changed: only in baseline {sorted(set(base) - set(now))}, only now {sorted(set(now) - set(base))}; "
              "run with --update", file=sys.stderr)
        return 1
    print(f"tokens ({stats.TOKENIZER}, OpenAI tokenizer, counted offline; not Claude token counts)")
    print("| workbook | cellprose | baseline | change | csv | vs csv |\n|---|---|---|---|---|---|")
    bad = []
    for name, t in now.items():
        ch = pct(t["cellprose"], base[name]["cellprose"])
        print(f"| {name} | {t['cellprose']} | {base[name]['cellprose']} | {ch:+.1f}% | {t['csv']} | {pct(t['cellprose'], t['csv']):+.0f}% |")
        if ch > args.per_workbook:
            bad.append(f"{name} grew {ch:+.1f}% (limit {args.per_workbook}%)")
    tot, tot0 = sum(t["cellprose"] for t in now.values()), sum(t["cellprose"] for t in base.values())
    csv = sum(t["csv"] for t in now.values())
    print(f"| **total** | {tot} | {tot0} | {pct(tot, tot0):+.1f}% | {csv} | {pct(tot, csv):+.0f}% |")
    if pct(tot, tot0) > args.total:
        bad.append(f"total grew {pct(tot, tot0):+.1f}% (limit {args.total}%)")
    for b in bad:
        print("FAIL:", b, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
