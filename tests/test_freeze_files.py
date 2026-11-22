"""Files frozen for the posted benchmark run and its addendum keep their recorded bytes.

benchmarks/freeze/benchmark.json and addendum.json record the SHA-256 of every file the posted digests cover. Editing
one of them (even a comment) means freeze.py no longer reproduces the posted digest. Dataset files rebuilt by scripts
are not committed, so they are skipped here.
"""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


@pytest.mark.parametrize("manifest", ["benchmark.json", "addendum.json"])
def test_frozen_files_keep_their_bytes(manifest):
    files = json.loads((ROOT / "benchmarks" / "freeze" / manifest).read_text())["files"]
    changed = [p for p, h in files.items()
               if (ROOT / p).exists() and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
    assert not changed, f"frozen files changed: {changed}"
