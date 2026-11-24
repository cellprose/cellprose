"""LangChain loader: Excel workbooks as Cellprose documents.

    from langchain_cellprose import CellproseLoader
    docs = CellproseLoader("book.xlsx").load()                 # one Document for the workbook
    docs = CellproseLoader("book.xlsx", mode="sheet").load()   # one per sheet, for splitting and retrieval
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, Literal

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

__all__ = ["CellproseLoader", "split_sheets"]


class CellproseLoader(BaseLoader):
    """Load a .xlsx/.xlsm (or an existing .sheet.md) as Cellprose text.

    mode: "workbook" gives one Document; "sheet" gives one per sheet (plus one for defined names, if any), each
    with the front matter so it reads alone. Extra keyword arguments go to `cellprose.dumps` (sheets, cell_range,
    max_rows, recalc, legend). recalc defaults to "never": formulas without cached values print as `?`.
    """

    def __init__(self, file_path: str | Path, mode: Literal["workbook", "sheet"] = "workbook", **options: Any):
        if mode not in ("workbook", "sheet"):
            raise ValueError("mode must be 'workbook' or 'sheet'")
        self.file_path = Path(file_path)
        self.mode = mode
        self.options = {"recalc": "never", **options}

    def _text(self) -> str:
        if self.file_path.name.endswith((".sheet.md", ".cellprose.md")):
            return self.file_path.read_text(encoding="utf-8")
        import cellprose
        return cellprose.dumps(self.file_path, **self.options)

    def lazy_load(self) -> Iterator[Document]:
        text = self._text()
        meta = {"source": str(self.file_path), "format": "cellprose"}
        if self.mode == "workbook":
            yield Document(page_content=text, metadata=meta)
            return
        for sheet, part in split_sheets(text):
            yield Document(page_content=part, metadata={**meta, "sheet": sheet} if sheet is not None
                           else {**meta, "section": "names"})


def split_sheets(text: str) -> list[tuple[str | None, str]]:
    """Split Cellprose text into (sheet name, text) parts, one per `# Sheet:` section. Each part keeps the front
    matter so it reads on its own; the `# Names` section, when present, is the last part, with sheet name None."""
    lines = text.split("\n")
    start = 0
    if lines and lines[0] == "---" and "---" in lines[1:]:
        start = lines.index("---", 1) + 1
    head = "\n".join(lines[:start]).strip("\n")
    parts: list[tuple[str | None, list[str]]] = []
    pre: list[str] = []         # text between the front matter and the first heading: the row-number legend (SPEC §3.1)
    fenced = False
    for line in lines[start:]:
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("# Sheet: "):
            name = line[len("# Sheet: "):].strip()
            if len(name) >= 2 and name[0] == name[-1] == '"':
                name = name[1:-1]
            parts.append((name, [line]))
        elif not fenced and line == "# Names":
            parts.append((None, [line]))
        elif parts:
            parts[-1][1].append(line)
        else:
            pre.append(line)
    if not parts:
        return [(None, text)]
    head = "\n".join([head, *pre]).strip("\n") if any(x.strip() for x in pre) else head
    return [(n, (head + "\n\n" if head else "") + "\n".join(b).strip("\n") + "\n") for n, b in parts]
