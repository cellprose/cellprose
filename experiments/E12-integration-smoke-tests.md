# E12: MCP server and agent skill in Claude Code

**Date:** 2026-10-08 · **Status:** passed

## Question

Do the MCP server and the agent skill work in a real agent session, and do they lead to correct answers?

## Setup

| Test | Configuration | Question |
| --- | --- | --- |
| MCP server | Claude Code (Sonnet), `--mcp-config` with `sheetmark-mcp` limited to one folder; only the three Sheetmark tools allowed | "In forecast.xlsx: which bookings months are typed-in overrides, and if monthly growth rose to 5%, which cells would change?" (workbook `11_forecast_overrides`) |
| Agent skill | Claude Code (Sonnet), `skills/sheetmark` copied into the project's `.claude/skills/`; Bash, Read and Skill tools | "If someone raises the Upside growth assumption, does Y5 free cash flow change?" (workbook `13_scenario_switch`) |

Code: [`src/sheetmark/mcp_server.py`](../src/sheetmark/mcp_server.py), [`skills/sheetmark/`](../skills/sheetmark/).

## Results

| Test | Outcome | Turns | Cost |
| --- | --- | --- | --- |
| MCP server | Correct. Found both overrides (F2 May, J2 Sep) and named exactly the 20 cells the ground truth lists | 2 | $0.02 |
| Agent skill | Correct. Loaded the skill without being asked, ran the bundled converter, and explained that C4 is unused because `CHOOSE` selects Base. Its estimate if Upside were active (~535k) matched the recalculated 534,997 | 4 | $0.08 |

The automated suite ([`tests/`](../tests/)) also passes: 20 tests against MCP SDK 1.30 and 2.2. It covers stdio tool calls, folder restriction, elision of long blocks, and edit-impact reporting.

## Limits

- One run each, on our own workbooks.
- `write_cells` saves through openpyxl, which can drop charts, images and pivot tables. That's why it writes a copy by default.
