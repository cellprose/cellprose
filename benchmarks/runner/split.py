"""The dev / held-out split (benchmarks/split.json) and the guard that keeps held-out workbooks out of exploratory runs."""
import json
import random
from pathlib import Path

from .store import sha256_file

SPLIT_FILE = Path(__file__).resolve().parent.parent / "split.json"


class HeldOutError(SystemExit):
    """A held-out workbook was requested without --final."""


def load(path: Path = SPLIT_FILE) -> dict:
    return json.loads(Path(path).read_text())


def split_sha256(path: Path = SPLIT_FILE) -> str:
    return sha256_file(path)


# Development sets built after split.json was frozen (freeze/benchmark.json hashes it, so it is not edited) carry a
# reserved name prefix instead. Only external/devlarge.py (E33) makes `dev_` names; no held-out set uses the prefix.
DEV_PREFIXES = ("dev_",)


def role(workbook: str, split: dict | None = None) -> str:
    """'dev' for a workbook the split file lists or a `dev_` workbook; everything else is held out."""
    split = split or load()
    return "dev" if workbook in split["dev"] or workbook.startswith(DEV_PREFIXES) else "held_out"


def partition(workbooks, split: dict | None = None) -> tuple[list[str], list[str]]:
    split = split or load()
    dev = [w for w in workbooks if role(w, split) == "dev"]
    held = [w for w in workbooks if role(w, split) == "held_out"]
    return dev, held


def subset(held_out, n: int | None, seed: int) -> list[str]:
    """A seeded random subset of `n` held-out workbooks, in name order. The pool is sorted first so the draw does not
    depend on directory order."""
    pool = sorted(held_out)
    if n is None or n >= len(pool):
        return pool
    return sorted(random.Random(seed).sample(pool, n))


def check_requested(workbooks, final: bool, split: dict | None = None) -> None:
    """Refuse held-out workbooks unless `final`. Run before any call is planned or priced."""
    _, held = partition(workbooks, split)
    if held and not final:
        shown = ", ".join(held[:5]) + (f" and {len(held) - 5} more" if len(held) > 5 else "")
        raise HeldOutError(f"refusing held-out workbooks without --final: {shown}. Held-out data is for the final run only "
                           f"(docs/PROTOCOL.md section 3); a look at its results makes them exploratory.")


def select(requested: str | None, sample: list[str] | None, available, final: bool, n: int | None, seed: int | None,
           split: dict | None = None) -> list[str]:
    """The workbooks a run uses.

    Default: every development workbook in the corpus; with `final`, plus a seeded subset of `n` held-out workbooks
    (all of them when `n` is None). An explicit list or a sample is taken as given, then checked against the split.
    Raises SystemExit with a message when the request is refused."""
    split = split or load()
    seed = split["subset"]["seed"] if seed is None else seed
    if final and sample:
        raise SystemExit("--final cannot be combined with --sample")
    if requested:
        workbooks = requested.split(",")
    elif sample:
        workbooks = list(sample)
    else:
        dev, held = partition(available, split)
        workbooks = dev + (subset(held, n, seed) if final else [])
        if not workbooks:
            raise SystemExit("this corpus has no development workbooks; its held-out workbooks need --final")
    check_requested(workbooks, final, split)
    if n is not None and requested:
        dev, held = partition(workbooks, split)
        workbooks = dev + subset(held, n, seed)
    return workbooks


def require_clean_for_final(final: bool, dirty: bool | None, allow_dirty: bool) -> None:
    if final and dirty and not allow_dirty:
        raise SystemExit("refusing a --final run with uncommitted changes (commit them, or pass --allow-dirty and "
                         "say so in the write-up)")
