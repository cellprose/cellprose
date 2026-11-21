"""MarkItDown plugin that turns Excel workbooks into Cellprose instead of plain Markdown tables.

MarkItDown's built-in converter keeps cached values only. Cellprose keeps the formulas (as fill ranges), cell
addresses, merged cells and every sheet, in text that is still valid Markdown.

    pip install markitdown-cellprose
    markitdown --use-plugins book.xlsx
    MarkItDown(enable_plugins=True).convert("book.xlsx").markdown
"""
from __future__ import annotations

import os
import tempfile
from typing import Any, BinaryIO

from markitdown import DocumentConverter, DocumentConverterResult, MarkItDown, StreamInfo

__plugin_interface_version__ = 1
__all__ = ["CellproseConverter", "register_converters"]

EXTENSIONS = (".xlsx", ".xlsm")
MIMETYPES = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel.sheet.macroenabled.12",
)
# Lower runs first. MarkItDown's built-in XlsxConverter sits at 0.0 (specific format) and the generic fallbacks at
# 10.0, so the plugin must go below 0.0 to win when markitdown[xlsx] is installed.
PRIORITY = -1.0


class CellproseConverter(DocumentConverter):
    """Convert .xlsx/.xlsm to Cellprose. Options pass through as `convert(..., cellprose_options={...})`."""

    def __init__(self, recalc: str = "never", legend: bool = True):
        self.recalc = recalc
        self.legend = legend

    def accepts(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> bool:
        ext = (stream_info.extension or "").lower()
        mime = (stream_info.mimetype or "").lower()
        return ext in EXTENSIONS or any(mime.startswith(m) for m in MIMETYPES)

    def convert(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> DocumentConverterResult:
        import cellprose

        opts = {"recalc": self.recalc, "legend": self.legend, **(kwargs.get("cellprose_options") or {})}
        ext = (stream_info.extension or ".xlsx").lower()
        ext = ext if ext in EXTENSIONS else ".xlsx"
        # Keep the original file name, because the text's `source:` line shows it.
        name = os.path.basename(stream_info.filename or stream_info.local_path or "") or "workbook" + ext
        if not name.lower().endswith(EXTENSIONS):
            name += ext
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, name)
            with open(path, "wb") as f:
                while chunk := file_stream.read(1 << 20):
                    f.write(chunk)
            text = cellprose.dumps(path, **opts)
        title = os.path.splitext(stream_info.filename)[0] if stream_info.filename else None
        return DocumentConverterResult(markdown=text, title=title)


def register_converters(markitdown: MarkItDown, **kwargs: Any) -> None:
    markitdown.register_converter(CellproseConverter(), priority=PRIORITY)
