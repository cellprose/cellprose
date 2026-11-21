"""Tests for the direct-API benchmark runner. No network: the Anthropic client is replaced by a fake."""
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BENCH = Path(__file__).resolve().parent.parent / "benchmarks"
sys.path.insert(0, str(BENCH))

import api_run  # noqa: E402
from runner import models  # noqa: E402
from runner.cost import call_cost, estimate  # noqa: E402
from runner.prompts import SYSTEM, prompt  # noqa: E402
from runner.providers import AnthropicProvider, anthropic_credentials  # noqa: E402
from runner.store import build_raw, raw_path  # noqa: E402
from runner.types import CacheLeak, Truncated, Usage  # noqa: E402


def message(text="{}", model="claude-haiku-5-5", stop="end_turn", inp=100, out=50, cache_read=0, cache_write=0):
    usage = SimpleNamespace(input_tokens=inp, output_tokens=out, cache_read_input_tokens=cache_read,
                            cache_creation_input_tokens=cache_write,
                            output_tokens_details=SimpleNamespace(thinking_tokens=out // 2),
                            model_dump=lambda: {"input_tokens": inp, "output_tokens": out})
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], model=model, stop_reason=stop,
                           usage=usage, _request_id="req_test")


class _Stream:
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.msg


class FakeClient:
    """Stands in for anthropic.Anthropic: records every request body, replies with a canned message
    (or with reply(kw) when a callable is given)."""

    def __init__(self, reply=None):
        self.requests = []
        self.reply = reply or message()
        self.messages = self

    def stream(self, **kw):
        self.requests.append(kw)
        return _Stream(self.reply(kw) if callable(self.reply) else self.reply)

    def count_tokens(self, **kw):
        return SimpleNamespace(input_tokens=1000)


fake_client = FakeClient


# ---- registry and request body -------------------------------------------------------------------

def test_registry_pins_exact_models_with_explicit_reasoning():
    assert set(models.REGISTRY) >= {"haiku45", "haiku55", "sonnet55"}
    assert re.search(r"-\d{8}$", models.get("haiku45").model_id), "Haiku 4.5 must use the dated snapshot"
    for cfg in models.REGISTRY.values():
        explicit = {"openai": cfg.effort, "openrouter": cfg.extra}.get(cfg.provider, cfg.thinking)
        assert explicit is not None, f"{cfg.alias}: reasoning must be set explicitly"
        assert cfg.price_in > 0 and cfg.price_out > 0
    h45 = models.get("haiku45")
    assert h45.thinking["type"] == "enabled" and h45.thinking["budget_tokens"] < h45.max_tokens
    for alias in ("haiku55", "sonnet55"):
        assert models.get(alias).thinking == {"type": "adaptive"} and models.get(alias).effort


@pytest.mark.parametrize("alias", sorted(a for a, c in models.REGISTRY.items() if c.provider == "anthropic"))
def test_request_body_has_no_caching_and_all_settings(alias):
    cfg = models.get(alias)
    body = AnthropicProvider.request(cfg, "sys", "user text")
    assert "cache_control" not in json.dumps(body)
    assert body["model"] == cfg.model_id and body["max_tokens"] == cfg.max_tokens
    assert body["thinking"] == cfg.thinking
    assert body.get("output_config", {}).get("effort") == cfg.effort
    assert "temperature" not in body        # provider default, recorded in settings()
    assert cfg.settings()["prompt_caching"] == "off"


def test_price_for_matches_snapshot_suffix_and_rejects_unknown():
    assert models.price_for("claude-sonnet-5-5-20261001") == (2.0, 10.0)
    assert models.price_for("claude-haiku-4-5-20251001") == (1.0, 5.0)
    with pytest.raises(KeyError):
        models.price_for("claude-unknown-9")


# ---- provider behaviour --------------------------------------------------------------------------

def test_complete_normalises_usage_and_records_returned_model():
    client = fake_client(message(text="hello", model="claude-haiku-5-5-20261001", inp=120, out=80))
    res = AnthropicProvider(client).complete(models.get("haiku55"), "s", "u")
    assert res.text == "hello" and res.model_returned == "claude-haiku-5-5-20261001"
    assert (res.usage.input_tokens, res.usage.output_tokens, res.usage.reasoning_tokens) == (120, 80, 40)
    assert res.request_id == "req_test"


def test_cache_activity_is_an_error_not_a_result():
    for kw in ({"cache_read": 500}, {"cache_write": 500}):
        with pytest.raises(CacheLeak):
            AnthropicProvider(fake_client(message(**kw))).complete(models.get("haiku55"), "s", "u")


