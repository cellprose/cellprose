import datetime as dt
import random
import shutil
from pathlib import Path

import openpyxl
import pytest

import cellprose
from cellprose.cli import main as cli
from cellprose.reader import CompactProfileError, ParseError, decode_cell, split_row
from cellprose.recalc import recalc_copy, soffice
from cellprose.writer import fmt_value

import corpus

ROOT = Path(__file__).parent
BENCH = ROOT.parent / "benchmarks" / "workbooks"
GOLDEN = ROOT / "golden"
needs_lo = pytest.mark.skipif(soffice() is None, reason="LibreOffice is needed to recompute formulas")

NASTY = ['"hello"', '"x', 'x"', "<br>", "a<br>b", "\\", "a\\", "a\\|b", "\\|", "||", "|", "C:\\dir\\", "12:30:00", "10:30",
         "=x", "'=x", "'", "''", "'abc", "#N/A", "#REF! broken", "TRUE", "true", "?", "2026-10-07", "2026-10-07 note",
         " lead", "trail ", "  ", '"', '""', '" "', "- 5", "1e5", "1,5", "a\nb", "tab\tx", "…", "x…", "=SUM(1)", "+5",
         "-", ".", "5.", ".5", "<BR>", "\\<br>", "a\\\\|b", "'x ", "' x ", "0012", "1/2", "#", "#a", "nan", "12:30:00.5"]


def cell_roundtrip(text):
    """text -> grid cell -> text, through the same split and decode the reader uses."""
    (raw,) = split_row(f"|{fmt_value(text)}|", 1)
    return decode_cell(raw)


# ---- value encoding is invertible ---------------------------------------------------------------

@pytest.mark.parametrize("text", NASTY)
def test_text_survives_the_grid(text):
    assert cell_roundtrip(text) == (text, False)


def test_random_text_survives_the_grid():
    rng = random.Random(7)
    alphabet = list("\"'\\|<>brTRUEtrue 0123456789:-.eE\n…/!AZ=#?") + ["<br>", "\\|", '""', "12:30:00", "2026-01-02", "#N/A"]
    for _ in range(3000):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 9)))
        assert cell_roundtrip(s) == (s, False), repr(s)


def test_line_breaks_are_normalised_to_lf():
    assert cell_roundtrip("a\r\nb\rc") == ("a\nb\nc", False)


@pytest.mark.parametrize("value", [0, 7, -3, 0.1, 1.5e-7, 123456789012, 2.5, True, False,
                                   dt.datetime(2026, 10, 7), dt.datetime(2026, 10, 7, 14, 30, 5), dt.time(9, 5, 0)])
def test_typed_values_survive_the_grid(value):
    got, err = cell_roundtrip(value)
    assert got == value and type(got) is type(value) and not err


@pytest.mark.parametrize("err", ["#DIV/0!", "#N/A", "#REF!", "#VALUE!", "#NAME?", "#NUM!", "#NULL!"])
def test_error_literals(err):
    assert decode_cell(fmt_value(err, error=True)) == (err, True)


def test_escapes_in_split_row():
    assert split_row("|a\\|b|c\\\\|d|", 1) == ["a\\|b", "c\\\\", "d"]
    with pytest.raises(ParseError):
        split_row("|a|b", 1)


# ---- structure ---------------------------------------------------------------------------------

def test_design_example_parses():
    wb = cellprose.load((GOLDEN / "design_example.sheet.md").read_text())
    assert [s.name for s in wb.sheets] == ["P&L"] and wb.names == {"Growth": "Assumptions!$B$2", "Price": "Assumptions!$B$3"}
    c = wb.sheet("P&L").cells
    assert c[(2, 2)].value == 1200 and c[(2, 2)].formula is None          # typed in
    assert [c[(2, k)].formula for k in (3, 4, 5)] == ["B2*(1+Growth)", "C2*(1+Growth)", "D2*(1+Growth)"]   # fill range
    assert [c[(4, k)].formula for k in (2, 5)] == ["B2*B3", "E2*E3"]
    assert c[(3, 2)].formula == "Price" and c[(3, 5)].formula == "Price"
    assert c[(4, 6)].number_format == "$#,##0" and c[(4, 2)].number_format == "$#,##0"
    assert c[(2, 6)].formula == "SUM(B2:E2)" and c[(2, 6)].value is None


