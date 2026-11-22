"""Headline table: accuracy, total tokens and list-price cost per encoding, relative to CSV (one-shot)
and to raw .xlsx (agent mode), then the paired-bootstrap verdicts of docs/PROTOCOL.md section 7 and the
vendor-tokenizer counts beside billed input. Run score.py first."""
import json
import os
from pathlib import Path

import pandas as pd

from runner import split as splitmod
from runner.ids import canon
from limitations import block
from runner.models import LONG_TIERS, price_for
from score import HARD
from stats import comparisons

ROOT = Path(__file__).parent
RESULTS = Path(os.environ.get("RESULTS_DIR") or ROOT / "results")


def usage(d):
    mu = d.get("modelUsage") or {}
    family = "haiku" if "haiku" in d["model"] else "sonnet"     # CLI runs also list a helper model; take ours
    k = next(iter(mu)) if len(mu) == 1 else next(k for k in mu if family in k)   # runner files list only the one model
    v = mu[k]
    inp = v.get("inputTokens", 0) + v.get("cacheReadInputTokens", 0) + v.get("cacheCreationInputTokens", 0)
    out = v.get("outputTokens", 0)
    # cache-neutral list-price cost: repeated identical prompts hit the prompt cache, which would make
    # later repetitions look ~90% cheaper. Price every input token as uncached input instead.
    # Prices come from the exact model ID recorded in the file (runner/models.py).
    run = d.get("run") or {}
    price_in, price_out = ((run["price_in_per_mtok"], run["price_out_per_mtok"]) if "price_in_per_mtok" in run
                           else price_for(k))     # prices recorded with the call; older files fall back to the registry
    tier = run["long_prompt_tier"] if "long_prompt_tier" in run else next(
        (t for m, t in LONG_TIERS.items() if k.startswith(m)), None)     # None for flat-rate models
    # a long-prompt rate applies per request, so agent files are priced turn by turn
    turns = (run.get("provider_usage") or {}).get("turns")
    parts = ([(t.get("input_tokens", 0) + t.get("cache_read_tokens", 0) + t.get("cache_write_tokens", 0),
               t.get("output_tokens", 0)) for t in turns] if turns else [(inp, out)])
    cost = 0.0
    for pi, po in parts:
        r_in, r_out = (tier["price_in"], tier["price_out"]) if tier and pi > tier["threshold"] else (price_in, price_out)
        cost += (pi * r_in + po * r_out) / 1e6
    return inp, out, cost


rows = []
for f in (RESULTS / "raw").glob("*/*.json"):
    d = json.loads(f.read_text())
    i, o, c = usage(d)
    rep = f.stem.split(".")[-1] if f.stem.split(".")[-1].startswith("r") else "r0"
    pu = (d.get("run") or {}).get("provider_usage") or {}
    rows.append({"rep": rep, "model": d["model"], "workbook": d["workbook"], "encoding": canon(d["encoding"]), "in": i, "out": o,
                 "cost": c, "turns": d.get("num_turns", 1), "failed": int(bool(d.get("failed"))),
                 "tok_count": pu.get("tokenizer_input_tokens"), "tokenizer": pu.get("tokenizer"),
                 "billed": pu.get("billed_usd", c)})      # as billed (prompt cache on agent turns); never the metric
u = pd.DataFrame(rows)
s = pd.read_csv(RESULTS / "scores.csv")
acc = s.groupby(["model", "workbook", "encoding", "rep"])["score"].mean().rename("acc").reset_index()
df = u.merge(acc, on=["model", "workbook", "encoding", "rep"])
guess = df[df.encoding == "none"]      # the no-workbook control: not compared, shown beside accuracy below
df = df[df.encoding != "none"]
df["set"] = df.workbook.map(lambda w: "hard" if w in HARD else "standard")
df["split"] = df.workbook.map(splitmod.role)


def table(sub, base):
    # means per call, so encodings with different numbers of repetitions compare fairly
    g = sub.groupby(["model", "encoding"]).agg(n=("workbook", "count"), acc=("acc", "mean"), tin=("in", "mean"),
                                               tout=("out", "mean"), cost=("cost", "mean"), turns=("turns", "mean"))
    g["tokens"] = g.tin + g.tout
    g["cost_per_correct"] = g.cost / g.acc
    out = []
    for m in g.index.get_level_values(0).unique():
        t = g.loc[m].copy()
        b = t.loc[base]
        t["acc"] = (100 * t.acc).round(1)
        for c in ("tokens", "tout", "cost", "cost_per_correct"):
            t[c + "_vs"] = (100 * (t[c] / b[c] - 1)).round(0)
        t.insert(0, "model", m)
        out.append(t.reset_index())
    return pd.concat(out)


pd.set_option("display.width", 250)
one = df[~df.encoding.str.startswith("agent")]
cols = ["model", "encoding", "n", "acc", "tokens", "tokens_vs", "tout_vs", "cost", "cost_vs", "cost_per_correct_vs"]
res = {}
for st in ("standard", "hard", "all"):
    sub = one if st == "all" else one[one.set == st]
    if sub.empty:
        continue
    res[f"oneshot_{st}"] = table(sub, "csv")[cols]
    print(f"\n== one-shot, {st} (vs CSV)\n", res[f"oneshot_{st}"].to_string(index=False))
ag = df[df.encoding.str.startswith("agent") | df.encoding.isin(["sheetmark_lean", "cellprose_v03", "cellprose_v03_nolegend"])]
ag = ag[ag.workbook.isin(df[df.encoding == "agent_xlsx"].workbook)]
if len(ag):     # direct-API runs (e.g. results/sample) have no agent-mode files
    res["agent"] = table(ag, "agent_xlsx")[cols + ["turns"]]
    print("\n== agent mode (vs raw .xlsx with tools; cellprose_v03 and sheetmark_lean = one-shot in context)\n", res["agent"].to_string(index=False))