def test_truncated_and_refused_responses_are_errors():
    with pytest.raises(Truncated):
        AnthropicProvider(fake_client(message(stop="max_tokens"))).complete(models.get("haiku55"), "s", "u")
    with pytest.raises(RuntimeError):
        AnthropicProvider(fake_client(message(stop="refusal"))).complete(models.get("haiku55"), "s", "u")


# ---- raw file shape and cost ---------------------------------------------------------------------

def test_call_cost_prices_every_input_token_as_uncached():
    cfg = models.get("haiku45")
    u = Usage(input_tokens=1000, output_tokens=2000, cache_read_tokens=3000, cache_write_tokens=4000)
    assert call_cost(cfg, u) == pytest.approx((8000 * 1.0 + 2000 * 5.0) / 1e6)


def test_raw_file_keeps_the_shape_score_and_analyze_read():
    cfg = models.get("sonnet55")
    res = AnthropicProvider(fake_client(message(model="claude-sonnet-5-5", inp=900, out=100))).complete(cfg, "s", "u")
    d = build_raw(cfg, "01_sales_log", "csv", "u", res, {"run_id": "r1", "rep": 0})
    for key in ("model", "workbook", "encoding", "prompt_chars", "result", "usage", "modelUsage", "cost"):
        assert key in d
    assert d["model"] == "sonnet55"
    u = d["usage"]
    assert {"input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"} <= set(u)
    (model_id, mu), = d["modelUsage"].items()
    assert model_id == "claude-sonnet-5-5" and mu["inputTokens"] == 900 and mu["outputTokens"] == 100
    assert d["cost"] == pytest.approx((900 * 2.0 + 100 * 10.0) / 1e6)
    run = d["run"]
    assert run["requested_model"] == "claude-sonnet-5-5" and run["returned_model"] == model_id
    assert run["settings"]["thinking"] == {"type": "adaptive"} and run["settings"]["effort"] == "high"
    json.dumps(d)       # serialisable


def test_raw_path_follows_existing_naming(tmp_path):
    cfg = models.get("haiku55")
    assert raw_path(tmp_path, cfg, "01_sales_log", "csv", 0) == tmp_path / "raw/haiku55/01_sales_log.csv.json"
    assert raw_path(tmp_path, cfg, "01_sales_log", "csv", 2).name == "01_sales_log.csv.r2.json"


# ---- estimate, sample mode, budget gate ---------------------------------------------------------

def test_estimate_uses_counted_tokens_and_reports_a_ceiling():
    cfg = models.get("haiku55")
    est = estimate([(cfg, "s", "u")] * 3, count_tokens=lambda c, s, u: 1000)
    assert est.calls == 3 and est.input_tokens == 3000 and est.exact_input
    assert est.expected_usd == pytest.approx(3 * (1000 * 0.10 + cfg.est_output_tokens * 0.50) / 1e6)
    assert est.ceiling_usd > est.expected_usd


def test_sample_is_one_model_three_workbooks_two_encodings(tmp_path):
    todo, cached = api_run.plan(["haiku55"], api_run.SAMPLE_WORKBOOKS, api_run.SAMPLE_ENCS, 0, tmp_path)
    assert len(todo) == 6 and cached == 0 and len(api_run.SAMPLE_WORKBOOKS) == 3
    assert all((BENCH / "questions" / f"{w}.json").exists() for w in api_run.SAMPLE_WORKBOOKS)


def test_budget_gate_refuses_before_any_call(tmp_path, monkeypatch, capsys):
    client = fake_client()
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: AnthropicProvider(client))
    rc = api_run.main(["--sample", "--models", "haiku55", "--out", str(tmp_path), "--max-usd", "0.0001"])
    assert rc == 2 and client.requests == []
    assert "above" in capsys.readouterr().out


def test_estimate_only_makes_no_calls_and_prints_cost(tmp_path, monkeypatch, capsys):
    client = fake_client()
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: AnthropicProvider(client))
    assert api_run.main(["--sample", "--models", "haiku55", "--out", str(tmp_path), "--estimate-only"]) == 0
    assert client.requests == [] and "expected cost: $" in capsys.readouterr().out


# ---- end to end: run, skip cached, score ---------------------------------------------------------

def perfect_answers(kw):
    """Reply with the ground truth for whichever workbook the prompt is about."""
    user = kw["messages"][0]["content"]
    wb = next(p.stem for p in (BENCH / "questions").glob("*.json")
              if all(q["q"] in user for q in json.loads(p.read_text())))
    return message(text=json.dumps({q["id"]: q["truth"] for q in json.loads((BENCH / "questions" / f"{wb}.json").read_text())}),
                   model="claude-haiku-5-5")


