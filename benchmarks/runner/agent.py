"""Agent mode through the APIs: the workbook is a file in an empty folder and the model explores it with two tools
(`bash` and `read_file`) until it answers, as `run_agent.py` did through the Claude CLI.

Per call this module
  - pins the model and its reasoning settings exactly as the one-shot runner does. Anthropic turns use automatic
    prompt caching (top-level cache_control, 5-minute TTL) unless cache=False, in which case any cache activity is an
    error; OpenAI caches automatically. Either way the cost metric prices every token uncached, and the billed amount
    is recorded beside it (`billed_usd`);
  - records the tokens of every turn, so the cost of re-reading a growing context is visible, and sums them;
  - stops after `max_turns` turns or `max_call_usd` of list-price spend, and records that as a failure (scored 0).

Provider backends keep their own message history; the loop below is the same for both.
SECURITY: the `bash` tool runs the model's commands on this machine, in a temporary folder with a minimal
environment (no API keys, HOME set to the folder) and a timeout. That limits accidents, not a hostile model:
run agent mode inside a container or VM.
"""
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .cost import billed_cost, call_cost
from .types import (ApiFailure, BudgetExceeded, CacheLeak, CallError, CallResult, ModelCfg, Refused, Truncated,
                    TurnLimit, Usage)

MAX_TURNS = 40              # the CLI runs used --max-turns 40
MAX_CALL_USD = 1.0
TOOL_TIMEOUT_S = 60
MAX_TOOL_OUTPUT = 20_000    # characters returned to the model per tool call

