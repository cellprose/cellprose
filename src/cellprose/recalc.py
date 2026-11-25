"""Recalculate a workbook's formulas with headless LibreOffice, so cached values exist."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path


def soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        p = shutil.which(name)
        if p:
            return p
    mac = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    return mac if os.path.exists(mac) else None


def _run(cmd: list[str], timeout: int) -> None:
    """subprocess.run, but a timeout also kills what `soffice` launched (soffice.bin), not just the launcher."""
    posix = os.name == "posix"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=posix)
    try:
        proc.communicate(timeout=timeout)
    except BaseException:
        if posix:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            proc.kill()
        proc.wait()
        raise
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def discard(copy: str | Path) -> None:
    """Delete a copy made by recalc_copy, with the temp folder it lives in."""
    shutil.rmtree(Path(copy).parent, ignore_errors=True)


def recalc_copy(path: str | Path, timeout: int = 300) -> Path:
    """Return the path of a recalculated copy in a temp folder. Raises RuntimeError if LibreOffice is missing."""
    exe = soffice()
    if not exe:
        raise RuntimeError("LibreOffice (soffice) not found; install it to compute formula values")
    path = Path(path).resolve()         # absolute, so a file name starting with "-" is not read as an option
    out = Path(tempfile.mkdtemp(prefix="cellprose-"))
    profile = out / "profile"  # private profile: works even while the user has LibreOffice open
    try:
        _run([exe, f"-env:UserInstallation={profile.as_uri()}", "--headless", "--calc",
              "--convert-to", "xlsx", "--outdir", str(out), str(path)], timeout)
        result = out / (path.stem + ".xlsx")
        if not result.exists():
            raise RuntimeError(f"LibreOffice did not produce {result.name}")
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    shutil.rmtree(profile, ignore_errors=True)      # the converted copy stays; the callers' temp dirs are small
    return result