def test_design_example_to_xlsx(tmp_path):
    out = cellprose.load((GOLDEN / "design_example.sheet.md").read_text()).to_xlsx(tmp_path / "x.xlsx")
    ws = openpyxl.load_workbook(out)["P&L"]
    assert ws["D4"].value == "=D2*D3" and ws["A2"].value == "Units" and ws["B2"].value == 1200
    assert ws["F4"].number_format == "$#,##0"
    assert openpyxl.load_workbook(out).defined_names["Growth"].attr_text == "Assumptions!$B$2"


def test_sheet_state_freeze_merges_and_local_names_are_read():
    text = ("---\nsheetmark: 0.2\n---\n\n# Sheet: \"Q1 #2\"\n\n```meta\nhidden: true\nfreeze: B2\n```\n\n"
            "## A1:B2\n\n|#|A|B|\n|-|-|-|\n|1|x|1|\n|2|y|2|\n\n```merges\nA1:B1\n```\n\n# Names\n\n```names\nQ1 #2!Loc = $B$2\n```\n")
    s = cellprose.load(text).sheets[0]
    assert (s.name, s.state, s.freeze, s.merges, s.names) == ("Q1 #2", "hidden", "B2", ["A1:B1"], {"Loc": "$B$2"})


@pytest.mark.parametrize("text,fragment", [
    ("# Sheet: A\n", "front matter"),
    ("---\ncellprose: 0.1\n---\n", "unsupported cellprose version"),
    ("---\nsheetmark: 0.2\n", "not closed"),
    ("---\nsheetmark: 0.2\n---\n\n# Sheet: A\n\n|#|A|\n|-|-|\n|1|x|y|\n", "expected 2 cells"),
    ("---\nsheetmark: 0.2\n---\n\n# Sheet: A\n\n|#|A|\n|x|y|\n", "separator"),
    ("---\nsheetmark: 0.2\n---\n\n# Sheet: A\n\n```formulas\nA1 = 1\n", "unclosed"),
    ("---\nsheetmark: 0.2\n---\n\n# Sheet: A\n\n```formulas\nnonsense\n```\n", "RANGE ="),
    ("---\nsheetmark: 0.2\n---\n\n# Names\n\n```names\nNoSuch!x = 1\n```\n", "unknown sheet"),
])
def test_malformed_files_raise_with_a_line_number(text, fragment):
    with pytest.raises(ParseError, match=fragment) as e:
        cellprose.load(text)
    assert e.value.line


def test_compact_profile_is_refused():
    with pytest.raises(CompactProfileError):
        cellprose.load("---\nsheetmark: 0.2\nprofile: compact\n---\n")


def test_unknown_lines_are_warnings_not_errors():
    wb = cellprose.load("---\nsheetmark: 0.2\n---\n\n# Sheet: A\n\nsome prose\n")
    assert wb.warnings and "some prose" in wb.warnings[0]


# ---- values survive an actual .xlsx, no LibreOffice needed -------------------------------------

