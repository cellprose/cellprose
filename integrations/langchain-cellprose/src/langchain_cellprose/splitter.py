"""A Cellprose-aware splitter: cut by sheet or region, never between a table and its formulas."""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.documents import BaseDocumentTransformer, Document

from ._structure import (
    Block,
    Parsed,
    Region,
    SheetPart,
    line_box,
    names_in,
    overlaps,
    parse,
    row_number,
    target_box,
)

__all__ = ["CellproseSplitter"]

_DOC_KEYS = ("sheet", "sheet_index", "sheet_count")      # a Document made per sheet already knows these


@dataclass
class Chunk:
    text: str
    metadata: dict[str, Any]


class CellproseSplitter(BaseDocumentTransformer):
    """Split Cellprose text so each piece reads on its own.

    Every chunk starts with the front matter (and the row-number legend) and the `# Sheet:` heading, then holds
    whole regions: a region's table with its `formulas`, `formats` and `elided` blocks, plus the sheet-level lines
    (`merges`, `comments`, `arrays`, `validation`, loose `cells`) that fall inside it. Defined names that its
    formulas use, or that point into it, are added in a `# Names` section.

    by: "region" (default) makes one chunk per region; "sheet" makes one per sheet.
    chunk_size: optional limit in characters (or whatever `length_function` counts). A sheet that is over it falls
        back to regions; a region that is still over it is cut into bands of rows. A band keeps the region's first
        row, a `…` marker row and an `elided` block, so the file says which rows it leaves out, and it gets
        `profile: compact` in its front matter. Formulas are never cut: a fill range that touches the band is
        copied whole, so its anchor cell stays with it. With no chunk_size a region is never cut.
    include_names: carry relevant defined names into each chunk (default True). The full `# Names` section is
        also returned as its own chunk, as the loader does.

    Chunk metadata: sheet, sheet_index, sheet_count, region (e.g. "A1:F9"), region_index, chunk_kind ("sheet",
    "region", "loose" for cells outside any region, or "names") and, for bands, part and parts.
    """

    def __init__(self, by: Literal["region", "sheet"] = "region", chunk_size: int | None = None,
                 length_function: Callable[[str], int] = len, include_names: bool = True):
        if by not in ("region", "sheet"):
            raise ValueError("by must be 'region' or 'sheet'")
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.by, self.chunk_size, self.length, self.include_names = by, chunk_size, length_function, include_names

    # ---------------------------------------------------------------- public
    def split_text(self, text: str) -> list[str]:
        return [c.text for c in self.split_chunks(text)]

    def split_chunks(self, text: str) -> list[Chunk]:
        p = parse(text)
        if not p.sheets and p.names is None:
            return [Chunk(text, {"chunk_kind": "sheet"})]
        out: list[Chunk] = []
        for sheet in p.sheets:
            out.extend(self._sheet_chunks(p, sheet))
        if p.names is not None:
            out.append(Chunk(self._assemble(p, ["# Names", p.names.text()], None, None, []),
                             {"chunk_kind": "names", "section": "names"}))
        return out

    def split_documents(self, documents: Sequence[Document]) -> list[Document]:
        out = []
        for doc in documents:
            for chunk in self.split_chunks(doc.page_content):
                meta = {**doc.metadata, **chunk.metadata}
                meta.update({k: doc.metadata[k] for k in _DOC_KEYS if k in doc.metadata})
                out.append(Document(page_content=chunk.text, metadata=meta))
        return out

    def transform_documents(self, documents: Sequence[Document], **kwargs: Any) -> Sequence[Document]:
        return self.split_documents(documents)

    # --------------------------------------------------------------- sheets
    def _sheet_chunks(self, p: Parsed, sheet: SheetPart) -> list[Chunk]:
        base = {"sheet": sheet.name, "sheet_index": sheet.index, "sheet_count": len(p.sheets)}
        head = [sheet.heading] + ([sheet.meta.text()] if sheet.meta else [])
        blocks = [b for r in sheet.regions for b in r.blocks] + sheet.tail
        whole = self._assemble(p, head + [t for r in sheet.regions for t in (r.heading, "\n".join(r.table))]
                               + [b.text() for b in blocks], sheet, None, blocks)
        if not sheet.regions or (self.by == "sheet" and (self.chunk_size is None
                                                         or self.length(whole) <= self.chunk_size)):
            return [Chunk(whole, {**base, "chunk_kind": "sheet"})]
        chunks: list[Chunk] = []
        for n, region in enumerate(sheet.regions):
            inside = [Block(b.kind, ls) for b in sheet.tail
                      if (ls := [ln for ln in b.lines if (x := line_box(ln)) is not None and overlaps(x, region.box)])]
            meta = {**base, "chunk_kind": "region", "region": region.heading[3:].strip(), "region_index": n}
            chunks.extend(self._region_chunks(p, sheet, head, region, region.blocks + inside, meta))
        loose = [Block(b.kind, ls) for b in sheet.tail
                 if (ls := [ln for ln in b.lines if not any(
                     (x := line_box(ln)) is not None and overlaps(x, r.box) for r in sheet.regions)])]
        if loose:
            text = self._assemble(p, head + [b.text() for b in loose], sheet, None, loose)
            chunks.append(Chunk(text, {**base, "chunk_kind": "loose"}))
        return chunks

    # -------------------------------------------------------------- regions
    def _region_chunks(self, p: Parsed, sheet: SheetPart, head: list[str], region: Region, blocks: list[Block],
                       meta: dict[str, Any]) -> list[Chunk]:
        def build(table: list[str], blks: list[Block], compact: bool = False) -> str:
            return self._assemble(p, head + [region.heading, "\n".join(table)] + [b.text() for b in blks],
                                  sheet, region, blks, compact)

        full = build(region.table, blocks)
        rows = region.table[2:]
        if self.chunk_size is None or self.length(full) <= self.chunk_size or len(rows) < 3:
            return [Chunk(full, meta)]
        header, first, rest = region.table[:2], rows[0], rows[1:]
        room = self.chunk_size - self.length(build(header + [first], []))
        bands: list[list[str]] = [[]]
        used = 0
        for row in rest:
            if bands[-1] and used + self.length(row) + 1 > room:
                bands.append([])
                used = 0
            bands[-1].append(row)
            used += self.length(row) + 1
        chunks = []
        for k, band in enumerate(bands):
            nums = [n for n in map(row_number, [first] + band) if n is not None]
            gap = row_number(first) is not None and row_number(band[0]) not in (None, row_number(first) + 1)
            table = header + [first] + (["|".join(["…"] * len(header[0].split("|")))] if gap else []) + band
            kept = [Block(b.kind, ls) for b in blocks if b.kind != "elided"
                    and (ls := [ln for ln in b.lines if self._touches(ln, nums)])]
            missing = _missing(region.box[0], region.box[2], set(nums))
            if missing:
                kept.insert(0, Block("elided", missing))      # the writer puts it straight after the table
            chunks.append(Chunk(build(table, kept, True), {**meta, "part": k, "parts": len(bands)}))
        return chunks

    @staticmethod
    def _touches(line: str, rows: list[int]) -> bool:
        b = line_box(line)
        return b is None or any(b[0] <= r <= b[2] for r in rows)

    # ------------------------------------------------------------- assembly
    def _assemble(self, p: Parsed, body: list[str], sheet: SheetPart | None, region: Region | None,
                  blocks: list[Block], compact: bool = False) -> str:
        front = list(p.front)
        if compact and p.meta.get("profile") != "compact" and front:
            at = next((i for i, ln in enumerate(front) if ln.startswith(("cellprose:", "sheetmark:"))), 0) + 1
            front.insert(at, "profile: compact")
        pre = ["\n".join(front)] if front else []
        if p.legend and any(ln.startswith(("#|", "|#|")) for part in body for ln in part.split("\n")):
            pre.append(p.legend)
        if sheet is not None and self.include_names and p.names is not None:
            body = body + self._relevant_names(p, sheet, region, blocks)
        return "\n\n".join(pre + body).strip("\n") + "\n"

    def _relevant_names(self, p: Parsed, sheet: SheetPart, region: Region | None, blocks: list[Block]) -> list[str]:
        """Names a chunk's formulas use, or that point into it, as a `# Names` section."""
        used = "\n".join(ln for b in blocks if b.kind in ("formulas", "cells", "arrays", "validation")
                         for ln in b.lines)
        lines = []
        for line, scope, name, target in names_in(p.names):
            if scope is not None and scope != sheet.name:
                continue
            box = target_box(target)
            here = box is not None and box[0] == sheet.name and (region is None or overlaps(box[1], region.box))
            if here or re.search(rf"(?<![\w.]){re.escape(name)}(?![\w(])", used, re.IGNORECASE):
                lines.append(line)
        return ["# Names\n\n" + Block("names", lines).text()] if lines else []


def _missing(r1: int, r2: int, shown: set[int]) -> list[str]:
    """`elided` lines for the rows of r1..r2 that are not in `shown`."""
    out, start = [], None
    for r in range(r1, r2 + 2):
        gone = r <= r2 and r not in shown
        if gone and start is None:
            start = r
        elif not gone and start is not None:
            n = r - start
            out.append(f"rows: {start}-{r - 1}  # {n} rows not shown" if n > 1 else f"rows: {start}  # 1 row not shown")
            start = None
    return out
