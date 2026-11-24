# Integrations

Cellprose ships three things agents can use today:

| Piece | What it gives an agent | Where |
| --- | --- | --- |
| `cellprose` CLI and Python library | Convert any .xlsx/.xlsm to Cellprose text | `src/cellprose/` |
| MCP server (`cellprose-mcp`, or `cellprose mcp`) | Tools: `index_workbook`, `read_ranges`, `find_cells`, `trace_cell`, `whatif` (the kit the benchmark measured), plus `list_sheets`, `read_workbook`, `outline_workbook`, `write_cells` | `src/cellprose/mcp_server.py` |
| Agent skill | Teaches a model to read the format, and bundles a converter script | `skills/cellprose/` |

## Install

```bash
pip install "cellprose[mcp]"       # from PyPI; use pip install -e ".[mcp]" from a clone to develop
```

LibreOffice is optional. With it installed, files without cached formula values get computed, and `write_cells` can report what an edit changed.

## CLI

```bash
cellprose encode model.xlsx                      # writes model.sheet.md
cellprose encode model.xlsx -o - --sheet "P&L"   # one sheet to stdout
cellprose encode big.xlsx --max-rows 100         # compact profile for long tables
cellprose decode model.sheet.md                  # writes model.xlsx
cellprose decode model.sheet.md --recalc auto    # also cache formula values with LibreOffice (may rewrite formats)
cellprose check model.sheet.md                   # parse and validate, exit 1 on error
```

## MCP server

**Claude Code:**

```bash
claude mcp add cellprose -e CELLPROSE_ROOT="$HOME/work" -- cellprose-mcp
```

**Claude Desktop, Cursor, or any client that takes a JSON config:**

```json
{
  "mcpServers": {
    "cellprose": {
      "command": "cellprose-mcp",
      "env": { "CELLPROSE_ROOT": "/Users/you/work" }
    }
  }
}
```

`cellprose mcp` is the same server as `cellprose-mcp` (it is what `uvx --with "mcp>=1.2" cellprose mcp` runs). `CELLPROSE_ROOT` is optional. When set, the server only touches files inside that folder; when it is not set, the server can read and write any .xlsx/.xlsm the user can, so set it when the agent reads files you did not write.

| Tool | Read-only | What it does |
| --- | --- | --- |
| `index_workbook(path)` | yes | Start here. Each sheet's used range, then every region with its size, formula count and first row; about 30 tokens a region |
| `read_ranges(path, ranges, formats=false)` | yes | Up to 20 A1 ranges (`Sheet1!A1:F40`) in one call, as Cellprose tables with their fill-range formulas |
| `find_cells(path, text, sheet?)` | yes | Cells whose text contains `text`, each with the values to its right |
| `trace_cell(path, cell, dependents=false, transitive=false)` | yes | A formula's inputs, or the cells that read it, merged into ranges |
| `list_sheets(path)` | yes | Each sheet's used range, blocks, formula count and approximate token size |
| `outline_workbook(path)` | yes | Index plus every region with long ones cut to their first and last rows |
| `read_workbook(path, sheet?, cell_range?, max_rows=200)` | yes | The workbook, one sheet or one range as Cellprose |
| `write_cells(path, edits, output_path?, overwrite=false)` | no | Sets values or formulas, saves a copy (`<name>.edited.xlsx`) by default, recalculates, and lists every other cell whose value changed |
| `whatif(path, cell, value? / factor?)` | yes | Tries a change without saving: recalculates with LibreOffice and lists every other cell whose value would change. Reports an error naming LibreOffice if it is missing |

`index_workbook`, `read_ranges`, `find_cells`, `trace_cell` and `whatif` return what the benchmark's
"Cellprose with its own tools" arm saw, except that the text says `read_ranges` where the arm's tool was `read_range`, and
`trace_cell` is compact (addresses merged into ranges, no values; read values with `read_ranges`). The cost and accuracy
claims apply to a model that sticks to this lean kit; `read_workbook`, `outline_workbook` and `list_sheets` are not
what the arm had (Addendum A in `benchmarks/RESULTS.md`; `tests/test_mcp.py` checks it). In that arm
the index was in the first message; with the server, the model calls `index_workbook` first, which adds one turn.

Works with MCP Python SDK 1.x and 2.x.

## Agent skill

Copy `skills/cellprose/` into:

- **Claude Code:** `.claude/skills/` in a project, or `~/.claude/skills/` for every project.
- **Other agents that support skills:** their skills folder.

The skill triggers on spreadsheet tasks, explains how to read the format, and runs `scripts/cellprose_encode.py`. That script uses the installed package, or a vendored copy if the package isn't installed, so it only needs `openpyxl`.

After changing `src/cellprose/`, refresh the vendored copy:

```bash
cp src/cellprose/{__init__,reader,writer,recalc,cli,gitflow,tools}.py skills/cellprose/scripts/_vendor/cellprose/
```

## Verified

The automated tests (`pytest`) pass: 20 tests, against MCP SDK 1.30 and 2.2. They cover the writer, the stdio MCP tools, folder restriction, and edit impact.

Two manual checks were also run with Claude Code (Sonnet), October 2026:

| Check | Question | Result | Cost |
| --- | --- | --- | --- |
| MCP server | "Which bookings months are typed-in overrides, and what changes if growth rises to 5%?" | Found both overrides (May, Sep) and listed exactly the 20 cells the benchmark's ground truth expects | 2 turns, $0.02 |
| Skill | "If someone raises the Upside growth assumption, does Y5 free cash flow change?" | Triggered the skill by itself and answered correctly: no, because the Base scenario is selected via `CHOOSE`. Its estimate if Upside were selected (~535k) matched the recalculated value (534,997) | 4 turns, $0.08 |
