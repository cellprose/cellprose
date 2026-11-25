# langchain-cellprose

A LangChain document loader that reads `.xlsx` and `.xlsm` workbooks as [Cellprose](https://cellprose.com) text,
keeping formulas, cell addresses and every sheet in valid Markdown.

```bash
pip install langchain-cellprose
```

```python
from langchain_cellprose import CellproseLoader

docs = CellproseLoader("book.xlsx").load()                 # one Document for the whole workbook
docs = CellproseLoader("book.xlsx", mode="sheet").load()   # one per sheet, metadata["sheet"] set
docs = CellproseLoader("book.xlsx", max_rows=200).load()   # options pass to cellprose.dumps
```

Each Document's metadata says where it came from: `source`, `filename`, `format`, `cellprose_version`, `profile`
(`full`, or `compact` when rows were left out and the text cannot be turned back into a workbook), `sheet_count`,
and in sheet mode `sheet` and `sheet_index` (0-based).

## Splitting without cutting a table from its formulas

A general text splitter can put a table in one chunk and its `formulas` block in another. `CellproseSplitter` cuts
only at region and sheet boundaries. Each chunk starts with the front matter and row-number legend, then holds
whole regions: the table, its `formulas`, `formats` and `elided` blocks, the sheet-level lines (merges, comments,
arrays, validation) that fall inside it, and the defined names its formulas use or that point into it.

```python
from langchain_cellprose import CellproseLoader, CellproseSplitter

docs = CellproseLoader("book.xlsx").load()
chunks = CellproseSplitter().split_documents(docs)                 # one chunk per region
chunks = CellproseSplitter(by="sheet").split_documents(docs)       # one chunk per sheet
chunks = CellproseSplitter(chunk_size=4000).split_documents(docs)  # fall back to regions, then bands of rows
```

Chunk metadata adds `region` (e.g. `A1:F9`), `region_index` and `chunk_kind` (`region`, `sheet`, `loose` for cells
outside any region, or `names`). With `chunk_size`, a region that is still too big is cut into bands of rows. A band
keeps the region's first row, a `…` marker row and an `elided` block that names the missing rows, and its front matter
says `profile: compact`. Formulas are never cut: a fill range that touches the band is copied whole, so its first
cell, which the relative references hang on, stays with it. Formulas that point at another region or sheet keep the
reference but not the cells it points to.

For question answering over a workbook, passing the whole workbook in one Document usually beats chunking: the
benchmark answers came from reading every sheet at once. Use `mode="sheet"` when the workbook is too large for
the context window.