def test_sample_run_writes_scoreable_files_and_resumes(tmp_path, monkeypatch):
    client = fake_client(perfect_answers)
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: AnthropicProvider(client))
    args = ["--sample", "--models", "haiku55", "--out", str(tmp_path)]
    assert api_run.main(args) == 0
    files = sorted((tmp_path / "raw" / "haiku55").glob("*.json"))
    assert len(files) == 6 and len(client.requests) == 6
    assert len({json.loads(f.read_text())["run"]["run_id"] for f in files}) == 1      # one run id per invocation
    assert all(r["system"] == SYSTEM for r in client.requests)

    assert api_run.main(args) == 0 and len(client.requests) == 6                       # second pass: all cached

    subprocess.run([sys.executable, "score.py"], cwd=BENCH, check=True, capture_output=True,
                   env={**os.environ, "RESULTS_DIR": str(tmp_path)})
    rows = list(csv.DictReader((tmp_path / "scores.csv").open()))
    assert rows and {r["model"] for r in rows} == {"haiku55"}
    assert all(float(r["score"]) == 1.0 for r in rows)


def test_failed_call_is_recorded_as_a_failure_and_returns_nonzero(tmp_path, monkeypatch):
    client = fake_client(message(cache_read=10))
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: AnthropicProvider(client))
    rc = api_run.main(["--models", "haiku55", "--workbooks", "01_sales_log", "--encs", "csv", "--out", str(tmp_path)])
    (raw,) = [json.loads(f.read_text()) for f in (tmp_path / "raw").rglob("*.json")]
    assert rc == 1 and raw["failed"] and raw["failure"]["kind"] == "cache_leak" and raw["result"] == ""


def test_prompts_are_built_from_the_shared_module():
    p = prompt("01_sales_log", "csv")
    assert p.startswith('<workbook format="CSV">') and "Questions:" in p


def test_anthropic_credentials_fallback_and_workspace_header():
    assert anthropic_credentials({}) == (None, {})
    assert anthropic_credentials({"CELLPROSE_ANTHROPIC_KEY": "k2"}) == ("k2", {})
    assert anthropic_credentials({"SHEETMARK_ANTHROPIC_KEY": "k3"}) == ("k3", {})       # the pre-rename name
    assert anthropic_credentials({"CELLPROSE_ANTHROPIC_KEY": "k2", "SHEETMARK_ANTHROPIC_KEY": "k3"})[0] == "k2"
    key, headers = anthropic_credentials({"ANTHROPIC_API_KEY": "k1", "CELLPROSE_ANTHROPIC_KEY": "k2",
                                          "CELLPROSE_ANTHROPIC_WORKSPACE_ID": "ws"})
    assert key == "k1" and headers == {"anthropic-workspace-id": "ws"}


# ---- OpenAI provider ----------------------------------------------------------------------------

from runner.providers import OpenAIProvider  # noqa: E402
from runner.types import ModelCfg  # noqa: E402

OAI = ModelCfg("oai_test", "openai", "gpt-test", 1.0, 4.0, max_tokens=1000, effort="medium",
               prompt_caching="automatic (cannot be disabled); priced uncached")


def oai_response(text="{}", status="completed", inp=1200, cached=1000, out=300, reasoning=200, refusal=False):
    usage = SimpleNamespace(input_tokens=inp, output_tokens=out,
                            input_tokens_details=SimpleNamespace(cached_tokens=cached),
                            output_tokens_details=SimpleNamespace(reasoning_tokens=reasoning),
                            model_dump=lambda: {"input_tokens": inp, "output_tokens": out})
    part = SimpleNamespace(type="refusal" if refusal else "output_text")
    return SimpleNamespace(status=status, incomplete_details=SimpleNamespace(reason="max_output_tokens"),
                           usage=usage, output=[SimpleNamespace(content=[part])], output_text=text,
                           model="gpt-test-2026-01-01", _request_id="req_oai")


class FakeOpenAI:
    def __init__(self, reply):
        self.requests, self.reply, self.responses = [], reply, self

    def create(self, **kw):
        self.requests.append(kw)
        return self.reply


def test_openai_request_sets_effort_and_limits_explicitly():
    body = OpenAIProvider.request(OAI, "sys", "usr")
    assert body == {"model": "gpt-test", "instructions": "sys", "input": "usr", "max_output_tokens": 1000,
                    "store": False, "reasoning": {"effort": "medium"}}
    assert "temperature" not in body and "tools" not in body


