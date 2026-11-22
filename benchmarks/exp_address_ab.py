"""E31: small A/B of row-label layouts for the "one column to the right" address fault (docs/PROTOCOL.md is untouched).

  python3 exp_address_ab.py gen                       # writes results/e31_address_ab/{questions,encoded}
  python3 exp_address_ab.py run --models haiku55 --reps 2 [--estimate-only]
  python3 exp_address_ab.py report

Development only, not a protocol run: the workbooks are the 17 `rw_` ones (already seen twice) and the questions are the
17 committed address questions plus 6 extra address questions per table workbook, drawn by rule (rows at fixed
fractions, target columns cycled), with ground truth read from the .xlsx. Variants are made offline from the shipped
v0.3 text by a pure text transform of the table blocks. Same system prompt and answer rules as runner/prompts.py,
no prompt caching, every token priced uncached.
"""
import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE / "external" / "realworld"
import os
SET_B = os.environ.get("E31_SET") == "b"      # round 3: fresh rows and columns, only four variants
OUT = HERE / "results" / ("e31b_address_retest" if SET_B else "e31_address_ab")
FRACS = (0.05, 0.2, 0.5, 0.8, 0.95, 0.35) if SET_B else (0.1, 0.3, 0.4, 0.6, 0.7, 0.9)
VARIANTS = ["v03", "hdr_row", "row_end", "addr_label", "repeat_hdr", "note", "note_short", "note_each", "note_ex"]
if os.environ.get("E31_SET") == "b":
    VARIANTS = ["v03", "note", "note_each", "note_ex"]
NOTE_SHORT = "Rows: row number, then columns A, B, C in order.\n\n"
NOTE = "Note: the first field of each table row is its row number, not a cell; column A is the second field.\n\n"


def _tables(lines):
    """Yield (start, end) line spans of compact tables: a `#|A|B..` header, a `-|-` rule, rows up to a blank line."""
    i = 0
    while i < len(lines):
        if re.match(r"^#\|[A-Z]", lines[i]) and i + 1 < len(lines) and lines[i + 1].startswith("-|"):
            j = i + 2
            while j < len(lines) and lines[j].strip():
                j += 1
            yield i, j
            i = j
        else:
            i += 1


def cols_first(text):
    for ln in text.split("\n"):
        if re.match(r"^#\|[A-Z]", ln):
            return ln.split("|")[1:]
    return ["A", "B"]


def transform(text: str, variant: str) -> str:
    if variant == "v03":
        return text
    lines = text.split("\n")
    out, pos = [], 0
    for s, e in _tables(lines):
        out += lines[pos:s]
        head, rule, rows = lines[s], lines[s + 1], lines[s + 2:e]
        cols = head.split("|")[1:]
        wide = len(cols) > 6
        if variant == "hdr_row":
            out += ["row|" + "|".join(cols), rule] + rows
        elif variant == "row_end":
            out += ["|".join(cols) + "|#", "-|" * len(cols) + "-"]
            out += [("|".join(r.split("|")[1:]) + "|" + r.split("|")[0]) for r in rows]
        elif variant == "addr_label":
            out += [head, rule] + [f"{cols[0]}{r.split('|')[0]}|" + "|".join(r.split("|")[1:]) for r in rows]
        elif variant == "repeat_hdr":
            out += [head, rule]
            for k, r in enumerate(rows, 1):
                out.append(r)
                if wide and k % 20 == 0 and k != len(rows):
                    out.append(head)
        elif variant in ("note", "note_short", "note_ex"):
            out += [head, rule] + rows
        elif variant == "note_each":
            out += [NOTE_SHORT.strip(), head, rule] + rows
        else:
            raise SystemExit(variant)
        pos = e
    out += lines[pos:]
    t = "\n".join(out)
    if variant in ("note", "note_short", "note_ex"):
        note = {"note": NOTE, "note_short": NOTE_SHORT, "note_ex": NOTE}[variant]
        if variant == "note_ex":
            for s_, e_ in _tables(text.split("\n")):
                f = text.split("\n")[s_ + 2].split("|")
                hc = text.split("\n")[s_].split("|")[1:]
                if len(f) > 3 and len(hc) > 1:
                    note = NOTE.rstrip("\n") + f" Example: the row `{f[0]}|{f[1][:20]}|{f[2][:20]}|...` has {hc[0]}{f[0]}={f[1][:20]}, {hc[1]}{f[0]}={f[2][:20]}.\n\n"
                    break
        t = t.replace("\n---\n\n", "\n---\n\n" + note, 1)
    return t


