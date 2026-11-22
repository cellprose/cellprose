"""Backlog B20: the fill-range hint variant (experimental, opt-in)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))
import api_agent  # noqa: E402
import encoders  # noqa: E402
from runner.prompts import AGENT_FILES  # noqa: E402

BASE = encoders.ROOT / "encoded"


def test_hint_shows_the_last_cell_of_a_shifting_range_and_skips_the_rest():
    text = "```formulas\nB4:E4 = B2*B3\nB3:E3 = Price\nF2 = SUM(B2:E2)\nA9:A11 = $B$1*A8\n```\n| not a formula | A1:B2 = x |\n"
    out = encoders.add_fill_hints(text).split("\n")
    assert out[1] == "B4:E4 = B2*B3  # E4 = E2*E3"
    assert out[2] == "B3:E3 = Price"                  # no relative reference: nothing to show
    assert out[3] == "F2 = SUM(B2:E2)"                # single cell
    assert out[4] == "A9:A11 = $B$1*A8  # A11 = $B$1*A10"
    assert out[-2] == "| not a formula | A1:B2 = x |"   # only formulas blocks are touched


@pytest.mark.parametrize("p", sorted(BASE.glob("*.sheetmark_lean_gfm.txt")))
def test_committed_hint_files_are_the_v02_files_plus_comments(p):
    hint = p.with_name(p.name.replace("lean_gfm.txt", "lean_gfm_hint.txt"))
    assert hint.read_text() == encoders.add_fill_hints(p.read_text())
    base_lines, hint_lines = p.read_text().split("\n"), hint.read_text().split("\n")
    assert len(base_lines) == len(hint_lines)             # comments only: no line added or removed
    assert all(h == b or h.startswith(b + "  # ") for b, h in zip(base_lines, hint_lines))


def test_the_v02_reader_rejects_the_hint_comment():
    """Why this stays an experiment: adopting it needs a spec and reader change (E22)."""
    sys.path.insert(0, str(ROOT / "src"))
    import cellprose
    text = ("---\nsheetmark: 0.2\n---\n\n# Sheet: S\n\n## A1:C3\n\n|#|A|B|C|\n|-|-|-|-|\n|1|1|2|3|\n|2|4|5|6|\n|3|?|?|?|\n"
            "```formulas\nA3:C3 = A1*A2  # C3 = C1*C2\n```\n")
    with pytest.raises(Exception):
        cellprose.load(text)


def test_hint_variant_is_opt_in_and_not_a_registered_encoding():
    assert "agent_sheetmark_hint" in api_agent.VARIANTS and "agent_sheetmark_hint" not in api_agent.DEFAULT_VARIANTS
    assert encoders.HINT_ENCODING not in encoders.ENCODINGS
    assert AGENT_FILES["agent_sheetmark_hint"][2] == "{wb}.sheetmark_lean_gfm_hint.txt"
    tin, tout, _ = api_agent.historic_tokens("agent_sheetmark_hint", ROOT / "benchmarks" / "results" / "raw")
    base_in, base_out, _ = api_agent.historic_tokens("agent_sheetmark", ROOT / "benchmarks" / "results" / "raw")
    assert tin == pytest.approx(base_in * 1.06) and tout == base_out
