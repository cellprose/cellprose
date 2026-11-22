#!/usr/bin/env python3
"""Reference encoder: `encode.py workbook.json` prints the .sheet.md text on stdout; warnings go to stderr."""
import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _xlsx import build_pair  # noqa: E402

from cellprose.writer import Options, dumps_workbook  # noqa: E402


def main(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    fwb, vwb = build_pair(doc)
    opts = doc.get("options", {})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        text = dumps_workbook(fwb, vwb, Options(max_rows=opts.get("max_rows")))
    for w in caught:
        print(f"warning: {w.message}", file=sys.stderr)
    sys.stdout.buffer.write(text.encode("utf-8"))


if __name__ == "__main__":
    main(sys.argv[1])
