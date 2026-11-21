"""Round trip on real public workbooks (tests/real/). Committed files are always tested; the Damodaran files, which
have no redistribution licence, are downloaded only when CELLPROSE_FETCH_REAL=1 and checked against their SHA-256."""
import hashlib
import json
import re
import os
import urllib.request
from pathlib import Path

import pytest

import cellprose
from cellprose.recalc import soffice

import corpus

REAL = Path(__file__).parent / "real"
MANIFEST = json.loads((REAL / "manifest.json").read_text())
CACHE = Path(__file__).parent.parent / ".pytest_cache" / "real-workbooks"
needs_lo = pytest.mark.skipif(soffice() is None, reason="LibreOffice is needed to recompute formulas")

# Files that do not round-trip today, with the cause. Each is strict-xfail: when a fix lands the test XPASSes and
# fails the run, which is the cue to delete the entry. Fixing these is writer/reader work, not part of this corpus.
KNOWN = {
    "dam_fcffginzu.xlsx": "round trip changes cell content (not yet triaged)",
    "dam_fcffsimpleginzu.xlsx": "round trip changes cell content (not yet triaged)",
    "dam_fcffsimpleginzuCorona.xlsx": "round trip changes cell content (not yet triaged)",
    "dam_capstru.xlsx": "round trip changes cell content (not yet triaged)",
    "dam_ctryprem.xlsx": "round trip changes cell content (not yet triaged)",
}


def fetch(entry):
    path = CACHE / entry["file"]
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(entry["source_url"], timeout=120) as r:
            path.write_bytes(r.read())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], f"{entry['file']}: download changed"
    return path


def cases():
    skip = pytest.mark.skipif(os.environ.get("CELLPROSE_FETCH_REAL") != "1", reason="set CELLPROSE_FETCH_REAL=1 to download")
    return ([pytest.param(e, id=e["file"]) for e in MANIFEST["committed"]]
            + [pytest.param(e, id=e["file"], marks=skip) for e in MANIFEST["fetch"]])


def test_committed_files_match_the_manifest():
    for e in MANIFEST["committed"]:
        assert hashlib.sha256((REAL / e["file"]).read_bytes()).hexdigest() == e["sha256"], e["file"]
        assert e["licence"] and e["source_url"], e["file"]
    assert {p.name for p in REAL.glob("*.xlsx")} == {e["file"] for e in MANIFEST["committed"]}


@needs_lo
@pytest.mark.parametrize("entry", cases())
def test_real_workbook_roundtrip(entry, tmp_path, request):
    if entry["file"] in KNOWN:
        request.applymarker(pytest.mark.xfail(strict=True, reason=KNOWN[entry["file"]]))
    src = REAL / entry["file"] if (REAL / entry["file"]).exists() else fetch(entry)
    first = cellprose.dumps(src)
    out = tmp_path / "rt"
    out.mkdir()
    decoded = cellprose.load(first).to_xlsx(out / src.name)
    # the "not carried" note counts what the format drops, so a decoded copy no longer has anything to count
    assert cellprose.dumps(decoded) == re.sub(r"(; )?not carried: [^';]*", "", first).replace("note: ''\n", "").replace("note: '; ", "note: '")
    assert corpus.content(decoded) == corpus.content(src)