def gen():
    sys.path.insert(0, str(HERE / "external"))
    sys.path.insert(0, str(HERE))
    import realworld as rw
    spec = json.loads((CORPUS / "spec.json").read_text())
    srcs = rw.source_manifest()
    (OUT / "questions").mkdir(parents=True, exist_ok=True)
    (OUT / "encoded").mkdir(exist_ok=True)
    for name, swb in spec["workbooks"].items():
        qs = [q for q in json.loads((CORPUS / "questions" / f"{name}.json").read_text()) if q["type"] == "address"]
        for q in qs:
            q["id"] = "q" + str(len(qs) and qs.index(q) + 1)
        if "table" in swb:
            cfg = swb["table"]
            book = rw.Book(rw.find_source(srcs[swb["file"]], None, Path("/tmp/fetch")))
            ws = book.v[cfg["sheet"]]
            hdr, keys = cfg["header_row"], cfg["key"] if isinstance(cfg["key"], list) else [cfg["key"]]
            first, last = hdr + 1, ws.max_row
            while last > first and all(ws.cell(last, c).value is None for c in range(1, ws.max_column + 1)):
                last -= 1
            n = last - first + 1
            cols = [c for c in range(1, ws.max_column + 1) if ws.cell(hdr, c).value not in (None, "")]
            for k, fr in enumerate(FRACS):
                col = rw.L(cols[(k * 3 + (4 if SET_B else 2)) % len(cols)])
                r = first + int(fr * n)
                while r <= last:
                    kv = {c: ws[f"{c}{r}"].value for c in keys}
                    ans = ws[f"{col}{r}"].value
                    if (all(v is not None for v in kv.values()) and len(book.rows_matching(cfg["sheet"], kv, first)) == 1
                            and ans is not None and not hasattr(ans, "isoformat")):
                        break
                    r += 1
                else:
                    continue
                head = " ".join(str(ws[f"{col}{hdr}"].value or "").split())
                where = " and ".join(f"'{' '.join(str(ws[f'{c}{hdr}'].value).split())}' is "
                                     f"{kv[c].strip()!r}" if isinstance(kv[c], str) else
                                     f"'{' '.join(str(ws[f'{c}{hdr}'].value).split())}' is {rw.clean(kv[c])!r}" for c in keys)
                cell = f"{cfg['sheet']}!{col}{r}"
                qs.append({"type": "address", "id": f"q{len(qs) + 1}", "cell": cell, "truth": cell,
                           "q": f"In the sheet '{cfg['sheet']}', which cell holds '{head}' for the row where {where}? "
                                "Give its cell address."})
        (OUT / "questions" / f"{name}.json").write_text(json.dumps(qs, indent=1, default=str) + "\n")
        text = (CORPUS / "encoded" / f"{name}.cellprose_v03_nolegend.txt").read_text()
        for v in VARIANTS:
            (OUT / "encoded" / f"{name}.{v}.txt").write_text(transform(text, v))
        print(name, len(qs), "questions")


def build_prompt(wb, v):
    sys.path.insert(0, str(HERE))
    from runner.prompts import KIND
    qs = json.loads((OUT / "questions" / f"{wb}.json").read_text())
    text = (OUT / "encoded" / f"{wb}.{v}.txt").read_text()
    parts = [f'<workbook format="Sheetmark">\n{text}\n</workbook>\n',
             "Answer each question. Rules:\n"
             "- Cell addresses use A1 notation qualified with the sheet name, e.g. Sheet1!B5.\n"
             "- For list questions, return a JSON array of cell addresses; ranges like Sheet1!B2:B9 are allowed. "
             "Return [] if there are none.\n"
             "- For value questions, return a number without units or thousands separators, or a short string.\n"
             "- If the workbook does not give enough information, give your best guess.\n\nQuestions:"]
    parts += [f"{q['id']} ({KIND[q['type']]}): {q['q']}" for q in qs]
    parts.append('\nReturn JSON like {"q1": ..., "q2": ...} with every question id.')
    return "\n".join(parts)


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except Exception:
        return {}


