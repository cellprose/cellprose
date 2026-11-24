"""The skill ships a vendored copy of the package so it works with only openpyxl installed. It must not drift."""
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src" / "cellprose"
VENDOR = ROOT / "skills" / "cellprose" / "scripts" / "_vendor" / "cellprose"
NOT_VENDORED = {"mcp_server.py"}      # needs the MCP SDK, which the skill does not depend on
REFRESH = "cp src/cellprose/{__init__,_sparse,reader,writer,recalc,cli,gitflow,tools}.py skills/cellprose/scripts/_vendor/cellprose/"


def test_vendored_copy_is_current():
    stale = [p.name for p in VENDOR.glob("*.py") if p.read_bytes() != (SRC / p.name).read_bytes()]
    assert not stale, f"stale vendored files {stale}; refresh with: {REFRESH}"


def test_vendored_copy_has_every_module_the_package_imports():
    missing = sorted(p.name for p in SRC.glob("*.py") if p.name not in NOT_VENDORED and not (VENDOR / p.name).exists())
    # stats.py is only used by `cellprose stats`, which the skill does not call
    assert set(missing) <= {"stats.py"}, f"missing from the vendored copy: {missing}"
