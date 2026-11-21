"""End-to-end test: start the MCP server over stdio and call each tool like an agent would."""
import os
import shutil
import sys
from pathlib import Path

import anyio
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from cellprose.recalc import soffice

BENCH = Path(__file__).parent.parent / "benchmarks" / "workbooks"


def _text(result) -> str:
    return "".join(getattr(c, "text", "") for c in result.content)


async def _session_run(fn, env=None):
    params = StdioServerParameters(command=sys.executable, args=["-m", "cellprose.mcp_server"], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await fn(session)


def test_tools_listed():
    async def fn(s):
        tools = await s.list_tools()
        return {t.name for t in tools.tools}
    assert anyio.run(_session_run, fn) == {"list_sheets", "index_workbook", "read_ranges", "read_workbook", "write_cells", "outline_workbook", "find_cells", "trace_cell", "whatif"}


def test_list_and_read(tmp_path):
    book = tmp_path / "model.xlsx"
    shutil.copy(BENCH / "05_multisheet_model.xlsx", book)

    async def fn(s):
        listing = _text(await s.call_tool("list_sheets", {"path": str(book)}))
        sheet = _text(await s.call_tool("read_workbook", {"path": str(book), "sheet": "Summary"}))
        return listing, sheet
    listing, sheet = anyio.run(_session_run, fn)
    assert "4 sheet(s)" in listing and "Summary" in listing
    assert sheet.startswith("---\ncellprose: 0.3")
    assert "# Sheet: Summary" in sheet and "# Sheet: Inputs" not in sheet
    assert "B2:D2 = Revenue!B5" in sheet


def test_read_elides_long_blocks(tmp_path):
    book = tmp_path / "sales.xlsx"
    shutil.copy(BENCH / "01_sales_log.xlsx", book)

    async def fn(s):
        return _text(await s.call_tool("read_workbook", {"path": str(book), "max_rows": 20}))
    text = anyio.run(_session_run, fn)
    assert "profile: compact" in text and "```elided" in text
    assert "H2:H151 = F2*G2" in text  # formulas still cover every row


@pytest.mark.skipif(soffice() is None, reason="LibreOffice not installed")
def test_write_reports_impact(tmp_path):
    book = tmp_path / "pnl.xlsx"
    shutil.copy(BENCH / "03_pnl_quarterly.xlsx", book)

    async def fn(s):
        return _text(await s.call_tool("write_cells", {"path": str(book),
                                                        "edits": [{"cell": "P&L!B15", "value": 20000}]}))
    out = anyio.run(_session_run, fn)
    assert (tmp_path / "pnl.edited.xlsx").exists()
    assert "P&L!B7: 18000 -> 20000" in out  # Opex Q1 follows the named input
    assert "P&L!F8" in out                   # full-year EBITDA changed
    assert "P&L!F4" not in out               # revenue did not


@pytest.mark.skipif(soffice() is None, reason="LibreOffice not installed")
def test_whatif_does_not_modify(tmp_path):
    book = tmp_path / "pnl.xlsx"
    shutil.copy(BENCH / "03_pnl_quarterly.xlsx", book)
    before = book.read_bytes()

    async def fn(s):
        return _text(await s.call_tool("whatif", {"path": str(book), "cell": "P&L!B15", "value": 20000}))
    out = anyio.run(_session_run, fn)
    assert "15 other cells change value: P&L!B7:F9" in out
    assert book.read_bytes() == before


def test_whatif_rejects_value_and_factor_together(tmp_path):
    book = tmp_path / "pnl.xlsx"
    shutil.copy(BENCH / "03_pnl_quarterly.xlsx", book)

    async def fn(s):
        return await s.call_tool("whatif", {"path": str(book), "cell": "P&L!B15", "value": 5, "factor": 2})
    result = anyio.run(_session_run, fn)
    assert getattr(result, "is_error", None) or getattr(result, "isError", False)
    assert "exactly one" in _text(result)


@pytest.mark.skipif(os.path.exists("/Applications/LibreOffice.app"), reason="soffice is found outside PATH on macOS")
def test_whatif_reports_missing_libreoffice(tmp_path):
    book = tmp_path / "pnl.xlsx"
    shutil.copy(BENCH / "03_pnl_quarterly.xlsx", book)
    env = {"PATH": "/nonexistent"}

    async def fn(s):
        return await s.call_tool("whatif", {"path": str(book), "cell": "P&L!B15", "value": 1})
    result = anyio.run(_session_run, fn, env)
    assert getattr(result, "is_error", None) or getattr(result, "isError", False)
    assert "LibreOffice" in _text(result)


def test_root_restriction(tmp_path):
    book = tmp_path / "pnl.xlsx"
    shutil.copy(BENCH / "03_pnl_quarterly.xlsx", book)
    env = {"CELLPROSE_ROOT": str(tmp_path / "elsewhere"), "PATH": "/usr/bin:/bin"}

    async def fn(s):
        return await s.call_tool("read_workbook", {"path": str(book)})
    result = anyio.run(_session_run, fn, env)
    assert getattr(result, "is_error", None) or getattr(result, "isError", False)
    assert "outside CELLPROSE_ROOT" in _text(result)


def test_lean_kit_matches_the_benchmarked_tools(tmp_path):
    """index_workbook, read_ranges and trace_cell return what the benchmark's lean arm saw (benchmarks/runner/agent.py)."""
    from cellprose import tools
    book = tmp_path / "model.xlsx"
    shutil.copy(BENCH / "05_multisheet_model.xlsx", book)

    async def fn(s):
        idx = _text(await s.call_tool("index_workbook", {"path": str(book)}))
        rng = _text(await s.call_tool("read_ranges", {"path": str(book), "ranges": ["Summary!A1:D3", "Inputs!A1:B2"]}))
        tr = _text(await s.call_tool("trace_cell", {"path": str(book), "cell": "Summary!B2"}))
        bad = await s.call_tool("read_ranges", {"path": str(book), "ranges": []})
        return idx, rng, tr, bad
    idx, rng, tr, bad = anyio.run(_session_run, fn)
    assert idx == tools.index(book).replace("read_range", "read_ranges")
    assert rng == tools.read_ranges(book, ["Summary!A1:D3", "Inputs!A1:B2"])
    assert "# Sheet: Summary" in rng and "# Sheet: Inputs" in rng and "```formats" not in rng
    assert tr == tools.trace(book, "Summary!B2", compact=True)
    assert getattr(bad, "is_error", None) or getattr(bad, "isError", False)