def run(a):
    sys.path.insert(0, str(HERE))
    from runner import models
    from runner.prompts import SYSTEM
    from runner.providers import get_provider
    wbs = sorted(p.stem for p in (OUT / "questions").glob("*.json"))
    jobs = [(m, wb, v, r) for m in a.models.split(",") for r in range(a.reps) for v in VARIANTS for wb in wbs]
    rawdir = OUT / "raw"
    jobs = [j for j in jobs if not (rawdir / j[0] / f"{j[1]}.{j[2]}.r{j[3]}.json").exists()]
    cfgs = {m: models.get(m) for m in a.models.split(",")}
    est = 0.0
    for m, wb, v, r in jobs:
        n = len(build_prompt(wb, v)) / 3.2          # characters per token, conservative
        c = cfgs[m]
        est += n * c.price_in / 1e6 + c.est_output_tokens * c.price_out / 1e6
    print(f"{len(jobs)} calls to run; rough estimate ${est:.2f} (character-based)")
    if a.estimate_only or not jobs:
        return
    if est > a.max_usd:
        raise SystemExit(f"estimate above --max-usd {a.max_usd}")
    prov = {m: get_provider(c) for m, c in cfgs.items()}
    spend, lock = [0.0], threading.Lock()

    def one(j):
        m, wb, v, r = j
        with lock:
            if spend[0] >= a.max_usd:
                return
        res = prov[m].complete(cfgs[m], SYSTEM, build_prompt(wb, v))
        u = res.usage
        cfg = cfgs[m]
        pin, pout = cfg.price_in, cfg.price_out
        if cfg.long_threshold and u.total_input > cfg.long_threshold:
            pin, pout = cfg.long_price_in, cfg.long_price_out
        cost = u.total_input * pin / 1e6 + (u.output_tokens) * pout / 1e6
        with lock:
            spend[0] += cost
        p = rawdir / m / f"{wb}.{v}.r{r}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"text": res.text, "input": u.total_input, "output": u.output_tokens, "cost": cost}))
        print(f"{m} {wb}.{v}.r{r} in={u.total_input} cost=${cost:.4f}", flush=True)

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(one, jobs))
    print(f"spend ${spend[0]:.3f}")


def norm(s):
    return re.sub(r"\s+", "", str(s)).upper().replace("'", "")


def report():
    import collections
    stats = collections.defaultdict(lambda: {"ok": 0, "n": 0, "in": 0, "cost": 0.0, "calls": 0, "plus1": 0})
    for p in sorted((OUT / "raw").glob("*/*.json")):
        m = p.parent.name
        wb, v, _ = p.name[:-5].rsplit(".", 2)
        d = json.loads(p.read_text())
        ans = parse(d["text"])
        s = stats[(m, v)]
        s["in"] += d["input"]; s["cost"] += d["cost"]; s["calls"] += 1
        for q in json.loads((OUT / "questions" / f"{wb}.json").read_text()):
            s["n"] += 1
            got = norm(ans.get(q["id"], ""))
            if got == norm(q["truth"]):
                s["ok"] += 1
            else:
                sheet, cell = q["truth"].rsplit("!", 1)
                mm = re.match(r"([A-Z]+)(\d+)$", cell)
                if mm and got.endswith(mm.group(2)) and len(got) > 0:
                    s["plus1"] += 1
    print("| Model | Variant | Address accuracy | Wrong (same row, other column) | Mean input tokens per call | Cost per call |")
    print("| --- | --- | --- | --- | --- | --- |")
    for (m, v), s in sorted(stats.items(), key=lambda kv: (kv[0][0], VARIANTS.index(kv[0][1]))):
        print(f"| {m} | {v} | {100 * s['ok'] / s['n']:.1f}% ({s['ok']}/{s['n']}) | {s['plus1']} | "
              f"{s['in'] / s['calls']:.0f} | ${s['cost'] / s['calls']:.4f} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["gen", "run", "report"])
    ap.add_argument("--models", default="haiku55")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--max-usd", type=float, default=2.0)
    ap.add_argument("--estimate-only", action="store_true")
    a = ap.parse_args()
    {"gen": gen, "run": lambda: run(a), "report": report}[a.mode]()
