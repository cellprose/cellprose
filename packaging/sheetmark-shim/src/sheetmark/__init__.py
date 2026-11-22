"""Compatibility shim: Sheetmark was renamed to Cellprose. `import sheetmark` forwards every attribute and submodule to `cellprose`."""
import sys
import warnings

import cellprose

warnings.warn("the 'sheetmark' package was renamed to 'cellprose'; install and import cellprose instead",
              DeprecationWarning, stacklevel=2)

for _name in ("reader", "writer", "recalc", "cli", "gitflow", "stats", "mcp_server"):
    try:
        sys.modules[f"sheetmark.{_name}"] = __import__(f"cellprose.{_name}", fromlist=["_"])
    except ImportError:       # stats needs tiktoken, mcp_server needs the MCP SDK
        pass


def __getattr__(name):
    return getattr(cellprose, name)


def main() -> int:
    from cellprose.cli import main as _main
    return _main()


def mcp_main():
    from cellprose.mcp_server import main as _main
    return _main()