def test_text_and_types_survive_xlsx(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "S"
    for i, v in enumerate(NASTY + corpus.LOOKALIKES, start=1):
        ws.cell(row=i, column=1).value = v
        ws.cell(row=i, column=1).data_type = "s"
        ws.cell(row=i, column=2).value = i
    src = tmp_path / "a.xlsx"
    wb.save(src)
    out = cellprose.load(cellprose.dumps(src, recalc="never")).to_xlsx(tmp_path / "b.xlsx")
    a, b = openpyxl.load_workbook(src)["S"], openpyxl.load_workbook(out)["S"]
    for i, v in enumerate(NASTY + corpus.LOOKALIKES, start=1):
        assert (b.cell(row=i, column=1).value, b.cell(row=i, column=1).data_type) == (v, "s"), repr(v)
        assert a.cell(row=i, column=1).value == v


def test_formula_lookalike_text_is_not_a_formula(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"], ws["B1"] = "=not a formula", 1
    ws["A1"].data_type = "s"
    ws["A2"], ws["B2"] = "=B1*2", None
    src = tmp_path / "a.xlsx"
    wb.save(src)
    text = cellprose.dumps(src, recalc="never")
    assert "\n1|'=not a formula|1\n" in text and "A2 = B1*2" in text and "A1 =" not in text


# ---- round trips through LibreOffice -----------------------------------------------------------

def roundtrip(xlsx: Path, tmp: Path):
    """encode -> decode -> .xlsx -> recalculate -> encode. The output keeps the input's file name so the
    `source:` line matches. Returns both texts and the decoded .xlsx."""
    first = cellprose.dumps(xlsx)
    out = tmp / "rt"
    out.mkdir()
    decoded = cellprose.load(first).to_xlsx(out / xlsx.name)
    return first, cellprose.dumps(decoded), decoded


@needs_lo
@pytest.mark.parametrize("name", sorted(p.name for p in BENCH.glob("*.xlsx")))
def test_benchmark_workbook_roundtrip_is_byte_identical(name, tmp_path):
    first, second, decoded = roundtrip(BENCH / name, tmp_path)
    assert second == first
    assert corpus.content(decoded) == corpus.content(BENCH / name)       # formulas and typed values, not just text


@needs_lo
def test_edge_case_workbook_roundtrip(tmp_path):
    # Start from a LibreOffice-saved copy so formulas have cached values, as in a file saved by Excel. (dumps()
    # reads a file without cached values through LibreOffice, which can rewrite number-format strings.)
    raw = corpus.edge_workbook(tmp_path / "raw.xlsx")
    src = tmp_path / "edge.xlsx"
    src.write_bytes(recalc_copy(raw).read_bytes())
    first, second, decoded = roundtrip(src, tmp_path)
    assert second == first
    got, want = corpus.content(decoded), corpus.content(src)
    assert got["names"] == want["names"]
    for sheet, w in want["sheets"].items():
        g = got["sheets"][sheet]
        assert {k: v for k, v in g.items() if k != "cells"} == {k: v for k, v in w.items() if k != "cells"}
        assert g["cells"].keys() == w["cells"].keys()
        for addr, (kind, value, fmt) in w["cells"].items():
            gkind, gvalue, gfmt = g["cells"][addr]
            assert (gkind, gvalue) == (kind, value), (sheet, addr)
            assert fmt is None or gfmt == fmt, (sheet, addr)       # fmt is None for loose cells: not kept in v0.2


def test_edge_workbook_semantics_without_recalc(tmp_path):
    """Same check as above but with no LibreOffice: decode straight from the first encoding."""
    src = corpus.edge_workbook(tmp_path / "edge.xlsx")
    text = cellprose.dumps(src, recalc="never")
    decoded = cellprose.load(text).to_xlsx(tmp_path / "out.xlsx")
    ws = openpyxl.load_workbook(decoded)
    assert ws["Hidden"].sheet_state == "hidden" and ws["P&L"].freeze_panes == "B2"
    assert ws["Q1 #2"].merged_cells.ranges and ws["P&L"]["E3"].value == 51.5            # typed-in override
    assert ws["P&L"]["D2"].value == "=C2*(1+Growth)" and ws["P&L"]["C3"].value == "=Assumptions!$B$3"
    assert ws["Assumptions"]["B4"].value == dt.datetime(2026, 1, 31)
    assert ws["Assumptions"]["B5"].value == dt.datetime(2026, 10, 7, 14, 30, 5)
    assert ws["Q1 #2"]["K24"].value == dt.datetime(2026, 12, 25)                         # loose date stays a date
    assert [c.value for c in ws["Q1 #2"]["A"][3:3 + len(corpus.LOOKALIKES)]] == corpus.LOOKALIKES


# ---- CLI ---------------------------------------------------------------------------------------

def test_cli_decode_and_check(tmp_path, capsys):
    md = tmp_path / "book.sheet.md"
    shutil.copy(GOLDEN / "design_example.sheet.md", md)
    assert cli(["check", str(md)]) == 0
    assert cli(["decode", str(md)]) == 0
    assert (tmp_path / "book.xlsx").exists()
    bad = tmp_path / "bad.sheet.md"
    bad.write_text("not cellprose")
    assert cli(["check", str(bad)]) == 1 and cli(["decode", str(bad)]) == 1
    assert "front matter" in capsys.readouterr().err


@pytest.mark.parametrize("value", [53.779999999999994, 37095.979999999996, 315726.07000000007, 0.1 + 0.2, 1e-300])
def test_17_digit_floats_survive_to_xlsx(value, tmp_path):
    """openpyxl writes numbers with %.16g, which cuts the last digit of 17-digit floats."""
    from cellprose.reader import _exact_floats
    wb = openpyxl.Workbook()
    wb.active["A1"] = value
    src = tmp_path / "f.xlsx"
    with _exact_floats():       # (the fixture itself must not lose the digits)
        wb.save(src)
    back = cellprose.load(cellprose.dumps(src)).to_xlsx(tmp_path / "g.xlsx")
    assert openpyxl.load_workbook(back).active["A1"].value == value


@pytest.mark.skipif(soffice() is None, reason="LibreOffice is needed to recompute formulas")
def test_text_formulas_decode_and_recompute(tmp_path):
    """Formulas that return text are rewritten and recomputed like any other (the ogl13 #NAME? comes from its
    external-workbook references, whose link is not part of the format)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["k", "v"])
    ws.append(["a", "=UPPER(A2)"])
    ws.append(["b", "=VLOOKUP(A3,A2:B3,1,FALSE)"])
    ws.append(["c", "=A2&A3"])
    src = tmp_path / "t.xlsx"
    wb.save(src)
    first = cellprose.dumps(src)
    back = cellprose.load(first).to_xlsx(tmp_path / "u.xlsx")
    assert "#NAME?" not in cellprose.dumps(back)
    assert cellprose.dumps(back).split("---\n", 2)[2] == first.split("---\n", 2)[2]


# ---- known limits (SPEC §12) -------------------------------------------------------------------

def test_known_limits_are_as_the_spec_says(tmp_path):
    """Pins SPEC §12 so a change in behaviour shows up as a spec change: CRLF reads back as LF, a decoded
    formula has no cached value, and a loose cell keeps its number format."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "S"
    ws["A1"], ws["A2"], ws["A3"] = "a\r\nb", 2, "=A2*3"
    ws["F9"] = 0.25
    ws["F9"].number_format = "0.0%"                                     # a loose cell: touches no other cell
    src = tmp_path / "limits.xlsx"
    wb.save(src)
    text = cellprose.dumps(src, recalc="never")
    out = cellprose.load(text).to_xlsx(tmp_path / "out.xlsx")
    assert openpyxl.load_workbook(out)["S"]["A1"].value == "a\nb"                              # line break is LF
    assert openpyxl.load_workbook(out)["S"]["A3"].value == "=A2*3"
    assert openpyxl.load_workbook(out, data_only=True)["S"]["A3"].value is None                # no cached value
    assert openpyxl.load_workbook(out)["S"]["F9"].number_format == "0.0%"                      # loose format kept


MIXED = ("---\ncellprose: 0.3\n---\n\n# Sheet: S\n\n## A1:D2\n\n#|A|B|C|D\n-|-|-|-|-\n1|hi|2.5|#N/A|6\n2|x|3|4|5\n\n"
         "```formulas\nA1 = VLOOKUP(A2,'[1]Master Sheet '!$A$1:$B$2,2,FALSE)\nB1 = '[1]Master Sheet '!B1*2\n"
         "C1 = '[2]Other'!C1\nD1 = B2*2\n```\n")


@pytest.mark.skipif(soffice() is None, reason="LibreOffice is needed to recompute formulas")
@pytest.mark.parametrize("recalc", ["never", "always"])
def test_external_workbook_formulas_keep_their_shown_result(recalc, tmp_path):
    """The link behind [n] is not part of the format: the shown result is cached, the formula is kept as written,
    and the file carries a link part, so it round-trips even next to ordinary formulas that LibreOffice recomputes."""
    import zipfile
    wb = cellprose.load(MIXED)
    out = wb.to_xlsx(tmp_path / "e.xlsx", recalc=recalc)
    assert any("another workbook" in w for w in wb.warnings)
    vals, forms = openpyxl.load_workbook(out, data_only=True).active, openpyxl.load_workbook(out).active
    assert (vals["A1"].value, vals["B1"].value, vals["C1"].value) == ("hi", 2.5, "#N/A")
    assert forms["A1"].value == "=VLOOKUP(A2,'[1]Master Sheet '!$A$1:$B$2,2,FALSE)"
    assert forms["B1"].value == "='[1]Master Sheet '!B1*2"
    names = zipfile.ZipFile(out).namelist()
    assert "xl/externalLinks/externalLink1.xml" in names and "xl/externalLinks/externalLink2.xml" in names
    assert cellprose.dumps(out, legend=False).split("---\n", 2)[2] == MIXED.split("---\n", 2)[2]
