"""Build `dev_`, a development set of large real workbooks (experiments/E33).

  python3 external/devlarge.py select   # seeded draw of N workbooks from the project's real-workbooks folder
  python3 external/devlarge.py build    # questions, ground truth, review.md, encodings (as realworld2.py)
  python3 external/devlarge.py --data select|build   # the data-heavy set `dev_d_` in external/devdata (below)

Why: the 14 synthetic dev workbooks are all small, and E32 showed the xlsx-reading agent beats the one-shot file only
on large files (above about 40k characters). Changes for large files have to be tuned on large files that are not
in any held-out set.

Rules (fixed before any model call on this set):
  - Pool: every .xlsx and .xls under /mnt/project-files/real-workbooks/{files,files2,files3} (.xls converted by
    LibreOffice).
  - Excluded: every file a held-out set selected (rw_, rw2_, rw3_), matched by SHA-256, by file name and by base name
    (the stem without the dam_ / enron__author__id__ prefixes and case), so an .xls and its .xlsx twin both go.
    Files that were only screened and rejected by rw2_ or rw3_ stay in the pool: no model has seen them.
  - Eligible: realworld2.eligible (same question rules, MAX_TOKENS 100k) and a v0.3 text of at least MIN_TOKENS
    o200k tokens (about 20k characters), so every workbook is on the large side of E32's crossover.
  - A seeded shuffle (SEED), at most one Enron file per author, until N are kept.
--data2 (E34): the --data rules with seed 20261110, N = 20, and the dev_ and dev_d_ files also excluded; names dev_e_.
--data (E33 follow-up): the same rules with SEED_DATA, the files the first draw kept also excluded, and one more test
(the project folder has no eligible file left that passes it, so --enron draws from the full Enron corpus, figshare
1221767, CC BY 4.0, skipping every author rw2_ or rw3_ selected):
the v0.3 text is at most DATA_RATIO times the CSV text in o200k tokens, so values, not formulas, make up most of it.
Names start `dev_d_`.
Questions are the realworld2 rules unchanged (6 per workbook). The names start with `dev_`, which
runner/split.py treats as development (split.json itself is hashed by freeze/tier2.json and is not edited).
"""
import argparse
import json
import random
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import realworld2 as rw2  # noqa: E402

OUT = HERE / "devlarge"
SEED = 20261108
N = 10
MIN_TOKENS = 6_000
SEED_DATA, DATA_RATIO = 20261109, 1.3
MAX_BYTES, SCREEN_SECONDS = 2_000_000, 120     # added after the first --enron pass stalled on one file (E33)
PREFIX = "dev_"
POOL = [Path("/mnt/project-files/real-workbooks") / d for d in ("files", "files2", "files3")]
rw2.OUT, rw2.SEED = OUT, SEED
rw2.DEFAULT_FILES = [str(OUT / "files")]     # local copies (not in git); build copies Enron ones to sources/


def base(name: str) -> str:
    stem = Path(name).stem.lower()
    if stem.startswith("enron__"):
        stem = stem.split("__", 3)[-1]
    elif stem.count("__") >= 2:          # a file straight from the Enron corpus: author__id__name
        stem = stem.split("__", 2)[-1]
    return re.sub(r"^dam_", "", stem)


def author_of(name: str) -> str | None:
    if name.startswith("enron__"):
        return name.split("__")[1]
    return name.split("__")[0] if name.count("__") >= 2 else None


def excluded():
    shas, names, bases = set(), set(), set()
    for s in ("realworld", "realworld2", "realworld3"):
        for w in json.loads((HERE / s / "manifest.json").read_text())["workbooks"].values():
            for k in ("sha256", "original_sha256"):
                if w.get(k):
                    shas.add(w[k])
            for k in ("source_file", "file", "original"):
                if w.get(k):
                    names.add(Path(w[k]).name)
                    bases.add(base(w[k]))
    return shas, names, bases


def heldout_authors() -> set[str]:
    """Enron authors any held-out set selected: their other files stay out of dev sets too."""
    out = set()
    for s in ("realworld2", "realworld3"):
        for w in json.loads((HERE / s / "manifest.json").read_text())["workbooks"].values():
            for k in ("file", "original"):
                if w.get(k) and author_of(Path(w[k]).name):
                    out.add(author_of(Path(w[k]).name))
    return out


