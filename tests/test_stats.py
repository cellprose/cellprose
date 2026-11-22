"""`cellprose stats`: sizes per format, offline."""
import json

import openpyxl
import pytest

from cellprose import stats
from cellprose.cli import main


@pytest.fixture
def book(tmp_path):
    p = tmp_path / "b.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["Item", "Qty", "Note"])
    ws.append(["Bolt", 3, "a|b"])
    ws.append(["Nut", 4, None])
    wb.save(p)
    return p


def test_baselines(book):
    assert stats.to_csv(book) == "## Data\nItem,Qty,Note\nBolt,3,a|b\nNut,4,\n"
    md = stats.to_markdown(book)
    assert "| Item | Qty | Note |" in md and "a\\|b" in md


def test_compute_without_tokens(book):
    r = stats.compute(book, tokens=False)
    assert r["tokenizer"] is None
    assert set(r["formats"]) == {"cellprose", "csv", "markdown"}
    assert all(v["chars"] > 0 and v["tokens"] is None for v in r["formats"].values())


def test_cli_no_tokens(book, capsys):
    assert main(["stats", "--no-tokens", str(book)]) == 0
    out = capsys.readouterr().out
    assert "| cellprose |" in out and "tokens" not in out.split("\n")[1]


def test_cli_json_with_tokens(book, capsys):
    pytest.importorskip("tiktoken")
    try:
        stats.counter()
    except RuntimeError:
        pytest.skip("tiktoken vocabulary unavailable offline")
    assert main(["stats", "--json", str(book)]) == 0
    data = json.loads(capsys.readouterr().out)[str(book)]
    assert data["tokenizer"] == "o200k_base"
    assert data["formats"]["csv"]["tokens"] > 0


def test_pct():
    assert stats._pct(110, 100) == "+10.0%" and stats._pct(1, 0) == "n/a"


def test_ci_sample_baseline_covers_the_benchmark_workbooks():
    """The CI token check (benchmarks/ci_sample.py) compares against ci_baseline.json; a new workbook needs --update."""
    import json
    from pathlib import Path
    bench = Path(__file__).parent.parent / "benchmarks"
    base = json.loads((bench / "ci_baseline.json").read_text())["workbooks"]
    assert set(base) == {p.stem for p in (bench / "workbooks").glob("*.xlsx")}
