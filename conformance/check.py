#!/usr/bin/env python3
"""Cellprose v0.3 conformance checker. Python 3.8+ standard library only; it runs your implementation as a program,
so the implementation can be written in any language. See README.md.

    python conformance/check.py --encoder "node encode.js" --decoder "./decode"

--encoder CMD   Writer under test. Run as `CMD <workbook.json>`; it must print the .sheet.md text on stdout.
--decoder CMD   Reader under test. Run as `CMD <file.sheet.md>`; it must print the decoded workbook as JSON on stdout,
                or exit non-zero for a file a reader must reject.
--only ID ...   Run only these cases (id or unique prefix, e.g. 07).
--list          List the cases and exit.
--validate      Check that the kit itself is complete and well-formed, and exit.
-v              Show a diff for every failure (default: first 40 lines).

Exit status: 0 when every selected check passed, 1 when any failed, 2 on a usage error.
"""
import argparse
import difflib
import json
import shlex
import subprocess
import sys
from pathlib import Path

CASES = Path(__file__).resolve().parent / "cases"
TIMEOUT = 120


# ----------------------------------------------------------------------------------------------- kit
def load_cases():
    cases = []
    for d in sorted(p for p in CASES.iterdir() if p.is_dir()):
        meta = json.loads((d / "case.json").read_text(encoding="utf-8"))
        cases.append((d.name, d, meta))
    return cases


def validate(cases):
    problems = []
    for cid, d, meta in cases:
        for key in ("title", "spec"):
            if not meta.get(key):
                problems.append(f"{cid}: case.json lacks '{key}'")
        if "write" not in meta and "read" not in meta:
            problems.append(f"{cid}: case.json has neither 'write' nor 'read'")
        files = []
        for side in ("write", "read"):
            s = meta.get(side)
            if not s:
                continue
            files += [s["input"]] + ([s["expected"]] if "expected" in s else [])
            if "expected" not in s and not s.get("rejects"):
                problems.append(f"{cid}: '{side}' needs 'expected' or 'rejects'")
        for f in files:
            if not (d / f).is_file():
                problems.append(f"{cid}: missing file {f}")
            elif f.endswith(".json"):
                try:
                    json.loads((d / f).read_text(encoding="utf-8"))
                except ValueError as e:
                    problems.append(f"{cid}: {f} is not valid JSON ({e})")
        on_disk = {p.name for p in d.iterdir()}
        for extra in sorted(on_disk - set(files) - {"case.json"}):
            problems.append(f"{cid}: file {extra} is not used by case.json")
    return problems


# ----------------------------------------------------------------------------------------------- running
class Fail(Exception):
    pass


def run(command, path):
    try:
        return subprocess.run(shlex.split(command) + [str(path)], capture_output=True, timeout=TIMEOUT)
    except FileNotFoundError as e:
        return Fail(f"cannot run {command!r}: {e}")
    except subprocess.TimeoutExpired:
        return Fail(f"{command!r} did not finish within {TIMEOUT}s")


def tail(raw, n=300):
    text = raw.decode("utf-8", "replace").strip()
    return text[-n:]


def diff(expected, actual, names, limit):
    lines = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(), names[0], names[1], lineterm="", n=2))
    more = len(lines) - limit
    return "\n".join(lines[:limit] + ([f"... {more} more diff lines (use -v)"] if more > 0 else []))


def check_encode(d, w, command, limit):
    r = run(command, d / w["input"])
    if isinstance(r, Fail):
        return str(r)
    if r.returncode != 0:
        return f"exit status {r.returncode}; stderr: {tail(r.stderr)}"
    expected = (d / w["expected"]).read_bytes()
    if r.stdout != expected:
        try:
            return "output differs from expected.sheet.md:\n" + diff(
                expected.decode("utf-8"), r.stdout.decode("utf-8"), ("expected", "actual"), limit)
        except UnicodeDecodeError:
            return "output is not valid UTF-8"
    if w.get("warns") and not r.stderr.strip():
        return "the spec requires a warning for this workbook, but nothing was written to stderr"
    return None


