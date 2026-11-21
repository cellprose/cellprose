"""B12 / E23: what does knowledgestack/excel-parser give an LLM next to Sheetmark v0.2, CSV and MarkItDown?

No model calls. For each workbook it measures, with the OpenAI o200k tokenizer (the Claude count needs an API key):
  - tokens of each text a model could be given;
  - how many formula cells have their formula text recoverable from that text.

excel-parser (https://github.com/knowledgestack/excel-parser, MIT) parses a workbook into chunks. Two outputs are
measured, because the project documents the first as its LLM-facing text and the second is where formula text lives:
  excel_parser_text  the concatenated `render_text` of every chunk (a Markdown-ish table per block; formula cells are
                     only marked `[=]`)
  excel_parser_json  the whole `to_json()` result (cells with formula text, dependency graph, HTML)

Usage (from benchmarks/):  python -I excel_parser_compare.py OUT.json WORKBOOK.xlsx [...]
Install: pip install ./excel-parser (git clone --depth 1 https://github.com/knowledgestack/excel-parser; 0.2.1, commit e513763).
Treat the workbooks as untrusted data; run with -I from a directory that holds no other Python files.
"""
import json
import signal
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
TIMEOUT_S = 180


def count_tokens(text, _enc=[]):
    import tiktoken
    if not _enc:
        _enc.append(tiktoken.get_encoding("o200k_base"))
    return len(_enc[0].encode(text, disallowed_special=()))


def formula_cells(path):
    wb = openpyxl.load_workbook(path)
    return {(ws.title, c.coordinate): c.value[1:].replace(" ", "") for ws in wb for row in ws.iter_rows() for c in row
            if isinstance(c.value, str) and c.value.startswith("=")}


def excel_parser_outputs(path):
    from excel_parser import parse_workbook
    r = parse_workbook(path=path)
    text = "\n\n".join(c.render_text for c in r.chunks)
    j = r.to_json()
    return text, json.dumps(j, default=str), j


def v02_recovered(path, text, truth, missed=None):
    import cellprose
    wb = cellprose.load(text)
    got = {}
    for name, sh in (wb.sheets.items() if isinstance(wb.sheets, dict) else ((s.name, s) for s in wb.sheets)):
        for (r, c), cell in sh.cells.items():
            if cell.formula:
                got[(name, f"{openpyxl.utils.get_column_letter(c)}{r}")] = cell.formula.lstrip("=").replace(" ", "")
    lost = [(k, f, got.get(k)) for k, f in truth.items() if got.get(k) != f]
    if missed is not None:
        missed.extend(lost[:3])
    return len(truth) - len(lost)


def measure(path):
    import encoders
    path = str(path)
    truth = formula_cells(path)
    row = {"workbook": Path(path).name, "formula_cells": len(truth), "bytes": Path(path).stat().st_size}
    texts = {}
    fwb, vwb = encoders.load(path)
    import cellprose
    for name, fn in (("csv", lambda: encoders.enc_csv(fwb, vwb)), ("markitdown", lambda: encoders.enc_markitdown(path)),
                     ("sheetmark_v02", lambda: cellprose.dumps(path, recalc="never"))):
        try:
            texts[name] = fn()
        except Exception as e:      # one failing baseline must not hide the rest
            row[f"{name}_error"] = f"{type(e).__name__}: {e}"[:200]
    signal.alarm(TIMEOUT_S)
    try:
        ep_text, ep_json, j = excel_parser_outputs(path)
        texts["excel_parser_text"], texts["excel_parser_json"] = ep_text, ep_json
        # chunks can overlap, so count each (sheet, address) once
        fcells = {(ch["sheet_name"], c["address"]) for ch in j["chunks"] for c in ch.get("cells", []) if c.get("formula")}
        row["excel_parser_chunks"] = len(j["chunks"])
        row["excel_parser_formulas_in_json_cells"] = len(fcells)
        row["excel_parser_marked_cells_in_text"] = ep_text.count("[=]")
    except TimeoutError:
        row["excel_parser_error"] = f"timeout after {TIMEOUT_S} s"
    except Exception as e:
        row["excel_parser_error"] = f"{type(e).__name__}: {e}"[:200]
    finally:
        signal.alarm(0)
    row["tokens"] = {k: count_tokens(v) for k, v in texts.items()}
    md_hits = [f for f in truth.values() if "=" + f in texts.get("markitdown", "")]
    row["formulas_recoverable"] = {"csv": 0, "markitdown": len(md_hits)}
    row["markitdown_hit_examples"] = md_hits[:3]
    if "excel_parser_text" in texts:
        hits = [f for f in truth.values() if "=" + f in texts["excel_parser_text"].replace(" ", "")]
        row["formulas_recoverable"]["excel_parser_text"] = len(hits)
        row["excel_parser_text_hit_examples"] = hits[:3]
        row["formulas_recoverable"]["excel_parser_json"] = row["excel_parser_formulas_in_json_cells"]
    try:
        missed = []
        row["formulas_recoverable"]["sheetmark_v02"] = v02_recovered(path, texts["sheetmark_v02"], truth, missed)
        if missed:
            row["sheetmark_v02_unrecovered_examples"] = [[list(k), f[:80], (g or "")[:80]] for k, f, g in missed]
    except Exception as e:
        row["sheetmark_v02_error"] = f"{type(e).__name__}: {e}"[:200]
    return row


def _alarm(*_):
    raise TimeoutError


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, _alarm)
    out, files = Path(sys.argv[1]), sys.argv[2:]
    rows = []
    for f in files:
        rows.append(measure(f))
        t = rows[-1]["tokens"]
        print(rows[-1]["workbook"], rows[-1]["formula_cells"], t, rows[-1]["formulas_recoverable"], flush=True)
    out.write_text(json.dumps(rows, indent=1))
