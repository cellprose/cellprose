"""Git integration: a textconv diff driver for .xlsx and a pre-commit hook that keeps a sidecar Cellprose file."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .writer import Options, dumps_workbook, load_pair

EXT = ".sheet.md"  # the default sidecar extension
ALT_EXT = ".cellprose.md"  # equally supported; used when a repository already keeps its sidecars under it
DRIVER = "cellprose"
ATTRIBUTES_LINE = f"*.xlsx diff={DRIVER}"
HOOK_MARK = "# cellprose pre-commit hook"
HOOK_BODY = f"""{HOOK_MARK}
cellprose pre-commit || exit 1
"""


def sidecar(xlsx: Path) -> Path:
    """The sidecar of a workbook: `book.sheet.md`, or `book.cellprose.md` when only that one exists."""
    stem = xlsx.name[: -len(xlsx.suffix)]
    alt = xlsx.with_name(stem + ALT_EXT)
    if alt.exists() and not xlsx.with_name(stem + EXT).exists():
        return alt
    return xlsx.with_name(stem + EXT)


def textconv(path: str | Path) -> str:
    """Cellprose text of a workbook for `git diff`. Never recalculates (fast) and omits the source name,
    which for git is a temporary file and would show up as noise in every diff."""
    fwb, vwb = load_pair(Path(path))
    return dumps_workbook(fwb, vwb, Options(source=None))


def _git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def precommit(cwd: Path | None = None) -> int:
    """Write a sidecar for every staged .xlsx/.xlsm and stage it; drop the sidecar of a deleted workbook."""
    root = Path(_git("rev-parse", "--show-toplevel", cwd=cwd).strip())
    out = _git("diff", "--cached", "--name-status", "--no-renames", "-z", cwd=root).split("\0")
    entries = list(zip(out[0::2], out[1::2]))
    from . import dumps
    status = 0
    for flag, name in entries:
        if Path(name).suffix.lower() not in (".xlsx", ".xlsm"):
            continue
        x = root / name
        side = sidecar(x)
        rel = side.relative_to(root).as_posix()
        if side.is_symlink() or not side.resolve().is_relative_to(root.resolve()):
            print(f"cellprose: refusing to write {rel}: it is a symlink or leaves the repository", file=sys.stderr)
            status = 1
            continue
        if flag == "D":
            if _git("ls-files", "--", rel, cwd=root).strip():
                _git("rm", "-q", "--cached", "--", rel, cwd=root)
                side.unlink(missing_ok=True)
                print(f"cellprose: removed {rel}", file=sys.stderr)
            continue
        # encode what is staged, not the working copy, so the sidecar matches the commit
        data = subprocess.run(["git", "show", f":{name}"], cwd=root, check=True, capture_output=True).stdout
        fd, tmp = tempfile.mkstemp(prefix="cellprose-staged-", suffix=".xlsx")
        staged = Path(tmp)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        try:
            text = dumps(staged, recalc="never").replace(f"source: {staged.name}", f"source: {x.name}", 1)
        except Exception as e:  # unreadable workbook must not silently skip the sidecar
            print(f"cellprose: cannot encode {name}: {e}", file=sys.stderr)
            status = 1
            continue
        finally:
            staged.unlink(missing_ok=True)
        side.write_text(text, encoding="utf-8", newline="\n")
        _git("add", "--", rel, cwd=root)
        print(f"cellprose: updated {rel}", file=sys.stderr)
    return status


def setup(cwd: Path | None = None, hook: bool = True) -> list[str]:
    """Configure the current repository: diff driver, .gitattributes line and (optionally) the pre-commit hook."""
    root = Path(_git("rev-parse", "--show-toplevel", cwd=cwd).strip())
    done = []
    _git("config", f"diff.{DRIVER}.textconv", "cellprose textconv", cwd=root)
    _git("config", f"diff.{DRIVER}.binary", "true", cwd=root)
    done.append(f"git config diff.{DRIVER}.textconv")
    attrs = root / ".gitattributes"
    lines = attrs.read_text(encoding="utf-8").splitlines() if attrs.exists() else []
    if ATTRIBUTES_LINE not in lines:
        attrs.write_text("\n".join([*lines, ATTRIBUTES_LINE]) + "\n", encoding="utf-8")
        done.append(f".gitattributes: {ATTRIBUTES_LINE}")
    if hook:
        hooks = Path(_git("rev-parse", "--git-path", "hooks", cwd=root).strip())
        hooks = hooks if hooks.is_absolute() else root / hooks
        hooks.mkdir(parents=True, exist_ok=True)
        path = hooks / "pre-commit"
        existing = path.read_text(encoding="utf-8") if path.exists() else "#!/bin/sh\n"
        if HOOK_MARK not in existing:
            path.write_text(existing.rstrip("\n") + "\n" + HOOK_BODY, encoding="utf-8")
            path.chmod(path.stat().st_mode | 0o111)
            done.append(f"{path.relative_to(root) if path.is_relative_to(root) else path}")
    return done