TOOLS = [
    {"name": "bash", "description": "Run a shell command in the workbook folder (python3 with openpyxl is installed). "
                                    "Returns stdout and stderr.",
     "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read a text file from the workbook folder.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
]
# A purpose-built viewer, as SpreadsheetBench 2's agents get (`view_xlsx`: sheet structure, formulas and values). It is
# offered only to the `agent_xlsx_viewer` variant, so a win over the plain-shell agent cannot be put down to clumsy tools.
VIEW_XLSX = {"name": "view_xlsx",
             "description": "Show ./book.xlsx. With no sheet: every sheet with its used range. With a sheet: each "
                            "non-empty cell in the range (default the used range) as `A1 = value`, or "
                            "`A1 = =FORMULA -> cached value` for a formula.",
             "parameters": {"type": "object", "properties": {"sheet": {"type": "string"},
                                                             "range": {"type": "string", "description": "e.g. A1:F40"}}}}
VIEWER_TOOLS = TOOLS + [VIEW_XLSX]
# The Cellprose tool kit (src/cellprose/tools.py, experiments/E33): map the workbook, then read only what a question needs.
# Offered only to `agent_xlsx_cellprose`; the file, prompt and limits are those of agent_xlsx.
_S = {"type": "string"}
CELLPROSE_TOOLS = TOOLS + [
    {"name": "outline", "description": "Start here. The workbook ./book.xlsx as Cellprose text: an index of sheets and long "
                                       "regions, then every region as a table (row number, then cells by column letter) "
                                       "with its formulas as fill ranges (`B4:E4 = B2*B3`). Regions longer than 6 rows show "
                                       "only their first and last rows; read the rest with read_range.",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "read_range", "description": "Cells of one A1 range as Cellprose text (values, formulas, formats), e.g. "
                                          "`Sheet1!A1:F40`.",
     "parameters": {"type": "object", "properties": {"range": _S}, "required": ["range"]}},
    {"name": "find", "description": "Cells whose text contains the words (case-insensitive), each with up to 6 non-empty "
                                    "cells to its right. Use it to find a row label or a column header.",
     "parameters": {"type": "object", "properties": {"text": _S, "sheet": _S}, "required": ["text"]}},
    {"name": "trace", "description": "For a cell like `Sheet1!E12`: its formula and the cells it reads directly, or with "
                                     "dependents=true the formula cells that read it (transitive=true: every cell whose "
                                     "value depends on it).",
     "parameters": {"type": "object", "properties": {"cell": _S, "dependents": {"type": "boolean"},
                                                     "transitive": {"type": "boolean"}}, "required": ["cell"]}},
]


def view_xlsx(path: Path, sheet: str | None = None, cells: str | None = None) -> str:
    """The text the `view_xlsx` tool returns: formulas next to their cached values, row by row."""
    import openpyxl
    f = openpyxl.load_workbook(path, data_only=False)
    if not sheet:
        return "\n".join(f"{ws.title}: {ws.dimensions}" for ws in f.worksheets)
    if sheet not in f.sheetnames:
        return f"error: no sheet {sheet!r}; sheets are {f.sheetnames}"
    v = openpyxl.load_workbook(path, data_only=True)
    fs, vs = f[sheet], v[sheet]
    out = []
    for row in fs[cells or fs.dimensions]:
        for c in (row if isinstance(row, tuple) else (row,)):
            if c.value is None:
                continue
            if isinstance(c.value, str) and c.value.startswith("="):
                out.append(f"{c.coordinate} = {c.value} -> {vs[c.coordinate].value!r}")
            else:
                out.append(f"{c.coordinate} = {c.value!r}")
    return "\n".join(out) or "(no non-empty cells)"


def lean_tool(path: Path, name: str, args: dict) -> str:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from cellprose import tools
    if name == "read_range":
        refs = args.get("ranges") or ([args["range"]] if args.get("range") else [])
        return tools.read_ranges(path, [str(r) for r in refs][:20]) if refs else "error: give ranges"
    if name == "find":
        return tools.find(path, str(args["text"]), args.get("sheet"))
    if name == "whatif":
        return tools.whatif(path, str(args["cell"]), args.get("value"), args.get("factor"))
    return tools.trace(path, str(args["cell"]), bool(args.get("dependents")), bool(args.get("transitive")), compact=True)


def cellprose_tool(path: Path, name: str, args: dict, index_outline: bool = False) -> str:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from cellprose import tools
    if name == "outline":
        return tools.index(path) if index_outline else tools.outline(path)
    if name == "read_range":
        return tools.read_range(path, str(args["range"]))
    if name == "find":
        return tools.find(path, str(args["text"]), args.get("sheet"))
    return tools.trace(path, str(args["cell"]), bool(args.get("dependents")), bool(args.get("transitive")))


# E33 follow-up: the same kit with `outline` cut to an index of regions (about 1k tokens instead of about 10k), since
# every later turn re-reads it with caching off. Offered only to `agent_xlsx_cellprose_idx`.
CELLPROSE_IDX_TOOLS = [t for t in CELLPROSE_TOOLS if t["name"] != "outline"] + [
    {"name": "outline", "description": "Start here. An index of ./book.xlsx: each sheet's used range, then every region "
                                       "(a rectangle of non-empty cells) with its size, formula count and first row. "
                                       "It shows no other cell values; read them with read_range (row number, then cells "
                                       "by column letter, with formulas as fill ranges `B4:E4 = B2*B3`).",
     "parameters": {"type": "object", "properties": {}}}]


# E34: the lean kit. The index arrives with the questions (no outline turn), read_range takes several ranges and drops
# formats blocks, trace returns addresses merged into ranges, and there is no bash or read_file: Cellprose tools only.
LEAN_TOOLS = [
    {"name": "read_range", "description": "Cells of one or more A1 ranges as Cellprose text: a table per range (row "
                                          "number, then cells by column letter) and its formulas as fill ranges "
                                          "(`B4:E4 = B2*B3`). Ask for several ranges in one call.",
     "parameters": {"type": "object", "properties": {"ranges": {"type": "array", "items": _S,
                                                                "description": "e.g. [\"Sheet1!A1:F40\", \"Sheet2!B5\"]"}},
                    "required": ["ranges"]}},
    {"name": "find", "description": "Cells whose text contains the words (case-insensitive), each with up to 6 non-empty "
                                    "cells to its right. Use it to find a row label or a column header.",
     "parameters": {"type": "object", "properties": {"text": _S, "sheet": _S}, "required": ["text"]}},
    {"name": "trace", "description": "For a cell like `Sheet1!E12`: its formula and the addresses it reads directly, or "
                                     "with dependents=true the cells that read it (transitive=true: every cell whose "
                                     "value depends on it), as ranges.",
     "parameters": {"type": "object", "properties": {"cell": _S, "dependents": {"type": "boolean"},
                                                     "transitive": {"type": "boolean"}}, "required": ["cell"]}},
    {"name": "whatif", "description": "Change one input cell (set `value`, or multiply it by `factor`), recalculate the "
                                      "workbook, and list every other cell whose value changes, as ranges. The file "
                                      "is not changed. Use it for what-if questions.",
     "parameters": {"type": "object", "properties": {"cell": _S, "value": {}, "factor": {"type": "number"}},
                    "required": ["cell"]}},
]


class Sandbox:
    """A temporary folder holding the workbook file, and the two tools that operate on it."""

    def __init__(self, files: dict[str, Path], index_outline: bool = False, lean: bool = False):
        self.index_outline, self.lean = index_outline, lean
        self.dir = Path(tempfile.mkdtemp(prefix="sheetmark_agent_"))
        for name, src in files.items():
            shutil.copy(src, self.dir / name)

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def _clip(self, text: str) -> str:
        return text if len(text) <= MAX_TOOL_OUTPUT else text[:MAX_TOOL_OUTPUT] + f"\n[output cut at {MAX_TOOL_OUTPUT} characters]"

    def call(self, name: str, args: dict) -> str:
        try:
            if name == "bash":
                env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(self.dir), "LANG": "C.UTF-8"}
                r = subprocess.run(["bash", "-c", str(args["command"])], cwd=self.dir, env=env, capture_output=True,
                                   text=True, timeout=TOOL_TIMEOUT_S, errors="replace")
                return self._clip(r.stdout + r.stderr) or "(no output)"
            if name == "read_file":
                path = (self.dir / str(args["path"])).resolve()
                if self.dir.resolve() not in path.parents and path != self.dir.resolve():
                    return "error: path is outside the workbook folder"
                return self._clip(path.read_text(errors="replace"))
            if name == "view_xlsx":
                return self._clip(view_xlsx(self.dir / "book.xlsx", args.get("sheet"), args.get("range")))
            if self.lean and name in ("read_range", "find", "trace", "whatif"):
                return self._clip(lean_tool(self.dir / "book.xlsx", name, args))
            if name in ("outline", "read_range", "find", "trace"):
                return self._clip(cellprose_tool(self.dir / "book.xlsx", name, args, self.index_outline))
            return f"error: unknown tool {name!r}"
        except subprocess.TimeoutExpired:
            return f"error: command timed out after {TOOL_TIMEOUT_S} s"
        except Exception as e:
            return f"error: {type(e).__name__}: {e}"


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class Turn:
    text: str
    tool_calls: list[ToolCall]
    result: CallResult          # this turn's usage, model and request id


