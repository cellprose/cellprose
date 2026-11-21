#!/usr/bin/env python3
"""Rewrite every case's expected files from the Python reference implementation.

    python conformance/reference/regenerate.py            # rewrite, then review `git diff conformance/`
    python conformance/reference/regenerate.py --check    # exit 1 if any file would change

The expected files are the contract, so a change to one is a format decision: read the diff against docs/SPEC.md before
committing, and update the spec first when the format itself changes."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE.parent / "cases"


def run(script, path):
    r = subprocess.run([sys.executable, str(HERE / script), str(path)], capture_output=True)
    return r


def main(check):
    stale = []
    for d in sorted(p for p in CASES.iterdir() if p.is_dir()):
        meta = json.loads((d / "case.json").read_text(encoding="utf-8"))
        jobs = []
        if "write" in meta:
            jobs.append(("encode.py", meta["write"]["input"], meta["write"]["expected"]))
        rd = meta.get("read", {})
        if "expected" in rd:
            jobs.append(("decode.py", rd["input"], rd["expected"]))
        for script, src, dest in jobs:
            r = run(script, d / src)
            if r.returncode != 0:
                sys.exit(f"{d.name}: {script} failed: {r.stderr.decode()[-400:]}")
            target = d / dest
            if not target.exists() or target.read_bytes() != r.stdout:
                stale.append(f"{d.name}/{dest}")
                if not check:
                    target.write_bytes(r.stdout)
    for s in stale:
        print(("would change " if check else "rewrote ") + s)
    if check and stale:
        sys.exit(1)
    print("all expected files match the reference implementation" if not stale else "")


if __name__ == "__main__":
    main("--check" in sys.argv)