def test_openai_usage_splits_cached_input_and_prices_it_uncached():
    client = FakeOpenAI(oai_response())
    res = OpenAIProvider(client).complete(OAI, "s", "u")
    assert (res.usage.input_tokens, res.usage.cache_read_tokens) == (200, 1000)
    assert res.usage.reasoning_tokens == 200 and res.usage.output_tokens == 300
    assert call_cost(OAI, res.usage) == pytest.approx((1200 * 1.0 + 300 * 4.0) / 1e6)
    assert res.raw_usage["billed_input_tokens"] == 1200 and "tokenizer_input_tokens_o200k" in res.raw_usage
    assert OAI.settings()["prompt_caching"].startswith("automatic")


def test_openai_truncation_and_refusal_raise():
    with pytest.raises(Truncated):
        OpenAIProvider(FakeOpenAI(oai_response(status="incomplete"))).complete(OAI, "s", "u")
    with pytest.raises(RuntimeError, match="refused"):
        OpenAIProvider(FakeOpenAI(oai_response(refusal=True))).complete(OAI, "s", "u")


@pytest.mark.parametrize("alias", sorted(a for a, c in models.REGISTRY.items() if c.provider == "openai"))
def test_openai_registry_entries_set_effort_and_state_the_caching_limit(alias):
    cfg = models.get(alias)
    assert OpenAIProvider.request(cfg, "s", "u")["reasoning"] == {"effort": cfg.effort}
    assert "cannot be disabled" in cfg.settings()["prompt_caching"]


def test_reps_share_one_run_id_and_vendor_cap_stops_new_calls(tmp_path, monkeypatch):
    client = fake_client(perfect_answers)
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: AnthropicProvider(client))
    args = ["--sample", "--models", "haiku55", "--out", str(tmp_path), "--reps", "2"]
    assert api_run.main(args) == 0 and len(client.requests) == 12
    files = list((tmp_path / "raw" / "haiku55").glob("*.json"))
    assert {f.stem.split(".")[-1] == "r1" for f in files} == {True, False}
    assert len({json.loads(f.read_text())["run"]["run_id"] for f in files}) == 1


def test_vendor_cap_refuses_when_expected_cost_is_above_it(tmp_path, monkeypatch, capsys):
    client = fake_client()
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: AnthropicProvider(client))
    rc = api_run.main(["--sample", "--models", "haiku55", "--out", str(tmp_path), "--vendor-cap-usd", "0.0000001"])
    assert rc == 2 and client.requests == [] and "vendor cap" in capsys.readouterr().out


def test_long_prompt_tier_prices_each_request_on_its_own_prompt_length():
    haiku, sol, sonnet = models.get("haiku55"), models.get("gpt61sol"), models.get("sonnet55")
    # up to the threshold the base rate applies, one token over switches the whole request (input and output)
    assert call_cost(haiku, Usage(input_tokens=100_000, output_tokens=1_000)) == pytest.approx(0.0105)
    assert call_cost(haiku, Usage(input_tokens=100_001, output_tokens=1_000)) == pytest.approx(0.0525005)
    # cache tokens count towards prompt length
    assert call_cost(haiku, Usage(input_tokens=1, cache_read_tokens=100_000)) > 0.05
    assert call_cost(sol, Usage(input_tokens=272_000, output_tokens=0)) == pytest.approx(0.544)
    assert call_cost(sol, Usage(input_tokens=272_001, output_tokens=0)) == pytest.approx(1.088004)
    # flat-rate models have no tier
    assert sonnet.long_threshold is None
    assert call_cost(sonnet, Usage(input_tokens=500_000)) == pytest.approx(1.0)


def test_estimate_uses_the_long_rate_for_a_long_prompt():
    cfg = models.get("haiku55")
    short = estimate([(cfg, "s", "x" * 1000)], count_tokens=lambda *a: 50_000)
    long_ = estimate([(cfg, "s", "x" * 1000)], count_tokens=lambda *a: 150_000)
    assert long_.expected_usd / short.expected_usd > 4


def test_registry_prices_match_vendor_pages_checked_2026_10_11():
    want = {"haiku45": (1, 5), "haiku55": (0.10, 0.50), "sonnet55": (2, 10), "opus55": (4, 20), "fable51": (10, 50),
            "gpt6luna": (0.10, 0.50), "gpt61sol": (2, 10), "gpt6astra": (10, 50)}
    for alias, p in want.items():
        assert (models.get(alias).price_in, models.get(alias).price_out) == p
    assert (models.get("haiku55").prices(100_001)) == (0.50, 2.50)
    assert (models.get("gpt6luna").prices(272_001)) == (0.20, 0.75)
    assert (models.get("gpt6astra").prices(272_001)) == (20.0, 75.0)
