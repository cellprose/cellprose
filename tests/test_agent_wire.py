"""Agent-mode runner against the real Anthropic and OpenAI SDKs, with the network replaced by httpx's MockTransport.

The other agent tests use hand-made fake clients, which can drift from what the SDKs send and parse. Here the real
clients serialise the request, the mock returns wire-format responses (server-sent events for Anthropic, JSON for
OpenAI), and the SDK parses them, so the request body, the tool loop, the usage mapping and the history resend are
checked as the vendors would see them. No network, no key, no spend."""
import json
import sys
from pathlib import Path

import pytest

anthropic = pytest.importorskip("anthropic")
openai = pytest.importorskip("openai")
try:                      # the SDKs name their HTTP client after the package they depend on
    import httpx2 as httpx
except ImportError:
    httpx = pytest.importorskip("httpx")

BENCH = Path(__file__).resolve().parent.parent / "benchmarks"
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(Path(__file__).parent))
from runner import agent as agentmod, models  # noqa: E402
from runner.prompts import AGENT_SYSTEM  # noqa: E402
from runner.providers import AnthropicProvider, OpenAIProvider  # noqa: E402


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def anthropic_stream(blocks, stop, inp, out, model="claude-haiku-5-5"):
    """blocks: ("thinking", text) | ("text", text) | ("tool_use", id, name, input)."""
    ev = [sse("message_start", {"type": "message_start", "message": {
        "id": "msg_1", "type": "message", "role": "assistant", "model": model, "content": [], "stop_reason": None,
        "stop_sequence": None, "usage": {"input_tokens": inp, "output_tokens": 1}}})]
    for i, b in enumerate(blocks):
        if b[0] == "thinking":
            start, delta = ({"type": "thinking", "thinking": ""},
                            [{"type": "thinking_delta", "thinking": b[1]}, {"type": "signature_delta", "signature": "sig"}])
        elif b[0] == "text":
            start, delta = {"type": "text", "text": ""}, [{"type": "text_delta", "text": b[1]}]
        else:
            start = {"type": "tool_use", "id": b[1], "name": b[2], "input": {}}
            delta = [{"type": "input_json_delta", "partial_json": json.dumps(b[3])}]
        ev.append(sse("content_block_start", {"type": "content_block_start", "index": i, "content_block": start}))
        for d in delta:
            ev.append(sse("content_block_delta", {"type": "content_block_delta", "index": i, "delta": d}))
        ev.append(sse("content_block_stop", {"type": "content_block_stop", "index": i}))
    ev.append(sse("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None},
                                    "usage": {"output_tokens": out}}))
    ev.append(sse("message_stop", {"type": "message_stop"}))
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content="".join(ev).encode())


def openai_response(items, inp, out, reasoning=0, cached=0, status="completed", model="gpt-6-luna"):
    text = "".join(c["text"] for it in items if it["type"] == "message" for c in it["content"] if c["type"] == "output_text")
    return httpx.Response(200, json={
        "id": "resp_1", "object": "response", "created_at": 1, "model": model, "status": status, "output": items,
        "parallel_tool_calls": True, "tool_choice": "auto", "tools": [],
        "usage": {"input_tokens": inp, "output_tokens": out, "total_tokens": inp + out,
                  "input_tokens_details": {"cached_tokens": cached},
                  "output_tokens_details": {"reasoning_tokens": reasoning}}})


