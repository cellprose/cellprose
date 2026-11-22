# llama-index-readers-cellprose

A LlamaIndex reader that loads `.xlsx` and `.xlsm` workbooks as [Cellprose](https://cellprose.com) text, keeping
formulas, cell addresses and every sheet in valid Markdown.

```bash
pip install llama-index-readers-cellprose
```

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.cellprose import CellproseReader

docs = CellproseReader().load_data("book.xlsx")              # one Document per workbook
docs = CellproseReader(mode="sheet").load_data("book.xlsx")  # one per sheet, metadata["sheet"] set
docs = SimpleDirectoryReader("data", file_extractor={".xlsx": CellproseReader()}).load_data()
```