else:
    print("\n(no agent-mode runs in this results directory; skipping that table)")
final = [json.loads(f.read_text()) for f in sorted((RESULTS / "runs").glob("*.json"))
         if json.loads(f.read_text()).get("run", {}).get("final")] if (RESULTS / "runs").exists() else []
if final:       # the benchmark run (docs/PROTOCOL.md section 10): its own limitations, filled from the results
    dates = sorted({m["invocation"].get("prices_checked") or "not recorded" for m in final})
    print("\n" + block(run={"workbooks": s.workbook.nunique(), "questions": len(s.drop_duplicates(["workbook", "qid"]))
                            if "qid" in s else "?", "reps": u.rep.nunique(), "prices_checked": ", ".join(dates)}))
else:
    print("\n" + block())
with open(RESULTS / "headline.json", "w") as fh:
    json.dump({k: v.to_dict(orient="records") for k, v in res.items()}, fh, indent=1, default=float)


# ---- paired bootstrap: Cellprose against each baseline, per model (docs/PROTOCOL.md section 7). The compared encoding is
# v0.3 (`cellprose_v03`); a results directory from before v0.3 has none, so it falls back to v0.2 and says so.
A = canon(os.environ.get("COMPARE_ENC") or ("cellprose_v03" if (df.encoding == "cellprose_v03").any() else "cellprose_v03_nolegend" if (df.encoding == "cellprose_v03_nolegend").any() else "sheetmark_lean_gfm"))
LABEL = {"cellprose_v03": "v0.3", "cellprose_v03_nolegend": "v0.3 (no legend)", "sheetmark_lean_gfm": "v0.2"}.get(A, A)
if A == "sheetmark_lean_gfm" and not os.environ.get("COMPARE_ENC"):
    print("\n(no cellprose_v03 calls in this results directory: comparing the v0.2 text, sheetmark_lean_gfm)")
BASELINES = ["markitdown", "agent_xlsx", "agent_xlsx_viewer", "csv", "markdown", "toon"]      # primary first, then the reference and secondaries
verdicts = []
for name, sub in (("dev", df[df.split == "dev"]), ("held_out", df[df.split == "held_out"]), ("all", df)):
    for r in comparisons(sub, A, BASELINES):
        verdicts.append({"set": name, **r})
fails = df[df.failed == 1].groupby(["model", "encoding"]).size().rename("failed_calls").reset_index()
if verdicts:
    vt = pd.DataFrame(verdicts)
    show = vt[["set", "model", "baseline", "n_workbooks", "acc", "acc_baseline", "acc_diff_points", "ratio", "ratio_lo",
               "ratio_hi", "verdict"]].round(3)
    print(f"\n== {LABEL} ({A}) cost per correct vs each baseline: ratio < 1 means {LABEL} is cheaper; "
          "95% paired bootstrap over workbooks (10,000 resamples, fixed seed)\n", show.to_string(index=False))
    with open(RESULTS / "verdicts.json", "w") as fh:
        json.dump(verdicts, fh, indent=1, default=float)
# ---- the guess baseline (docs/PROTOCOL.md section 10): accuracy with no workbook at all, shown beside every arm's, so
# an accuracy figure is read against what can be answered without the data (zero answers, values already in place).
if len(guess):
    g = df.groupby(["model", "encoding"]).acc.mean().unstack().round(3)
    g.insert(0, "none (guess)", guess.groupby("model").acc.mean().round(3))
    print("\n== accuracy beside the no-workbook guess baseline (mean question score)\n", g.to_string())
if len(fails):
    print("\n== failed calls (scored 0, tokens included in cost)\n", fails.to_string(index=False))

# ---- vendor tokenizer count beside billed input (per call, system + prompt)
tk = df.dropna(subset=["tok_count"])
if len(tk):
    g = tk.groupby(["model", "encoding"]).agg(n=("in", "count"), billed_in=("in", "mean"), tokenizer_count=("tok_count", "mean"),
                                              tokenizer=("tokenizer", "first"))
    g["count_vs_billed"] = (g.tokenizer_count / g.billed_in).round(3)
    base = g.tokenizer_count.groupby(level=0).transform(lambda x: x.loc[(x.name, "csv")] if (x.name, "csv") in x.index else float("nan"))
    g["count_vs_csv"] = (g.tokenizer_count / base).round(3)
    print("\n== vendor tokenizer count vs billed input (one-shot calls)\n", g.round(0).assign(
        count_vs_billed=g.count_vs_billed, count_vs_csv=g.count_vs_csv).to_string())
    g.reset_index().to_csv(RESULTS / "tokenizer_counts.csv", index=False)

# ---- the actual bill, beside the metric: Anthropic agent turns use the prompt cache (docs/PROTOCOL.md section 5), so
# what was paid is lower than the uncached list-price cost every comparison above uses.
bill = u.groupby("model").agg(list_price_uncached=("cost", "sum"), billed=("billed", "sum")).round(2)
print("\n== spend: uncached list price (the metric) and as billed (Anthropic cache counted; OpenAI's automatic\n   cache discount is not)\n", bill.to_string())

# ---- infrastructure failures (docs/PROTOCOL.md section 5): not recorded and not in the metric, but paid for
infra = [json.loads(line) for f in sorted((RESULTS / "runs").glob("*.infra.jsonl")) for line in f.read_text().splitlines()]
if infra:
    inf = pd.DataFrame(infra).groupby("model").agg(attempts=("cost", "count"), list_price=("cost", "sum")).round(2)
    print("\n== infrastructure failures (redone on resume; their spend is outside the metric)\n", inf.to_string())