def normalize(doc):
    """The decoded form with its defaults filled in, so equal workbooks compare equal."""
    def cell(c):
        c = dict(c)
        if c.get("fmt") == "General":
            del c["fmt"]
        return c
    return {"sheets": [{"name": s["name"], "state": s.get("state", "visible"), "freeze": s.get("freeze"),
                        "merges": sorted(s.get("merges", [])), "names": s.get("names", {}),
                        "cells": {a: cell(c) for a, c in s.get("cells", {}).items()},
                        **({"comments": s["comments"]} if s.get("comments") else {}),
                        **({"validations": s["validations"]} if s.get("validations") else {})} for s in doc["sheets"]],
            "names": doc.get("names", {})}


def canon(x):
    """JSON text in which booleans, integers and floats stay distinct from each other but 5 and 5.0 are the same."""
    def walk(v):
        if isinstance(v, bool) or v is None or isinstance(v, str):
            return v
        if isinstance(v, (int, float)):
            return {"$num": repr(float(v))}
        if isinstance(v, list):
            return [walk(i) for i in v]
        return {k: walk(i) for k, i in sorted(v.items())}
    return json.dumps(walk(x), indent=1, ensure_ascii=False, sort_keys=True)


def check_decode(d, rd, command, limit):
    r = run(command, d / rd["input"])
    if isinstance(r, Fail):
        return str(r)
    if rd.get("rejects"):
        return None if r.returncode != 0 else "the file must be rejected, but the decoder exited with status 0"
    if r.returncode != 0:
        return f"exit status {r.returncode}; stderr: {tail(r.stderr)}"
    try:
        actual = json.loads(r.stdout.decode("utf-8"))
        want, got = canon(normalize(json.loads((d / rd["expected"]).read_text(encoding="utf-8")))), canon(normalize(actual))
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        return f"stdout is not a decoded workbook ({type(e).__name__}: {e}): {tail(r.stdout)}"
    if want != got:
        return "decoded workbook differs from decoded.json:\n" + diff(want, got, ("expected", "actual"), limit)
    if rd.get("warns") and not r.stderr.strip():
        return "the spec requires a warning for this file, but nothing was written to stderr"
    return None


# ----------------------------------------------------------------------------------------------- main
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--encoder")
    p.add_argument("--decoder")
    p.add_argument("--only", nargs="+", metavar="ID")
    p.add_argument("--list", action="store_true")
    p.add_argument("--validate", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    cases = load_cases()
    if a.validate:
        problems = validate(cases)
        print("\n".join(problems) if problems else f"kit ok: {len(cases)} cases")
        return 1 if problems else 0
    if a.list:
        for cid, _, m in cases:
            sides = "".join(s[0].upper() if s in m else "-" for s in ("write", "read"))
            print(f"{cid:34} [{sides}] {m['spec']:12} {m['title']}")
        return 0
    if not (a.encoder or a.decoder):
        p.error("give --encoder and/or --decoder (or --list / --validate)")
    if a.only:
        picked = []
        for want in a.only:
            hits = [c for c in cases if c[0] == want] or [c for c in cases if c[0].startswith(want)]
            if not hits:
                p.error(f"no case matches {want!r}")
            picked += hits
        cases = picked

    limit = 10 ** 6 if a.verbose else 40
    counts = {"pass": 0, "fail": 0}
    for cid, d, meta in cases:
        for side, command, fn in (("write", a.encoder, check_encode), ("read", a.decoder, check_decode)):
            if not command or side not in meta:
                continue
            problem = fn(d, meta[side], command, limit)
            kind = "encode" if side == "write" else "decode"
            if problem is None:
                counts["pass"] += 1
                print(f"PASS  {cid:34} {kind}")
            else:
                counts["fail"] += 1
                print(f"FAIL  {cid:34} {kind}  ({meta['title']}; spec {meta['spec']})")
                print("      " + problem.replace("\n", "\n      "))
    total = counts["pass"] + counts["fail"]
    print(f"\n{counts['pass']}/{total} checks passed" + ("" if not counts["fail"] else f", {counts['fail']} failed"))
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
