"""Every headline number carries its limitations (docs/PROTOCOL.md section 10, backlog B22)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))
from limitations import LIMITATIONS, SHORT, block  # noqa: E402

# The short limits line for the 11 Nov 2026 run (benchmarks/RESULTS.md), which README.md quotes. It lives here, not in
# benchmarks/limitations.py, because that file is in the run's freeze list and must keep its frozen bytes.
RUN_SHORT = ("Limits: 30 real-world and 28 SpreadsheetBench workbooks, 3 repeats, four models on one date, rule-generated "
             "questions, list prices checked 2026-11-11 with every token uncached; nothing pooled across models or corpora.")


def test_documents_that_quote_a_headline_carry_the_short_limits():
    assert SHORT in (ROOT / "docs/DESIGN.md").read_text(), "DESIGN.md quotes a headline without the limits line"
    # README quotes the 11 Nov 2026 run, so it carries that run's line
    assert RUN_SHORT in (ROOT / "README.md").read_text(), "README.md quotes the run without its limits line"


def test_the_five_required_limits_are_listed():
    names = {k for k, _ in LIMITATIONS}
    assert {"Small test set", "All synthetic", "Prices", "Single turn", "Tokenizers"} <= names
    assert all(k in block() for k in names)


def test_report_prints_the_limits_after_its_tables():
    src = (ROOT / "benchmarks" / "report.py").read_text() + (ROOT / "benchmarks" / "analyze.py").read_text()
    assert src.count("block()") == 2
