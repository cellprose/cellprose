"""Score raw model answers against ground truth and summarise by encoding, model and task."""
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

from openpyxl.utils import range_boundaries, get_column_letter

from runner.ids import canon

ROOT = Path(__file__).parent
RESULTS = Path(os.environ.get("RESULTS_DIR") or ROOT / "results")   # RESULTS_DIR=results/sample for api_run.py --sample
RAW = RESULTS / "raw"
CORPUS = Path(os.environ.get("CELLPROSE_CORPUS") or ROOT)   # same variable as runner/prompts.py
ORDER = ["none", "csv", "markdown", "markitdown", "markdown_kv", "toon", "grid_values", "sheetmark", "sheetmark_inline", "sheetmark_labels", "sheetmark_lean", "sheetmark_lean_gfm", "sheetmark_lean_gfm_nopipe", "cellprose_v03_nolegend", "cellprose_v03", "agent_xlsx", "agent_xlsx_viewer", "agent_xlsx_cellprose", "agent_xlsx_cellprose_idx", "agent_cellprose_lean", "agent_cellprose_v03_nolegend", "agent_cellprose_v03", "agent_sheetmark", "agent_sheetmark_hint", "sheetmark_lean_gfm_hint"]
TASKS = ["lookup", "address", "trace", "impact", "hardcode"]
HARD = {"11_forecast_overrides", "12_lookalike_drivers", "13_scenario_switch", "14_cost_allocation"}


def parse_json(text):
    """Return the last JSON object in the reply (models sometimes self-correct and print a second one)."""
    dec = json.JSONDecoder()
    best = {}
    i = 0
    while True:
        i = text.find("{", i)
        if i < 0:
            return best
        try:
            obj, end = dec.raw_decode(text, i)
            if isinstance(obj, dict) and any(k.startswith("q") for k in obj):
                best = obj
            i = end
        except json.JSONDecodeError:
            i += 1


def cells(ans, default_sheet):
    """Expand an address, range, or list of them into a set of 'Sheet!A1' strings."""
    items = ans if isinstance(ans, list) else [ans]
    out = set()
    for it in items:
        if not isinstance(it, str):
            continue
        for part in re.split(r"[,;]\s*", it):
            part = part.strip().replace("$", "")
            if not part:
                continue
            if "!" in part:
                sh, rng = part.rsplit("!", 1)
                sh = sh.strip()
                if len(sh) >= 2 and sh[0] == sh[-1] == "'":
                    sh = sh[1:-1].replace("''", "'")      # 'Original OBA''s'!X is the sheet Original OBA's
                else:
                    sh = sh.strip('"')
            else:
                sh, rng = default_sheet, part
            rng = rng.strip().upper()
            try:
                c1, r1, c2, r2 = range_boundaries(rng)
            except Exception:
                continue
            if None in (c1, r1, c2, r2) or (c2 - c1 + 1) * (r2 - r1 + 1) > 5000:
                continue
            out |= {f"{sh.lower()}!{get_column_letter(c)}{r}" for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
    return out


def num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.replace(",", "").replace("$", "").strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


def score(q, ans):
    sheet = q["cell"].split("!")[0]
    t = q["truth"]
    if q["type"] == "lookup":
        tn, an = num(t), num(ans)
        if tn is not None:
            # a whole-number truth (an ID, a count, a typed integer) must match to 0.01: 0.5% of 8002468 is ±40,000
            tol = 0.01 if float(tn).is_integer() else max(abs(tn) * 0.005, 0.01)
            ok = an is not None and abs(an - tn) <= tol
        else:
            ok = isinstance(ans, str) and ans.strip().lower() == str(t).strip().lower()
        return {"score": float(ok), "exact": float(ok)}
    if q["type"] == "address":
        got = cells(ans, sheet)
        ok = got == cells(t, sheet)
        return {"score": float(ok), "exact": float(ok)}
    truth = {c.lower().split("!")[0] + "!" + c.split("!")[1] for c in t}
    got = cells(ans, sheet)
    if not truth and not got:
        # An empty truth is only matched by an answer that was given: a missing key or a failed call scores 0.
        given = isinstance(ans, (list, str))
        return {"score": float(given), "exact": float(given)}
    tp = len(truth & got)
    p = tp / len(got) if got else 0.0
    r = tp / len(truth) if truth else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"score": f1, "exact": float(truth == got)}


