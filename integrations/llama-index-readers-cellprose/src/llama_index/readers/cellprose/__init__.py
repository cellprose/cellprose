"""LlamaIndex reader: Excel workbooks as Cellprose documents.

    from llama_index.readers.cellprose import CellproseReader
    docs = CellproseReader().load_data("book.xlsx")
    SimpleDirectoryReader("data", file_extractor={".xlsx": CellproseReader()}).load_data()
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

__all__ = ["CellproseReader", "split_sheets"]


class CellproseReader(BaseReader):
    """Read a .xlsx/.xlsm (or an existing .sheet.md) as Cellprose text.

    mode: "workbook" gives one Document; "sheet" gives one per sheet (plus one for defined names, if any), each
    with the front matter so it reads alone. Extra keyword arguments go to `cellprose.dumps` (sheets, cell_range,
    max_rows, recalc, legend). recalc defaults to "never": formulas without cached values print as `?`.
    """

    def __init__(self, mode: Literal["workbook", "sheet"] = "workbook", **options: Any):
        if mode not in ("workbook", "sheet"):
            raise ValueError("mode must be 'workbook' or 'sheet'")
        super().__init__()
        self.mode = mode
        self.options = {"recalc": "never", **options}

    def load_data(self, file: str | Path, extra_info: dict | None = None, fs: Any = None) -> list[Document]:
        path = Path(file)
        if fs is not None:
            import tempfile
            with fs.open(str(path), "rb") as f, tempfile.NamedTemporaryFile(suffix=path.suffix, delete=False) as t:
                t.write(f.read())
            local = Path(t.name)
        else:
            local = path
        try:
            if path.name.endswith((".sheet.md", ".cellprose.md")):
                text = local.read_text(encoding="utf-8")
            else:
                import cellprose
                text = cellprose.dumps(local, **self.options)
        finally:
            if local is not path:
                local.unlink(missing_ok=True)
        meta = {"file_name": path.name, "file_path": str(path), "format": "cellprose", **(extra_info or {})}
        if self.mode == "workbook":
            return [Document(text=text, metadata=meta)]
        return [Document(text=part, metadata={**meta, "sheet": sheet} if sheet is not None
                         else {**meta, "section": "names"}) for sheet, part in split_sheets(text)]


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
