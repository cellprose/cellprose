"""LangChain loader: Excel workbooks as Cellprose documents, and a splitter that keeps tables with their formulas.

    from langchain_cellprose import CellproseLoader
    docs = CellproseLoader("book.xlsx").load()                 # one Document for the workbook
    docs = CellproseLoader("book.xlsx", mode="sheet").load()   # one per sheet, for splitting and retrieval
    chunks = CellproseSplitter(chunk_size=4000).split_documents(docs)   # by region, formulas kept with their tables
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from ._structure import parse
from .splitter import CellproseSplitter

__all__ = ["CellproseLoader", "CellproseSplitter", "split_sheets"]


class CellproseLoader(BaseLoader):
    """Load a .xlsx/.xlsm (or an existing .sheet.md) as Cellprose text.

    mode: "workbook" gives one Document; "sheet" gives one per sheet (plus one for defined names, if any), each
    with the front matter so it reads alone. To split further without cutting a table from its formulas, pass the
    result to `CellproseSplitter`.

    Metadata: source, filename, format ("cellprose"), cellprose_version, profile ("full" or "compact"; a compact
    Document leaves rows out and cannot be turned back into a workbook), sheet_count, and in sheet mode sheet and
    sheet_index (0-based). Extra keyword arguments go to `cellprose.dumps` (sheets, cell_range,
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
        parsed = parse(text)
        meta: dict[str, Any] = {
            "source": str(self.file_path),
            "filename": self.file_path.name,
            "format": "cellprose",
            "cellprose_version": parsed.meta.get("cellprose") or parsed.meta.get("sheetmark") or "",
            "profile": parsed.meta.get("profile", "full"),
            "sheet_count": len(parsed.sheets),
        }
        if self.mode == "workbook":
            yield Document(page_content=text, metadata=meta)
            return
        index = {s.name: s.index for s in parsed.sheets}
        for sheet, part in split_sheets(text):
            yield Document(page_content=part, metadata={**meta, "sheet": sheet, "sheet_index": index[sheet]}
                           if sheet is not None else {**meta, "section": "names"})


def split_sheets(text: str) -> list[tuple[str | None, str]]:
    """Split Cellprose text into (sheet name, text) parts, one per `# Sheet:` section. Each part keeps the front
    matter so it reads on its own; the `# Names` section, when present, is the last part, with sheet name None."""
    lines = text.split("\n")
    start = 0
    if lines and lines[0] == "---" and "---" in lines[1:]:
        start = lines.index("---", 1) + 1
    head = "\n".join(lines[:start]).strip("\n")
    parts: list[tuple[str | None, list[str]]] = []
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
    if not parts:
        return [(None, text)]
    return [(n, (head + "\n\n" if head else "") + "\n".join(b).strip("\n") + "\n") for n, b in parts]