@dataclass
class AgentRun:
    result: CallResult          # final text, usage summed over turns
    turns: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)


def _dump(item):
    return item.model_dump(exclude_none=True) if hasattr(item, "model_dump") else dict(vars(item))


class AnthropicAgent:
    """Messages API with tools. Thinking blocks are passed back untouched, as the API requires."""
    name = "anthropic"

    def __init__(self, provider, cache: bool = True):
        self.provider = provider
        self.cache = cache

    def start(self, cfg: ModelCfg, system: str, user: str, tools=TOOLS) -> dict:
        return {"cfg": cfg, "system": system, "messages": [{"role": "user", "content": user}], "tools": tools}

    def step(self, st: dict) -> Turn:
        from .providers import AnthropicProvider
        cfg = st["cfg"]
        kw = AnthropicProvider.request(cfg, st["system"], "")
        kw["messages"] = st["messages"]
        kw["tools"] = [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in st.get("tools", TOOLS)]
        if self.cache:      # automatic caching: the breakpoint follows the growing conversation; 5-minute TTL
            kw["cache_control"] = {"type": "ephemeral"}
        with self.provider.client.messages.stream(**kw) as stream:
            msg = stream.get_final_message()
        res = AnthropicProvider.to_result(msg)
        if not self.cache and (res.usage.cache_read_tokens or res.usage.cache_write_tokens):
            raise CacheLeak(f"cache activity with caching off: read={res.usage.cache_read_tokens} "
                            f"write={res.usage.cache_write_tokens}", res)
        if msg.stop_reason == "max_tokens":
            raise Truncated(f"hit max_tokens={cfg.max_tokens} in one turn", res)
        if msg.stop_reason == "refusal":
            raise Refused("model refused the request", res)
        st["messages"].append({"role": "assistant", "content": msg.content})
        calls = [ToolCall(b.id, b.name, dict(b.input)) for b in msg.content if b.type == "tool_use"]
        return Turn(res.text, calls, res)

    def add_results(self, st: dict, results: list[tuple[ToolCall, str]]) -> None:
        st["messages"].append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": c.id, "content": out} for c, out in results]})


class OpenAIAgent:
    """Responses API with function tools. The history is resent each turn (store=False), with encrypted reasoning items
    so the model keeps its reasoning between tool calls. Not exercised against the live API yet."""
    name = "openai"

    def __init__(self, provider):
        self.provider = provider

    def start(self, cfg: ModelCfg, system: str, user: str, tools=TOOLS) -> dict:
        return {"cfg": cfg, "system": system, "input": [{"role": "user", "content": user}], "tools": tools}

    def step(self, st: dict) -> Turn:
        from .providers import OpenAIProvider
        cfg = st["cfg"]
        kw = OpenAIProvider.request(cfg, st["system"], "")
        kw["input"] = st["input"]
        kw["tools"] = [{"type": "function", **t} for t in st.get("tools", TOOLS)]
        kw["include"] = ["reasoning.encrypted_content"]
        r = self.provider.client.responses.create(**kw)
        u = r.usage
        cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
        usage = Usage(input_tokens=(u.input_tokens or 0) - cached, output_tokens=u.output_tokens or 0,
                      reasoning_tokens=getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None),
                      cache_read_tokens=cached)
        res = OpenAIProvider.to_result(r, usage, "", "")
        if getattr(r, "status", "completed") == "incomplete":
            raise Truncated(f"response incomplete at max_output_tokens={cfg.max_tokens} in one turn", res)
        for item in r.output:
            for part in getattr(item, "content", None) or []:
                if getattr(part, "type", None) == "refusal":
                    raise Refused("model refused the request", res)
        st["input"] += [_dump(i) for i in r.output]
        calls = [ToolCall(i.call_id, i.name, json.loads(i.arguments or "{}"))
                 for i in r.output if getattr(i, "type", None) == "function_call"]
        return Turn(getattr(r, "output_text", "") or "", calls, res)

    def add_results(self, st: dict, results: list[tuple[ToolCall, str]]) -> None:
        st["input"] += [{"type": "function_call_output", "call_id": c.id, "output": out} for c, out in results]


