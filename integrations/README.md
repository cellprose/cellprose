# Integrations

Thin adapters that put Cellprose where people already load spreadsheets. Each is its own package, depends on
`cellprose`, and is tested in CI (`.github/workflows/ci.yml`, job `integrations`).

| Package | What it does |
|---|---|
| [`markitdown-cellprose`](markitdown-cellprose/) | MarkItDown plugin: `markitdown --use-plugins book.xlsx` writes Cellprose instead of plain tables |
| [`langchain-cellprose`](langchain-cellprose/) | `CellproseLoader`, a LangChain document loader (whole workbook or one Document per sheet), and `CellproseSplitter`, which splits by sheet or region and keeps formulas with their tables |
| [`llama-index-readers-cellprose`](llama-index-readers-cellprose/) | `CellproseReader`, a LlamaIndex reader that also plugs into `SimpleDirectoryReader` |

All three default to `recalc="never"`, so they never start LibreOffice; formulas without cached values print as `?`.
`split_sheets` is copied into the LangChain and LlamaIndex packages so each installs on its own; keep the copies equal.

Not published yet. To publish: `pip wheel --no-deps -w dist <package>` then `twine upload dist/*`, after
`cellprose` itself is on PyPI.