def model_tokens(d):
    mu = d.get("modelUsage") or {}
    if not mu:
        u = d["usage"]
        return u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"]
    main = max(mu.items(), key=lambda kv: kv[1].get("inputTokens", 0) + kv[1].get("cacheReadInputTokens", 0)
               + kv[1].get("cacheCreationInputTokens", 0))
    v = main[1]
    return v.get("inputTokens", 0) + v.get("cacheReadInputTokens", 0) + v.get("cacheCreationInputTokens", 0)


def main():
    rows, tok = [], {}
    for f in sorted(RAW.glob("*/*.json")):
        d = json.loads(f.read_text())
        d["encoding"] = canon(d["encoding"])      # results from before the Nov 2026 rename score under the new ids
        qs = json.loads((CORPUS / "questions" / f"{d['workbook']}.json").read_text())
        ans = parse_json(d["result"])
        failed = bool(d.get("failed"))      # a failure record has result "" and so scores 0 on every question
        if not failed:      # a failed call's tokens are partial or zero; they would distort the workbook-token figures
            tok[(d["model"], d["workbook"], d["encoding"])] = model_tokens(d)
        for q in qs:
            s = score(q, ans.get(q["id"]))
            rows.append({"rep": f.stem.split(".")[-1] if f.stem.split(".")[-1].startswith("r") else "r0",
                         "set": "hard" if d["workbook"] in HARD else "standard",
                         "model": d["model"], "workbook": d["workbook"], "encoding": d["encoding"], "qid": q["id"],
                         "task": q["type"], "score": round(s["score"], 4), "exact": s["exact"], "failed": int(failed),
                         "answer": json.dumps(ans.get(q["id"]))[:300]})
    with open(RESULTS / "scores.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    # workbook tokens = call input tokens minus the no-workbook control call for the same model and workbook
    wbtok = defaultdict(list)
    for (m, wb, e), t in tok.items():
        if e != "none" and (m, wb, "none") in tok:
            st = "hard" if wb in HARD else "standard"
            for k in (st, "all"):
                wbtok[(k, m, e)].append((wb, t - tok[(m, wb, "none")]))
    agg = defaultdict(list)
    for r in rows:
        for st in (r["set"], "all"):
            agg[(st, r["model"], r["encoding"], r["task"])].append(r["score"])
            agg[(st, r["model"], r["encoding"], "all")].append(r["score"])
            agg[(st, r["model"], r["encoding"], r["task"] + "_exact")].append(r["exact"])
            agg[(st, r["model"], r["encoding"], "failed")].append(r["failed"])
    models = sorted({r["model"] for r in rows})
    summary = []
    for st in ("standard", "hard", "all"):
        for m in models:
            csv_tok = dict(wbtok.get((st, m, "csv"), []))
            for e in ORDER:
                if (st, m, e, "all") not in agg:
                    continue
                row = {"set": st, "model": m, "encoding": e, "n": len(agg[(st, m, e, "all")]),
                       "failed_questions": sum(agg[(st, m, e, "failed")])}
                for t in TASKS + ["all"]:
                    v = agg.get((st, m, e, t))
                    row[t] = round(100 * sum(v) / len(v), 1) if v else None
                for t in ("trace", "impact", "hardcode"):
                    v = agg.get((st, m, e, t + "_exact"))
                    row[t + "_exact"] = round(100 * sum(v) / len(v), 1) if v else None
                wt = dict(wbtok.get((st, m, e), []))
                if wt and csv_tok:
                    row["tokens"] = sum(wt.values())
                    row["tokens_vs_csv"] = round(sum(wt.values()) / sum(csv_tok.values()), 2)
                summary.append(row)
    keys = ["set", "model", "encoding", "n", "failed_questions", "lookup", "address", "trace", "impact", "hardcode", "all",
            "trace_exact", "impact_exact", "hardcode_exact", "tokens", "tokens_vs_csv"]
    with open(RESULTS / "summary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader(); w.writerows(summary)
    for r in summary:
        print("  ".join(f"{k}={r.get(k)}" for k in keys))


if __name__ == "__main__":
    main()
