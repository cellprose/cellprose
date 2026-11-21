"""Prompt construction, moved verbatim from run.py so every runner sends identical text."""
import json
import os
from pathlib import Path

from .ids import canon

ROOT = Path(__file__).resolve().parent.parent
# A corpus is a directory with questions/ and encoded/; CELLPROSE_CORPUS points at an external one (e.g. SpreadsheetBench).
CORPUS = Path(os.environ.get("CELLPROSE_CORPUS") or ROOT)
LABEL = {"csv": "CSV", "markdown": "Markdown tables", "markitdown": "Markdown tables (MarkItDown)", "markdown_kv": "Markdown key-value records",
         "toon": "TOON", "grid_values": "Sheetmark", "sheetmark": "Sheetmark",
         "sheetmark_inline": "Sheetmark", "sheetmark_labels": "Sheetmark",
         "sheetmark_lean": "Sheetmark", "sheetmark_lean_gfm": "Sheetmark",
         "sheetmark_lean_gfm_nopipe": "Sheetmark", "cellprose_v03": "Sheetmark", "cellprose_v03_nolegend": "Sheetmark"}   # label kept as in E30/E32
SYSTEM = ("You answer questions about a spreadsheet workbook provided as text. Use only the workbook. "
          "Reply with a single JSON object and nothing else.")
KIND = {"lookup": "value", "address": "address", "trace": "list", "impact": "list", "hardcode": "list"}


def prompt(wb, enc):
    qs = json.loads((CORPUS / "questions" / f"{wb}.json").read_text())
    parts = []
    if enc != "none":
        text = (CORPUS / "encoded" / f"{wb}.{canon(enc)}.txt").read_text()
        parts.append(f'<workbook format="{LABEL[canon(enc)]}">\n{text}\n</workbook>\n')
    else:
        parts.append("No workbook is provided this time. Answer with your best guess.\n")
    parts.append(
        "Answer each question. Rules:\n"
        "- Cell addresses use A1 notation qualified with the sheet name, e.g. Sheet1!B5.\n"
        "- For list questions, return a JSON array of cell addresses; ranges like Sheet1!B2:B9 are allowed. "
        "Return [] if there are none.\n"
        "- For value questions, return a number without units or thousands separators, or a short string.\n"
        "- If the workbook does not give enough information, give your best guess.\n\nQuestions:")
    for q in qs:
        parts.append(f"{q['id']} ({KIND[q['type']]}): {q['q']}")
    parts.append('\nReturn JSON like {"q1": ..., "q2": ...} with every question id.')
    return "\n".join(parts)


# ---- agent mode: the workbook is a file on disk and the model has tools
AGENT_SYSTEM = ("You answer questions about a spreadsheet workbook stored as a file in the current folder. "
                "Use the tools to inspect it (python3 with openpyxl is installed). "
                "When done, reply with a single JSON object and nothing else.")
AGENT_FILES = {"agent_xlsx": ("book.xlsx", "workbooks", "{wb}.xlsx"),
               "agent_xlsx_viewer": ("book.xlsx", "workbooks", "{wb}.xlsx"),     # same file, plus the view_xlsx tool
               "agent_xlsx_cellprose": ("book.xlsx", "workbooks", "{wb}.xlsx"),  # same file, plus the Cellprose tools (E33)
               "agent_xlsx_cellprose_idx": ("book.xlsx", "workbooks", "{wb}.xlsx"),  # as above, outline = index only
               "agent_cellprose_lean": ("book.xlsx", "workbooks", "{wb}.xlsx"),  # E34: index in the prompt, tools only
               "agent_cellprose_v03": ("book.sheet.md", "encoded", "{wb}.cellprose_v03.txt"),    # the default: v0.3 with the legend
               "agent_cellprose_v03_nolegend": ("book.sheet.md", "encoded", "{wb}.cellprose_v03_nolegend.txt"),   # as E28-E30 ran it
               "agent_sheetmark": ("book.sheet.md", "encoded", "{wb}.sheetmark_lean_gfm.txt"),   # legacy: v0.2 text
               # B20: v0.2 with the last cell of each fill range written out; experimental, never in a default run
               "agent_sheetmark_hint": ("book.sheet.md", "encoded", "{wb}.sheetmark_lean_gfm_hint.txt")}


# E34: the lean arm has no shell, so its system prompt does not offer python; its user prompt carries the index.
LEAN_SYSTEM = ("You answer questions about a spreadsheet workbook. Its index is in the message; read cells with the tools. "
               "When done, reply with a single JSON object and nothing else.")


def lean_prompt(wb: str) -> str:
    import sys
    sys.path.insert(0, str(ROOT.parent / "src"))
    from cellprose import tools
    idx = tools.index(CORPUS / "workbooks" / f"{wb}.xlsx")
    return agent_prompt(wb, "agent_cellprose_lean").replace("The workbook is ./book.xlsx.\n",
                                                            f"The workbook's index:\n{idx}\n", 1)


def agent_source(wb: str, variant: str) -> tuple[str, Path]:
    """(file name the model sees, path of the file to copy into its folder)."""
    name, folder, pattern = AGENT_FILES[canon(variant)]
    return name, CORPUS / folder / pattern.format(wb=wb)


def agent_prompt(wb: str, variant: str) -> str:
    """Same questions and answer rules as `prompt`, but the workbook is a file the model must open."""
    fname = AGENT_FILES[canon(variant)][0]
    qs = json.loads((CORPUS / "questions" / f"{wb}.json").read_text())
    parts = [f"The workbook is ./{fname}.\n",
             "Answer each question. Rules:\n"
             "- Cell addresses use A1 notation qualified with the sheet name, e.g. Sheet1!B5.\n"
             "- For list questions, return a JSON array of cell addresses; ranges like Sheet1!B2:B9 are allowed. "
             "Return [] if there are none.\n"
             "- For value questions, return a number without units or thousands separators, or a short string.\n"
             "- If the workbook does not give enough information, give your best guess.\n\nQuestions:"]
    for q in qs:
        parts.append(f"{q['id']} ({KIND[q['type']]}): {q['q']}")
    parts.append('\nReturn JSON like {"q1": ..., "q2": ...} with every question id.')
    return "\n".join(parts)
