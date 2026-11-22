"""Build `rw3_`, the fresh pilot set for the re-pilot after the Tier 1 gate failure (experiments/E32).

  python3 external/realworld3.py select --enron DIR     # 15 Enron files from authors rw2_ never used
  python3 external/realworld3.py build  [--files DIR]   # questions, ground truth, review.md, encodings
  python3 external/realworld3.py check  [--files DIR]

Same rules as `realworld2.py` (imported, not copied; that file is frozen for Tier 2 and is not edited), with a new seed
and one exclusion: every author and every file that `realworld2/selection.json` selected or screened is skipped.
No Damodaran file is left (all 49 were selected or screened in rw2_), so the set is Enron only: 15 workbooks, one per
author, 6 questions each, nothing written by hand. Fixed before any model call on this set.
"""
import argparse
import json
import random
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import realworld2 as rw2  # noqa: E402

OUT = HERE / "realworld3"
SEED = 20261107
N_ENRON = 15
rw2.OUT, rw2.SEED = OUT, SEED
DEFAULT_FILES = ["/mnt/project-files/real-workbooks/files3"]
rw2.DEFAULT_FILES = DEFAULT_FILES


def select(a):
    prev = json.loads((HERE / "realworld2" / "selection.json").read_text())
    skip_files = {Path(x["file"]).name for x in prev["screened"]} | {v.get("original", v["file"]) for v in prev["workbooks"].values()}
    skip_authors = {v["file"].split("__")[1] for v in prev["workbooks"].values() if v["source"] == "enron"} | \
                   {x["file"].partition("__")[0] for x in prev["screened"] if x["source"] == "enron"}
    files = Path(a.out_files)
    files.mkdir(parents=True, exist_ok=True)
    chosen, log = {}, []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        allx = sorted(p for p in Path(a.enron).rglob("*") if p.suffix.lower() in (".xls", ".xlsx"))
        random.Random(SEED).shuffle(allx)
        authors, bases = set(), set()
        for p in allx:
            if len(chosen) >= N_ENRON:
                break
            author, _, rest = p.name.partition("__")
            base = rest.split("__", 1)[-1].lower()
            if p.name in skip_files or author in skip_authors or author in authors or base in bases:
                continue
            try:
                x = rw2.convert(p, td / "conv") if p.suffix.lower() == ".xls" else p
            except Exception:
                log.append({"file": p.name, "source": "enron", "eligible": False, "reason": "conversion failed"})
                continue
            name = "rw3_enron_" + rw2.slug(author)
            good, why, info = rw2.eligible(x, name, td)
            log.append({"file": p.name, "source": "enron", "eligible": good, "reason": why})
            if not good:
                continue
            authors.add(author)
            bases.add(base)
            out = files / f"enron__{p.stem}.xlsx"
            shutil.copy(x, out)
            chosen[name] = {"source": "enron", "file": out.name, "sha256": rw2.sha256(out), "original": p.name,
                            "original_sha256": rw2.sha256(p), "source_url": "https://doi.org/10.6084/m9.figshare.1221767",
                            "licence": "CC BY 4.0 (Hermans and Murphy-Hill, 2015)", **info}
            print(f"kept {name} ({len(log)} screened)", flush=True)
    OUT.mkdir(exist_ok=True)
    (OUT / "selection.json").write_text(json.dumps(
        {"about": "Written by external/realworld3.py select; the rule is in realworld2.py and that file's docstring.",
         "seed": SEED, "excluded_authors_from_rw2": len(skip_authors), "workbooks": dict(sorted(chosen.items())),
         "screened": log}, indent=1) + "\n")
    print(f"{len(chosen)} Enron; {len(log)} files screened")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "build", "check", "freeze"])
    ap.add_argument("--enron")
    ap.add_argument("--out-files", default=DEFAULT_FILES[0])
    ap.add_argument("--files")
    ap.add_argument("--only")
    a = ap.parse_args(argv)
    if a.mode == "select":
        return select(a)
    if a.mode == "freeze":
        return freeze()
    return rw2.build(a, check=a.mode == "check")


def freeze():
    """SHA-256 of everything the re-pilot depends on, and one digest (same method as freeze/tier2.json)."""
    import hashlib
    root = HERE.parent.parent
    paths = [root / "docs" / "PROTOCOL.md", root / "docs" / "SPEC.md", Path(rw2.__file__), Path(__file__),
             root / "src" / "cellprose" / "writer.py", OUT / "selection.json", OUT / "manifest.json"] + \
        sorted((OUT / "questions").glob("*.json")) + sorted((OUT / "sources").glob("*.xlsx"))
    files = {str(p.relative_to(root)): rw2.sha256(p) for p in paths}
    digest = hashlib.sha256("".join(f"{k} {v}\n" for k, v in sorted(files.items())).encode()).hexdigest()
    out = HERE.parent / "freeze" / "pilot2.json"
    out.write_text(json.dumps({"tier": "re-pilot (E32)", "digest": digest,
                               "how": "sha256 of the lines '<path> <sha256>\\n' sorted by path", "files": files}, indent=1) + "\n")
    print(f"re-pilot digest {digest} over {len(files)} files")


if __name__ == "__main__":
    sys.exit(main() or 0)
