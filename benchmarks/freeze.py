"""Write benchmarks/freeze/benchmark.json: the SHA-256 of every file the benchmark run depends on, and one digest.

  python3 benchmarks/freeze.py        # after external/realworld2.py build and external/spreadsheetbench.py

The digest is the SHA-256 of the lines '<path> <sha256>\\n' sorted by path. It depends only on paths and contents, not
on any commit, so it can be recomputed from any copy of the repository plus the two datasets (docs/PROTOCOL.md section 9).

The Damodaran workbooks are the one exception to hashing bytes. They are not redistributed: anyone rebuilding the set
downloads Damodaran's .xls files and converts them with LibreOffice, and a conversion never gives the same bytes twice.
So each is listed as '<path>#cells' with the SHA-256 of its content (cell_sha256), which a fresh conversion reproduces.
"""
import hashlib
import json
from pathlib import Path

BENCH = Path(__file__).resolve().parent
ROOT = BENCH.parent
RW2, SB = BENCH / "external" / "realworld2", BENCH / "external" / "spreadsheetbench"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _val(v) -> str:
    """repr of a cell value, except array and data-table formulas, whose repr carries an object address."""
    if hasattr(v, "ref") and hasattr(v, "text"):
        return f"ArrayFormula({v.ref!r}, {v.text!r})"
    if type(v).__name__ == "DataTableFormula":
        return "DataTableFormula(" + ", ".join(f"{k}={getattr(v, k, None)!r}" for k in ("ref", "ca", "dt2D", "dtr", "r1", "r2", "del1", "del2")) + ")"
    return repr(v)


def cell_sha256(path) -> str:
    """SHA-256 of what a workbook says, not of its bytes: sheet order, then per sheet its merged ranges, data
    validations and every non-empty cell's formula or typed value, cached value, number format and comment, then the
    defined names. Everything the encoders and the questions read is covered; zip timestamps and styles ids are not."""
    import warnings
    import openpyxl
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        f = openpyxl.load_workbook(path)
        v = openpyxl.load_workbook(path, data_only=True)
    lines = ["sheets\t" + "\t".join(f.sheetnames)]
    for ws in f.worksheets:
        wv = v[ws.title]
        lines.append(f"sheet\t{ws.title}\t{ws.sheet_state}")
        lines += [f"merge\t{r}" for r in sorted(str(r) for r in ws.merged_cells.ranges)]
        lines += [f"validation\t{d.sqref}\t{d.type}\t{d.formula1}\t{d.formula2}"
                  for d in sorted(ws.data_validations.dataValidation, key=lambda d: str(d.sqref))]
        for row in ws.iter_rows():
            for c in row:
                if c.value is None and c.comment is None:
                    continue
                cached = wv[c.coordinate].value
                note = c.comment.text if c.comment else ""
                lines.append(f"cell\t{c.coordinate}\t{_val(c.value)}\t{_val(cached)}\t{c.number_format}\t{note!r}")
    for name, dn in sorted(f.defined_names.items()):
        lines.append(f"name\t{name}\t{dn.attr_text}")
    for ws in f.worksheets:
        for name, dn in sorted(ws.defined_names.items()):
            lines.append(f"name\t{ws.title}!{name}\t{dn.attr_text}")
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def by_content(p: Path) -> bool:
    return p.parent == RW2 / "workbooks" and p.name.startswith("rw2_dam_")


def paths():
    out = [ROOT / "docs" / "PROTOCOL.md", ROOT / "docs" / "SPEC.md", ROOT / "src" / "cellprose" / "writer.py",
           BENCH / "split.json", BENCH / "encoders.py", BENCH / "score.py", BENCH / "analyze.py", BENCH / "stats.py",
           BENCH / "limitations.py", BENCH / "api_run.py", BENCH / "api_agent.py", BENCH / "preflight.py",
           BENCH / "package-lock.json",
           BENCH / "external" / "realworld2.py", BENCH / "external" / "spreadsheetbench.py", Path(__file__).resolve(),
           RW2 / "selection.json", RW2 / "manifest.json"]
    out += sorted((BENCH / "runner").glob("*.py"))
    for d in (RW2, SB):
        out += sorted((d / "questions").glob("*.json")) + sorted((d / "workbooks").glob("*.xlsx"))
    return out


def main():
    files = {str(p.relative_to(ROOT)) + ("#cells" if by_content(p) else ""): cell_sha256(p) if by_content(p) else sha(p)
             for p in paths()}
    digest = hashlib.sha256("".join(f"{k} {v}\n" for k, v in sorted(files.items())).encode()).hexdigest()
    (BENCH / "freeze").mkdir(exist_ok=True)
    (BENCH / "freeze" / "benchmark.json").write_text(json.dumps(
        {"digest": digest, "how": "sha256 of the lines '<path> <sha256>\\n' sorted by path", "files": files},
        indent=1) + "\n")
    print(f"benchmark digest {digest} over {len(files)} files")


if __name__ == "__main__":
    main()