def select(a):
    shas, names, bases = excluded()
    if a.data:
        prev = [HERE / "devlarge" / "selection.json"] + ([HERE / "devdata" / "selection.json"] if a.data2 else [])
        first = [w for f in prev for w in json.loads(f.read_text())["workbooks"].values()]
        for w in first:
            shas.add(w["original_sha256"]); names.add(w["original"]); bases.add(base(w["original"]))
    (OUT / "files").mkdir(parents=True, exist_ok=True)
    dirs = [Path(a.enron)] if getattr(a, "enron", None) else POOL
    pool = sorted(p for d in dirs for p in d.rglob("*") if p.suffix.lower() in (".xls", ".xlsx"))
    banned_authors = heldout_authors()
    known = {}
    if getattr(a, "resume", None):     # lines "<file>: <reason>" printed by an earlier pass; only rejections are reused
        for line in Path(a.resume).read_text().splitlines():
            f, sep, why = line.rpartition(": ")
            if sep and why != "ok" and f.lower().endswith((".xls", ".xlsx")):
                known[f] = why
    random.Random(rw2.SEED).shuffle(pool)
    chosen, log, authors, seen_bases = {}, [], set(), set()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for p in pool:
            if len(chosen) >= N:
                break
            b = base(p.name)
            if p.name in known:          # --resume: the reason an earlier pass of this same draw recorded
                log.append({"file": p.name, "eligible": False, "reason": known[p.name]})
                continue
            if rw2.sha256(p) in shas or p.name in names or b in bases or b in seen_bases:
                continue
            author = author_of(p.name)
            if author and (author in authors or author in banned_authors):
                continue
            try:
                x = rw2.convert(p, td / "conv") if p.suffix.lower() == ".xls" else p
            except Exception:
                log.append({"file": p.name, "eligible": False, "reason": "conversion failed"})
                continue
            name = PREFIX + rw2.slug(b)
            if x.stat().st_size > MAX_BYTES:
                log.append({"file": p.name, "eligible": False, "reason": f"over {MAX_BYTES} bytes"})
                continue
            import signal
            signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError()))
            signal.alarm(SCREEN_SECONDS)
            try:
                good, why, info = rw2.eligible(x, name, td)
            except TimeoutError:
                good, why, info = False, f"screening took over {SCREEN_SECONDS} s", {}
            except Exception as e:      # e.g. LibreOffice's recalculated copy is unreadable by openpyxl
                good, why, info = False, f"screening failed: {type(e).__name__}", {}
            finally:
                signal.alarm(0)
            if good and info["tokens_o200k_v03"] < MIN_TOKENS:
                good, why = False, f"{info['tokens_o200k_v03']} tokens (< {MIN_TOKENS})"
            if good and a.data:
                import tiktoken
                n_csv = len(tiktoken.get_encoding("o200k_base").encode(rw2.encode(x, "csv"), disallowed_special=()))
                ratio = info["tokens_o200k_v03"] / max(n_csv, 1)
                info["v03_over_csv"] = round(ratio, 3)
                if ratio > DATA_RATIO:
                    good, why = False, f"formula-heavy: v0.3 is {ratio:.2f}x CSV (> {DATA_RATIO})"
            log.append({"file": p.name, "eligible": good, "reason": why})
            print(f"{p.name}: {why}", flush=True)
            if not good:
                continue
            seen_bases.add(b)
            if author:
                authors.add(author)
            out = OUT / "files" / ((f"enron__{p.stem}" if author and not p.name.startswith("enron__") else p.stem) + ".xlsx")
            shutil.copy(x, out)
            src = "enron" if author else "damodaran" if p.name.startswith("dam_") or "damodaran" in str(p) else "other"
            chosen[name] = {"source": src, "file": out.name, "sha256": rw2.sha256(out), "original": p.name,
                            "original_sha256": rw2.sha256(p), **info}
    (OUT / "selection.json").write_text(json.dumps(
        {"about": "Written by external/devlarge.py select; the rule is in that file's docstring.", "seed": rw2.SEED,
         "workbooks": dict(sorted(chosen.items())), "screened": log}, indent=1) + "\n")
    print(f"{len(chosen)} kept; {len(log)} screened")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "build", "check"])
    ap.add_argument("--files")
    ap.add_argument("--only")
    ap.add_argument("--enron", help="with --data: draw from this Enron corpus folder (figshare 1221767) instead")
    ap.add_argument("--resume", help="stdout log of an earlier select pass of the same draw (rejections are reused)")
    ap.add_argument("--data2", action="store_true", help="E34: a second data-heavy set, dev_e_ (external/devdata2), 20 files")
    ap.add_argument("--data", action="store_true", help="the data-heavy set dev_d_ (external/devdata)")
    a = ap.parse_args(argv)
    if a.data2:                 # E34: a second data-heavy draw, 20 files, dev_ and dev_d_ files excluded
        a.data = True
        global N, SEED_DATA
        N, SEED_DATA = 20, 20261110
    if a.data:
        global OUT, PREFIX
        OUT, PREFIX = (HERE / "devdata2", "dev_e_") if a.data2 else (HERE / "devdata", "dev_d_")
        rw2.OUT, rw2.SEED, rw2.DEFAULT_FILES = OUT, SEED_DATA, [str(OUT / "files")]
    if a.mode == "select":
        return select(a)
    return rw2.build(a, check=a.mode == "check")


if __name__ == "__main__":
    sys.exit(main() or 0)
