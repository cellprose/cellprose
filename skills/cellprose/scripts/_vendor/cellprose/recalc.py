"""Recalculate a workbook's formulas with headless LibreOffice, so cached values exist."""
from __future__ import annotations

import os
import shutil
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


def recalc_copy(path: str | Path, timeout: int = 300) -> Path:
    """Return the path of a recalculated copy in a temp folder. Raises RuntimeError if LibreOffice is missing."""
    exe = soffice()
    if not exe:
        raise RuntimeError("LibreOffice (soffice) not found; install it to compute formula values")
    path = Path(path)
    out = Path(tempfile.mkdtemp(prefix="cellprose-"))
    profile = out / "profile"  # private profile: works even while the user has LibreOffice open
    try:
        subprocess.run([exe, f"-env:UserInstallation={profile.as_uri()}", "--headless", "--calc",
                        "--convert-to", "xlsx", "--outdir", str(out), str(path)],
                       check=True, capture_output=True, timeout=timeout)
        result = out / (path.stem + ".xlsx")
        if not result.exists():
            raise RuntimeError(f"LibreOffice did not produce {result.name}")
    except BaseException:
        shutil.rmtree(out, ignore_errors=True)
        raise
    shutil.rmtree(profile, ignore_errors=True)      # the converted copy stays; the callers' temp dirs are small
    return result
