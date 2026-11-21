"""Run metadata shared by every runner: git state, input checksums and the per-run manifest."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import split as splitmod
from .store import git_dirty, git_sha, sha256_file, sha256_text


def input_checksums(corpus: Path, workbooks, encs, agent_files: bool = False) -> dict:
    """SHA-256 of every question file and encoded file a run can send (plus the .xlsx for agent mode), keyed by path
    relative to the corpus. `digest` covers all of them, so one value ties a result to its exact inputs."""
    files = {}
    for wb in sorted(workbooks):
        files[f"questions/{wb}.json"] = sha256_file(corpus / "questions" / f"{wb}.json")
        for enc in sorted(encs):
            if enc == "none" or enc.startswith("agent_"):
                continue
            files[f"encoded/{wb}.{enc}.txt"] = sha256_file(corpus / "encoded" / f"{wb}.{enc}.txt")
        if agent_files:
            files[f"workbooks/{wb}.xlsx"] = sha256_file(corpus / "workbooks" / f"{wb}.xlsx")
    digest = sha256_text("\n".join(f"{k} {v}" for k, v in sorted(files.items())))
    return {"digest": digest, "files": files}


def make_meta(corpus: Path, root: Path, final: bool, checksums: dict, extra: dict | None = None) -> dict:
    """The `run` block stored in every raw file of one invocation. Per-file checksums live in the manifest, not here."""
    now = datetime.now(timezone.utc)
    return {"run_id": now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6],
            "started_at": now.isoformat(timespec="seconds"), "git_sha": git_sha(), "git_dirty": git_dirty(),
            "corpus": str(corpus.relative_to(root)) if corpus.is_relative_to(root) else str(corpus),
            "inputs_sha256": checksums["digest"], "split_sha256": splitmod.split_sha256(), "final": final,
            **(extra or {})}


RESUME_HOURS = 48      # a run and all its resumes finish within this window of its start (docs/PROTOCOL.md section 5)


def resume_meta(out: Path, run_id: str, checksums: dict, invocation: dict) -> dict:
    """The `run` block of an earlier invocation, to continue it under the same run id. Refuses when the code, the
    settings or the inputs changed, or when the run started more than RESUME_HOURS ago; logs the resume in the run's manifest."""
    path = out / "runs" / f"{run_id}.json"
    if not path.exists():
        raise SystemExit(f"no manifest {path}; --resume needs the run id of an earlier invocation in this --out")
    man = json.loads(path.read_text())
    meta = man["run"]
    if meta["git_sha"] != git_sha() or git_dirty() != meta["git_dirty"]:
        raise SystemExit(f"run {run_id} was made at commit {meta['git_sha'][:12]}; the code changed, so it cannot resume")
    same = {k: v for k, v in invocation.items() if k != "argv"}
    was = {k: v for k, v in man["invocation"].items() if k != "argv"}
    if same != was:
        diff = sorted(k for k in same.keys() | was.keys() if same.get(k) != was.get(k))
        raise SystemExit(f"run {run_id} was invoked with other settings ({', '.join(diff)}); resume with the same command")
    if checksums["digest"] != meta["inputs_sha256"]:
        raise SystemExit(f"run {run_id}: the inputs changed since it started, so it cannot resume")
    started = datetime.fromisoformat(meta["started_at"])
    hours = (datetime.now(timezone.utc) - started).total_seconds() / 3600
    if hours > RESUME_HOURS:
        raise SystemExit(f"run {run_id} started {hours:.0f} h ago, past the {RESUME_HOURS} h window; start a new run")
    man.setdefault("resumes", []).append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **invocation})
    path.write_text(json.dumps(man, indent=1) + "\n")
    return meta


def write_manifest(out: Path, meta: dict, checksums: dict, invocation: dict) -> Path:
    """<out>/runs/<run_id>.json: the run block, every input checksum and how the run was invoked. It is small and is
    committed with the run id (SpreadsheetBench-derived inputs themselves are not)."""
    path = out / "runs" / f"{meta['run_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"run": meta, "invocation": invocation, "inputs": checksums}, indent=1) + "\n")
    return path


def check_prices_date(final: bool, value: str | None) -> str | None:
    """--prices-checked: the day the owner checked runner/models.py against the vendors' pricing pages (docs/PROTOCOL.md
    section 4). Required for a final run; returns an error message, or None when fine."""
    if value is None:
        return "a --final run needs --prices-checked YYYY-MM-DD (the day the list prices were checked)" if final else None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return f"--prices-checked {value!r}: expected YYYY-MM-DD"
    return None