def msg_item(text):
    return {"type": "message", "id": "msg_x", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": text, "annotations": []}]}


def call_item(call_id, name, args):
    return {"type": "function_call", "id": "fc_" + call_id, "call_id": call_id, "name": name,
            "arguments": json.dumps(args), "status": "completed"}


def reasoning_item():
    return {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "enc"}


def scripted(responses):
    """(handler, requests): the handler returns the scripted responses in order and records each request body."""
    seen, queue = [], list(responses)

    def handler(request):
        seen.append({"path": request.url.path, "body": json.loads(request.content), "headers": dict(request.headers)})
        return queue.pop(0)
    return httpx.MockTransport(handler), seen


def run(cfg, backend):
    with agentmod.Sandbox({"book.xlsx": BENCH / "workbooks" / "03_pnl_quarterly.xlsx"}) as sb:
        return agentmod.run_agent(cfg, backend, AGENT_SYSTEM, "How many sheets?", sb)


def test_anthropic_wire_requests_and_parsing():
    cfg = models.get("haiku55")
    transport, seen = scripted([
        anthropic_stream([("thinking", "look"), ("tool_use", "toolu_1", "bash", {"command": "ls"})], "tool_use", 1000, 120),
        anthropic_stream([("thinking", "done"), ("text", '{"q1": 3}')], "end_turn", 1400, 80)])
    client = anthropic.Anthropic(api_key="sk-test", base_url="https://api.anthropic.com", max_retries=0,
                                 http_client=httpx.Client(transport=transport))
    r = run(cfg, agentmod.get_agent(cfg, AnthropicProvider(client)))
    assert r.result.text == '{"q1": 3}'
    assert [t["input_tokens"] for t in r.turns] == [1000, 1400] and r.result.usage.output_tokens == 200
    first, second = (s["body"] for s in seen)
    assert seen[0]["path"] == "/v1/messages" and first["stream"] is True
    assert first["model"] == "claude-haiku-5-5" and first["thinking"] == {"type": "adaptive"}
    assert first["output_config"] == {"effort": "medium"} and first["system"] == AGENT_SYSTEM
    assert {t["name"] for t in first["tools"]} == {"bash", "read_file"}
    assert all("input_schema" in t for t in first["tools"])
    assert first["cache_control"] == {"type": "ephemeral"} and second["cache_control"] == {"type": "ephemeral"}
    # turn 2 resends the assistant turn (thinking block with its signature, then the tool_use) and the tool result
    roles = [m["role"] for m in second["messages"]]
    assert roles == ["user", "assistant", "user"]
    kinds = [b["type"] for b in second["messages"][1]["content"]]
    assert kinds == ["thinking", "tool_use"] and second["messages"][1]["content"][0]["signature"] == "sig"
    result = second["messages"][2]["content"][0]
    assert result["type"] == "tool_result" and result["tool_use_id"] == "toolu_1" and "book.xlsx" in result["content"]


def test_anthropic_wire_cache_activity_is_an_error():
    cfg = models.get("haiku55")
    leak = anthropic_stream([("text", "x")], "end_turn", 10, 5)
    leak = httpx.Response(200, headers=leak.headers, content=leak.content.replace(
        b'"input_tokens": 10', b'"input_tokens": 10, "cache_read_input_tokens": 7'))
    transport, _ = scripted([leak])
    client = anthropic.Anthropic(api_key="sk-test", max_retries=0, http_client=httpx.Client(transport=transport))
    from runner.types import CacheLeak
    with pytest.raises(CacheLeak):
        run(cfg, agentmod.get_agent(cfg, AnthropicProvider(client), cache=False))


def test_openai_wire_requests_history_and_usage():
    cfg = models.get("gpt6luna")
    transport, seen = scripted([
        openai_response([reasoning_item(), call_item("call_1", "bash", {"command": "ls"})], 2000, 300, reasoning=250, cached=512),
        openai_response([msg_item('{"q1": 3}')], 2600, 90, reasoning=40)])
    client = openai.OpenAI(api_key="sk-test", base_url="https://api.openai.com/v1", max_retries=0,
                           http_client=httpx.Client(transport=transport))
    r = run(cfg, agentmod.get_agent(cfg, OpenAIProvider(client)))
    assert r.result.text == '{"q1": 3}'
    u = r.result.usage
    assert (u.input_tokens + u.cache_read_tokens, u.output_tokens, u.reasoning_tokens) == (4600, 390, 290)
    assert r.turns[0]["cache_read_tokens"] == 512 and r.turns[0]["input_tokens"] == 1488
    first, second = (s["body"] for s in seen)
    assert seen[0]["path"] == "/v1/responses"
    assert first["model"] == "gpt-6-luna" and first["store"] is False and first["reasoning"] == {"effort": "medium"}
    assert first["max_output_tokens"] == 32000 and first["instructions"] == AGENT_SYSTEM
    assert first["include"] == ["reasoning.encrypted_content"]
    assert {t["name"] for t in first["tools"]} == {"bash", "read_file"} and all(t["type"] == "function" for t in first["tools"])
    types = [i.get("type", i.get("role")) for i in second["input"]]
    assert types == ["user", "reasoning", "function_call", "function_call_output"]
    assert second["input"][3]["call_id"] == "call_1" and "book.xlsx" in second["input"][3]["output"]
    assert second["input"][1]["encrypted_content"] == "enc"
    # cached input is still priced as uncached input: 4600 input tokens at $0.10, 390 output at $0.50 per million
    assert r.result.cost == pytest.approx((2000 * 0.10 + 300 * 0.50 + 2600 * 0.10 + 90 * 0.50) / 1e6)


def test_openai_wire_incomplete_turn_is_truncated_and_keeps_tokens():
    from runner.types import Truncated
    cfg = models.get("gpt6luna")
    transport, _ = scripted([openai_response([reasoning_item()], 900, 32000, reasoning=32000, status="incomplete")])
    client = openai.OpenAI(api_key="sk-test", max_retries=0, http_client=httpx.Client(transport=transport))
    with pytest.raises(Truncated) as e:
        run(cfg, agentmod.get_agent(cfg, OpenAIProvider(client)))
    assert e.value.result.usage.output_tokens == 32000


def test_anthropic_cached_turns_are_priced_uncached_and_billed_separately():
    """With caching on, cache reads are allowed; the cost metric still prices every token uncached, and the billed
    amount (cache reads at the cache price) is recorded beside it."""
    cfg = models.get("sonnet55")
    s1 = anthropic_stream([("tool_use", "toolu_1", "bash", {"command": "ls"})], "tool_use", 1000, 100)
    s2 = anthropic_stream([("text", '{"q1": 3}')], "end_turn", 100, 50)
    s2 = httpx.Response(200, headers=s2.headers, content=s2.content.replace(
        b'"input_tokens": 100', b'"input_tokens": 100, "cache_read_input_tokens": 1100'))
    transport, seen = scripted([s1, s2])
    client = anthropic.Anthropic(api_key="sk-test", max_retries=0, http_client=httpx.Client(transport=transport))
    r = run(cfg, agentmod.get_agent(cfg, AnthropicProvider(client)))
    uncached = ((1000 + 1200) * 2.0 + 150 * 10.0) / 1e6
    billed = ((1000 + 100) * 2.0 + 1100 * 0.10 + 150 * 10.0) / 1e6
    assert abs(r.result.cost - uncached) < 1e-9
    assert abs(r.result.raw_usage["billed_usd"] - billed) < 1e-6
