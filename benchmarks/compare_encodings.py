"""Two encodings head to head, per model: accuracy per repeat, billed tokens, cost and the paired bootstrap of
docs/PROTOCOL.md section 7. For runs without a CSV baseline, which analyze.py needs. Run score.py first.

  RESULTS_DIR=results/e19-nopipe python3 compare_encodings.py sheetmark_lean_gfm_nopipe sheetmark_lean_gfm
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

from score import HARD
from stats import paired_comparison

ROOT = Path(__file__).parent
RESULTS = Path(os.environ.get("RESULTS_DIR") or ROOT / "results")


def calls():
    rows = []
    for f in (RESULTS / "raw").glob("*/*.json"):
        d = json.loads(f.read_text())
        v = next(iter(d["modelUsage"].values()))
        i = v.get("inputTokens", 0) + v.get("cacheReadInputTokens", 0) + v.get("cacheCreationInputTokens", 0)
        o = v.get("outputTokens", 0)
        run = d["run"]
        cost = (i * run["price_in_per_mtok"] + o * run["price_out_per_mtok"]) / 1e6   # every input token uncached
        last = f.stem.split(".")[-1]
        rows.append({"model": d["model"], "workbook": d["workbook"], "encoding": d["encoding"],
                     "rep": last if last.startswith("r") else "r0", "inp": i, "out": o, "cost": cost})
    s = pd.read_csv(RESULTS / "scores.csv")
    acc = s.groupby(["model", "workbook", "encoding", "rep"])["score"].mean().rename("acc").reset_index()
    return pd.DataFrame(rows).merge(acc, on=["model", "workbook", "encoding", "rep"]), s


def main(a, b):
    df, s = calls()
    print(f"{len(df)} calls in {RESULTS}")
    for m in sorted(df.model.unique()):
        for e in (b, a):
            x = df[(df.model == m) & (df.encoding == e)]
            per = x.groupby("rep").agg(acc=("acc", "mean"), inp=("inp", "sum"), out=("out", "sum"), cost=("cost", "sum"))
            print(f"{m} {e}: acc {100 * x.acc.mean():.1f} ({' / '.join(f'{100 * v:.1f}' for v in per.acc)}), "
                  f"input {per.inp.mean():,.0f}, output {per.out.mean():,.0f}, "
                  f"cost ${per.cost.mean():.4f} ({' / '.join(f'${v:.4f}' for v in per.cost)}) per repeat")
        xa, xb = df[(df.model == m) & (df.encoding == a)], df[(df.model == m) & (df.encoding == b)]
        pct = lambda c: 100 * (xa[c].sum() / xb[c].sum() - 1)
        print(f"  {a} vs {b}: accuracy {100 * (xa.acc.mean() - xb.acc.mean()):+.1f} points, input {pct('inp'):+.1f}%, "
              f"output {pct('out'):+.1f}%, input+output "
              f"{100 * ((xa.inp.sum() + xa.out.sum()) / (xb.inp.sum() + xb.out.sum()) - 1):+.1f}%, cost {pct('cost'):+.1f}%")
        for st in ("standard", "hard"):
            ha, hb = xa[xa.workbook.isin(HARD) == (st == "hard")], xb[xb.workbook.isin(HARD) == (st == "hard")]
            print(f"  {st}: accuracy {100 * ha.acc.mean():.1f} vs {100 * hb.acc.mean():.1f}")
        r = paired_comparison(df, m, a, b)
        print(f"  paired bootstrap: cost per correct ratio {r['ratio']:.3f} [{r['ratio_lo']:.3f}, {r['ratio_hi']:.3f}], "
              f"accuracy {r['acc_diff_points']:+.2f} points [{r['acc_diff_lo']:+.2f}, {r['acc_diff_hi']:+.2f}]: {r['verdict']}")
    t = s[s.encoding.isin([a, b])].groupby(["model", "encoding", "task"])["score"].mean().unstack()
    print("\naccuracy by task (%)\n", (100 * t).round(1).to_string())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
