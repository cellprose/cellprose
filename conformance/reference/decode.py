#!/usr/bin/env python3
"""Reference decoder: `decode.py file.sheet.md` prints the decoded workbook as JSON on stdout.

Exits 1 with a message on stderr when the file must be rejected (unsupported version, compact profile, syntax error).
Unknown-block warnings go to stderr."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _xlsx import decoded_json  # noqa: E402

import cellprose  # noqa: E402


def main(path):
    try:
        wb = cellprose.load(Path(path).read_text(encoding="utf-8"))
    except cellprose.ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for w in wb.warnings:
        print(f"warning: {w}", file=sys.stderr)
    sys.stdout.buffer.write((json.dumps(decoded_json(wb), ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