def get_agent(cfg: ModelCfg, provider, cache: bool = True):
    if cfg.provider == "anthropic":
        return AnthropicAgent(provider, cache)
    if cfg.provider == "openai":
        return OpenAIAgent(provider)
    raise ValueError(f"agent mode is implemented for anthropic and openai, not {cfg.provider!r}")


def _sum(a: Usage, b: Usage) -> Usage:
    r = None if a.reasoning_tokens is None and b.reasoning_tokens is None else (a.reasoning_tokens or 0) + (b.reasoning_tokens or 0)
    return Usage(a.input_tokens + b.input_tokens, a.output_tokens + b.output_tokens, r,
                 a.cache_read_tokens + b.cache_read_tokens, a.cache_write_tokens + b.cache_write_tokens)


def run_agent(cfg: ModelCfg, backend, system: str, user: str, sandbox: Sandbox, max_turns: int = MAX_TURNS,
              max_call_usd: float = MAX_CALL_USD, tools=TOOLS) -> AgentRun:
    """Run the tool loop. Returns the final answer with usage summed over turns, or raises a CallError that carries the
    tokens spent so far (the runner records it as a failure scored 0)."""
    st = backend.start(cfg, system, user, tools)
    total, turns, trace = Usage(), [], []
    spent = 0.0         # list-price cost so far; each request is priced on its own prompt length
    billed = 0.0        # the same, as billed (cache writes and reads at their own prices)
    last: CallResult | None = None

    def so_far(text="", stop=None) -> CallResult:
        return CallResult(text=text, model_returned=last.model_returned if last else cfg.model_id,
                          request_id=last.request_id if last else None, usage=total, stop_reason=stop,
                          raw_usage={"turns": turns, "billed_usd": round(billed, 6)}, cost=spent)

    for n in range(1, max_turns + 1):
        if spent >= max_call_usd:
            raise BudgetExceeded(f"call reached its ${max_call_usd:.2f} cap after {n - 1} turns", so_far("", "budget"))
        try:
            turn = backend.step(st)
        except CallError as e:       # the failed turn's own tokens count too
            if e.result is not None:
                total = _sum(total, e.result.usage)
                spent += call_cost(cfg, e.result.usage)
                billed += billed_cost(cfg, e.result.usage)
                turns.append({"turn": n, **_turn_usage(e.result.usage), "failed": e.kind})
            e.result = so_far("", e.kind)
            raise
        except Exception as e:
            from .store import recordable
            if recordable(e):
                raise ApiFailure(f"{type(e).__name__}: {e}", so_far("", "api_error")) from e
            raise
        last = turn.result
        total = _sum(total, turn.result.usage)
        spent += call_cost(cfg, turn.result.usage)
        billed += billed_cost(cfg, turn.result.usage)
        turns.append({"turn": n, **_turn_usage(turn.result.usage), "tool_calls": [c.name for c in turn.tool_calls],
                      "stop_reason": turn.result.stop_reason})
        if not turn.tool_calls:
            return AgentRun(so_far(turn.text, turn.result.stop_reason), turns, trace)
        results = []
        for c in turn.tool_calls:
            out = sandbox.call(c.name, c.args)
            results.append((c, out))
            trace.append({"turn": n, "tool": c.name, "args": json.dumps(c.args)[:500], "output_chars": len(out)})
        backend.add_results(st, results)
    raise TurnLimit(f"no final answer after {max_turns} turns", so_far("", "turn_limit"))


def _turn_usage(u: Usage) -> dict:
    return {"input_tokens": u.input_tokens, "cache_read_tokens": u.cache_read_tokens,
            "cache_write_tokens": u.cache_write_tokens, "output_tokens": u.output_tokens,
            "reasoning_tokens": u.reasoning_tokens}
