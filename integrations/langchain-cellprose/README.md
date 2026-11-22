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

For question answering over a workbook, passing the whole workbook in one Document usually beats chunking: the
benchmark answers came from reading every sheet at once. Use `mode="sheet"` when the workbook is too large for
the context window.
