"""Freeze manifest for docs/PROTOCOL_ADDENDUM.md: every file of the benchmark freeze (freeze.paths()), plus the
addendum protocol, the compared arm's tools and the addendum scripts, with one digest computed as freeze.py does.
Writes benchmarks/freeze/addendum.json; freeze.py and freeze/benchmark.json are not changed.

    python3 benchmarks/freeze_addendum.py
"""
import hashlib
import json
from pathlib import Path

import freeze

ROOT, BENCH = freeze.ROOT, freeze.BENCH


def paths():
    return freeze.paths() + [ROOT / "docs" / "PROTOCOL_ADDENDUM.md", ROOT / "src" / "cellprose" / "tools.py",
                             BENCH / "addendum_noimpact.py", Path(__file__).resolve()]


def main():
    files = {str(p.relative_to(ROOT)) + ("#cells" if freeze.by_content(p) else ""):
             freeze.cell_sha256(p) if freeze.by_content(p) else freeze.sha(p) for p in paths()}
    digest = hashlib.sha256("".join(f"{k} {v}\n" for k, v in sorted(files.items())).encode()).hexdigest()
    (BENCH / "freeze" / "addendum.json").write_text(json.dumps(
        {"digest": digest, "how": "sha256 of the lines '<path> <sha256>\\n' sorted by path", "files": files},
        indent=1) + "\n")
    print(f"addendum digest {digest} over {len(files)} files")


if __name__ == "__main__":
    main()
