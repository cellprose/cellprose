# markitdown-cellprose

A [MarkItDown](https://github.com/microsoft/markitdown) plugin that converts `.xlsx` and `.xlsm` workbooks to
[Cellprose](https://cellprose.com) instead of plain Markdown tables. The output keeps formulas, cell addresses,
merged cells and every sheet, and it is still valid GitHub-Flavored Markdown.

```bash
pip install markitdown-cellprose
markitdown --use-plugins book.xlsx > book.sheet.md
```

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)
print(md.convert("book.xlsx").markdown)
# options: md.convert("book.xlsx", cellprose_options={"recalc": "auto", "max_rows": 200})
```

Formulas without cached values print as `?` unless you pass `recalc="auto"` and LibreOffice is installed.
Other file types go to MarkItDown's own converters as before.
