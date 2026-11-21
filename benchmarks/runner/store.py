"""Build and write the raw result JSON. The top-level keys match what run.py wrote, so score.py and
analyze.py read these files unchanged; `run` and `provider` are additive."""
import hashlib
import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from .cost import call_cost
from .types import CallError, CallResult, InfraFailure, ModelCfg, Usage


def git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=Path(__file__).parent, timeout=10).stdout.strip() or None
    except Exception:
        return None


def git_dirty(paths=(".", ":(exclude)results")) -> bool | None:
    """True when the benchmark tree has uncommitted changes (results/ is excluded: a run writes there), None when
    git cannot say. A final run records this so a result can be tied to a commit."""
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", *paths], capture_output=True, text=True,
                           cwd=Path(__file__).parent.parent, timeout=30, check=True)
        return bool(r.stdout.strip())
    except Exception:
        return None


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recordable(exc: BaseException) -> bool:
    """True for a failure that belongs to the call (a CallError, or an error raised by a provider SDK or its HTTP layer)
    and so is recorded and scored 0. A bug in the runner (TypeError, KeyError...) is not recordable: writing it down as
    a model failure would turn a code defect into zeros."""
    return isinstance(exc, CallError) or type(exc).__module__.split(".")[0] in {"anthropic", "openai", "httpx", "httpcore"}


INFRA_STATUS = {401, 402, 403, 408, 409, 429}      # plus every 5xx (529 is Anthropic's "overloaded")
INFRA_TEXT = ("credit balance", "billing", "insufficient_quota", "spend limit")


def infrastructure(exc: BaseException) -> bool:
    """True for a failure that says nothing about the model: no credit, a bad key, a rate limit, an overload, a server
    error or a network failure that outlasted the SDK's retries. Such a call is not recorded, so it stays to do and a
    resume makes it (docs/PROTOCOL.md section 5). Everything else recordable (truncated, refused, turn limit, per-call
    cap, a request the API rejects as invalid) is the call's own result and is scored 0."""
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        names = {c.__name__ for c in type(exc).__mro__}
        if names & {"APIConnectionError", "APITimeoutError"} or type(exc).__module__.split(".")[0] in {"httpx", "httpcore"}:
            return True
        status = getattr(exc, "status_code", None)
        if isinstance(status, int) and (status in INFRA_STATUS or status >= 500):
            return True
        if isinstance(status, int) and any(t in str(exc).lower() for t in INFRA_TEXT):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


_LOG_LOCK = threading.Lock()


def infra_failure(out: Path, meta: dict, cfg: ModelCfg, wb: str, enc: str, rep: int, data: dict) -> "InfraFailure":
    """Log an infrastructure failure to <out>/runs/<run id>.infra.jsonl (with what the attempt spent) and return the
    InfraFailure to raise. `data` is the failure record build_failure made; it is not written as a raw file."""
    f = data["failure"]
    line = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model": cfg.alias, "workbook": wb,
            "arm": enc, "rep": rep, "type": f["type"], "message": f["message"][:300], "cost": data["cost"]}
    path = out / "runs" / f"{meta['run_id']}.infra.jsonl"
    with _LOG_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(json.dumps(line) + "\n")
    return InfraFailure(f"{f['type']}: {f['message'][:300]}", cost=data["cost"])


def raw_path(root: Path, cfg: ModelCfg, wb: str, enc: str, rep: int) -> Path:
    return root / "raw" / cfg.alias / (f"{wb}.{enc}.json" if rep == 0 else f"{wb}.{enc}.r{rep}.json")


def build_raw(cfg: ModelCfg, wb: str, enc: str, user: str, res: CallResult, run: dict) -> dict:
    u = res.usage
    return {
        "model": cfg.alias, "workbook": wb, "encoding": enc, "prompt_chars": len(user),
        "prompt_sha256": sha256_text(user),
        "result": res.text,
        "usage": {"input_tokens": u.input_tokens, "cache_creation_input_tokens": u.cache_write_tokens,
                  "cache_read_input_tokens": u.cache_read_tokens, "output_tokens": u.output_tokens,
                  "output_tokens_details": {"thinking_tokens": u.reasoning_tokens}},
        "modelUsage": {res.model_returned: {
            "inputTokens": u.input_tokens, "outputTokens": u.output_tokens,
            "cacheReadInputTokens": u.cache_read_tokens, "cacheCreationInputTokens": u.cache_write_tokens,
            "thinkingTokens": u.reasoning_tokens}},
        "cost": res.cost if res.cost is not None else call_cost(cfg, u),     # uncached list price, not the billed amount
        "provider": cfg.provider,
        "run": {**run, "requested_model": cfg.model_id, "returned_model": res.model_returned,
                "request_id": res.request_id, "stop_reason": res.stop_reason, "settings": cfg.settings(),
                "price_in_per_mtok": cfg.price_in, "price_out_per_mtok": cfg.price_out,
                "long_prompt_tier": cfg.tier_record(),
                "provider_usage": res.raw_usage,
                "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
    }


def build_failure(cfg: ModelCfg, wb: str, enc: str, user: str, exc: BaseException, run: dict) -> dict:
    """The raw file of a call that gave no usable answer. It has the shape of a normal one, with an empty `result`
    (so score.py scores every question 0) and whatever tokens the provider reported, so it still costs what it cost.
    Errors before any response (network, auth) have no tokens and cost nothing."""
    res = exc.result if isinstance(exc, CallError) and exc.result is not None else None
    if res is None:
        res = CallResult(text="", model_returned=cfg.model_id, request_id=None, usage=Usage(), stop_reason=None)
    d = build_raw(cfg, wb, enc, user, res, run)
    d["result"] = ""
    d["failed"] = True
    d["failure"] = {"kind": getattr(exc, "kind", "error"), "type": type(exc).__name__, "message": str(exc)[:500],
                    "partial_text_chars": len(res.text)}
    return d


def write_raw(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1))
    tmp.replace(path)
