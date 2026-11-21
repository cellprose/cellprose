"""`cellprose stats`: size of a workbook as Cellprose vs CSV and Markdown, in characters and tokens.

Tokens are counted offline with tiktoken's o200k_base (an OpenAI tokenizer). Anthropic's tokenizer is not
public, so Claude's real counts differ; treat the percentages as a guide, not a billing figure.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
from pathlib import Path

from . import dumps
from .writer import load_pair

TOKENIZER = "o200k_base"


def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else "%.10g" % v
    if isinstance(v, dt.datetime):
        return v.date().isoformat() if v.time() == dt.time(0) else v.isoformat(timespec="seconds")
    if isinstance(v, dt.date):
        return v.isoformat()
    return str(v)


def _grids(path: Path):
    """(sheet title, rows of display values) for each sheet, trailing empty rows dropped."""
    _, vwb = load_pair(path)
    for ws in vwb.worksheets:
        rows = [[_cell(ws.cell(row=r, column=c).value) for c in range(1, ws.max_column + 1)]
                for r in range(1, ws.max_row + 1)]
        while rows and not any(rows[-1]):
            rows.pop()
        yield ws.title, rows


def to_csv(path: Path) -> str:
    parts = []
    for title, rows in _grids(path):
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerows(rows)
        parts.append(f"## {title}\n{buf.getvalue()}")
    return "\n".join(parts)


def to_markdown(path: Path) -> str:
    parts = []
    for title, rows in _grids(path):
        if not rows:
            parts.append(f"## {title}\n")
            continue
        esc = [[c.replace("|", "\\|").replace("\n", "<br>") for c in r] for r in rows]
        lines = ["| " + " | ".join(esc[0]) + " |", "|" + "---|" * len(esc[0])]
        lines += ["| " + " | ".join(r) + " |" for r in esc[1:]]
        parts.append(f"## {title}\n" + "\n".join(lines))
    return "\n\n".join(parts)


def counter():
    """Return a text -> token count function, or raise RuntimeError if tiktoken is unavailable."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding(TOKENIZER)
    except Exception as e:  # missing package, or vocabulary not cached and no network
        raise RuntimeError(
            f"token counting needs tiktoken and its {TOKENIZER} vocabulary ({e}); "
            "install with `pip install tiktoken` or pass --no-tokens") from e
    return lambda text: len(enc.encode(text, disallowed_special=()))


def compute(path: str | Path, tokens: bool = True) -> dict:
    """Sizes of each format. Returns {"tokenizer": ..., "formats": {name: {"chars": n, "tokens": n|None}}}."""
    path = Path(path)
    texts = {"cellprose": dumps(path), "csv": to_csv(path), "markdown": to_markdown(path)}
    count = counter() if tokens else None
    return {
        "tokenizer": TOKENIZER if tokens else None,
        "formats": {k: {"chars": len(t), "tokens": count(t) if count else None} for k, t in texts.items()},
    }


def _pct(new: int, base: int) -> str:
    return "n/a" if not base else f"{(new - base) / base * 100:+.1f}%"


def render(name: str, result: dict) -> str:
    f = result["formats"]
    tok = result["tokenizer"] is not None
    head = ["format", "chars", "vs cellprose"] + (["tokens", "vs cellprose"] if tok else [])
    lines = [f"{name}", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    sm = f["cellprose"]
    for k in ("cellprose", "csv", "markdown"):
        row = [k, str(f[k]["chars"]), "-" if k == "cellprose" else _pct(f[k]["chars"], sm["chars"])]
        if tok:
            row += [str(f[k]["tokens"]), "-" if k == "cellprose" else _pct(f[k]["tokens"], sm["tokens"])]
        lines.append("| " + " | ".join(row) + " |")
    if tok:
        lines.append(f"tokenizer: {result['tokenizer']} (OpenAI, counted offline); Anthropic's counts differ. "
                     "CSV and Markdown are naive values-only baselines: no formulas or formats.")
    return "\n".join(lines)
