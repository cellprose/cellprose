"""Build a question corpus from SpreadsheetBench (verified 400) for the one-shot runner.

  python3 external/spreadsheetbench.py          # download the pinned revision, select, encode
  CELLPROSE_CORPUS=external/spreadsheetbench python3 api_run.py --models haiku55 --encs csv,markitdown,cellprose_v03 ...

SpreadsheetBench tasks ask for a change to a workbook ("fill these cells"), scored against a golden workbook.
Here each selected task becomes value questions: the task's instruction, then "what value ends up in cell X",
with the golden workbook's value as ground truth. See external/README.md for why the tasks are restated.

Selection rule (fixed before any model run; never tuned on results):
  - instruction type "Cell-Level Manipulation", init and golden files present, one answer range on an existing sheet
  - every formula in the init workbook has a cached value (encodings need values)
  - the init workbook has MIN_CELLS..MAX_CELLS non-empty cells (MAX keeps every prompt inside every model's context)
  - up to QUESTIONS_PER_TASK answer cells, evenly spaced over the range's non-empty golden cells whose value is a
    number or a string (dates and booleans are skipped: the scorer compares them as text)

The data is CC BY-SA 4.0, so the downloaded files and the generated corpus stay out of git (see .gitignore).
"""
import json
import shutil
import sys
import tarfile
import urllib.request
import warnings
from datetime import date, datetime, time
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter, range_boundaries

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from encoders import ENCODINGS, encode  # noqa: E402

REVISION = "ab0b742b0fc95b946f212d80ac7771b5531272e4"      # Hugging Face dataset commit, KAKA22/SpreadsheetBench
URL = f"https://huggingface.co/datasets/KAKA22/SpreadsheetBench/resolve/{REVISION}/spreadsheetbench_verified_400.tar.gz"
CACHE = HERE / ".cache"
OUT = HERE / "spreadsheetbench"
MIN_CELLS, MAX_CELLS, QUESTIONS_PER_TASK = 300, 20000, 5
EXCLUDE = {   # generated questions that are not part of the set, with the reason; by their id as generated
    "sb_56786": dict.fromkeys(["q1", "q2", "q3", "q4", "q5"],
                              "the solution file contradicts the asker's own worked examples in the workbook"),
    "sb_45738": dict.fromkeys(["q1", "q3", "q4", "q5"],
                              "the request asks for '-' on these dates; the solution holds 0 formatted as '-'"),
    "sb_42216": {"q2": "the answer depends on whether the solution's inserted April row is counted"},
    "sb_52964": {"q1": "the request says U minus Y (-17); the answer is Y minus U (17)"},
}

warnings.filterwarnings("ignore", module="openpyxl")


def fetch() -> Path:
    root = CACHE / "spreadsheetbench_verified_400"
    if not root.exists():
        CACHE.mkdir(exist_ok=True)
        tgz = CACHE / f"verified_400.{REVISION[:8]}.tar.gz"
        if not tgz.exists():
            urllib.request.urlretrieve(URL, tgz)
        with tarfile.open(tgz) as t:
            t.extractall(CACHE, filter="data")
    return root


def nonempty(wb) -> int:
    return sum(1 for ws in wb for row in ws.iter_rows() for c in row if c.value is not None)


def uncached_formulas(fwb, vwb) -> bool:
    return any(isinstance(c.value, str) and c.value.startswith("=") and vwb[ws.title][c.coordinate].value is None
               for ws in fwb for row in ws.iter_rows() for c in row)


def answer_cells(task, golden):
    """[(sheet, coordinate, value)] for the answer range, or None when the task is unusable."""
    pos = task["answer_position"]
    if "," in pos:
        return None
    sheet = golden.sheetnames[0]
    if "!" in pos:
        sheet, pos = pos.rsplit("!", 1)
        sheet = sheet.strip("'")
    if sheet not in golden.sheetnames:
        return None
    c1, r1, c2, r2 = range_boundaries(pos.replace("$", ""))
    ws = golden[sheet]
    out = []
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            v = ws.cell(r, c).value
            if v is None or isinstance(v, (bool, datetime, date, time)):
                continue
            out.append((sheet, f"{get_column_letter(c)}{r}", v))
    return out


def pick(cells, k):
    if len(cells) <= k:
        return cells
    return [cells[round(i * (len(cells) - 1) / (k - 1))] for i in range(k)]


def main():
    root = fetch()
    tasks = json.loads((root / "dataset.json").read_text())
    if OUT.exists():
        shutil.rmtree(OUT)
    for d in ("workbooks", "questions", "encoded"):
        (OUT / d).mkdir(parents=True)
    kept, skipped = [], {}

    def skip(reason):
        skipped[reason] = skipped.get(reason, 0) + 1

    for t in tasks:
        if t["instruction_type"] != "Cell-Level Manipulation":
            skip("sheet-level task"); continue
        files = sorted((root / t["spreadsheet_path"]).glob("*.xlsx"))
        init = [f for f in files if f.name.endswith("_init.xlsx")]
        gold = [f for f in files if f.name.endswith("_golden.xlsx")]
        if not init or not gold:
            skip("missing files"); continue
        fwb, vwb = openpyxl.load_workbook(init[0]), openpyxl.load_workbook(init[0], data_only=True)
        n = nonempty(fwb)
        if not MIN_CELLS <= n <= MAX_CELLS:
            skip("outside size range"); continue
        if uncached_formulas(fwb, vwb):
            skip("init formulas without cached values"); continue
        cells = answer_cells(t, openpyxl.load_workbook(gold[0], data_only=True))
        if not cells:
            skip("no usable answer cells"); continue
        key = f"sb_{t['id']}"
        try:     # encoders.py is left unchanged; a workbook it cannot encode (e.g. an empty sheet) is skipped
            texts = {e: encode(init[0], e) for e in ENCODINGS if e != "markitdown"}
        except Exception:
            skip("encoder error"); continue
        try:     # the MarkItDown baseline is encoded after the selection above so it cannot change which tasks are kept
            texts["markitdown"] = encode(init[0], "markitdown")
        except Exception:
            skip("markitdown error"); continue
        picked = [c for i, c in enumerate(pick(cells, QUESTIONS_PER_TASK), 1) if f"q{i}" not in EXCLUDE.get(key, ())]
        if not picked:
            skip("every question on the exclusion list"); continue
        qs = []
        for i, (sheet, coord, v) in enumerate(picked, 1):
            ask = f"what value ends up in {sheet}!{coord}?"
            text = (f"A user asked: \"{t['instruction'].strip()}\" Suppose that request is carried out correctly; {ask}"
                    if i == 1 else f"Same request as q1: {ask}")
            qs.append({"type": "lookup", "q": text, "cell": f"{sheet}!{coord}", "id": f"q{i}",
                       "truth": v if isinstance(v, (int, float)) else str(v)})
        shutil.copy(init[0], OUT / "workbooks" / f"{key}.xlsx")
        (OUT / "questions" / f"{key}.json").write_text(json.dumps(qs, indent=1, default=str))
        for e, text in texts.items():
            (OUT / "encoded" / f"{key}.{e}.txt").write_text(text)
        kept.append({"id": t["id"], "cells": n, "questions": len(qs)})
    (OUT / "selection.json").write_text(json.dumps({"revision": REVISION, "min_cells": MIN_CELLS,
                                                     "max_cells": MAX_CELLS, "questions_per_task": QUESTIONS_PER_TASK,
                                                     "kept": kept, "skipped": skipped}, indent=1))
    print(f"kept {len(kept)} tasks, {sum(k['questions'] for k in kept)} questions; skipped {skipped}")


if __name__ == "__main__":
    main()
