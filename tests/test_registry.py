"""server.json (Official MCP Registry) must match the package, and the README must carry the ownership line."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_server_json_matches_package():
    s = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    py = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
    assert s["version"] == py == s["packages"][0]["version"]
    assert f"<!-- mcp-name: {s['name']} -->" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_cli_has_mcp_subcommand():
    from cellprose.cli import main
    import pytest
    with pytest.raises(SystemExit) as e:
        main(["mcp", "--help"])
    assert e.value.code == 0


def test_readme_links_are_absolute():
    """PyPI and npm show README.md as-is and do not rewrite relative links, so every link and image must be absolute."""
    import re
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    bad = [t for t in re.findall(r"\]\(([^)\s]+)", text) if not t.startswith(("http://", "https://", "mailto:"))]
    assert not bad, f"relative README links break on PyPI: {bad}"
