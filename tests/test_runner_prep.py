"""Tests for the benchmark prep of docs/PROTOCOL.md: dev/held-out split, failure records, run metadata, paired bootstrap,
the MarkItDown baseline, the agent-mode API runner and the open-weight provider. No network and no paid calls: every
client is a fake."""
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("pandas")       # benchmark extras; CI installs them (see .github/workflows/ci.yml)

BENCH = Path(__file__).resolve().parent.parent / "benchmarks"
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_agent  # noqa: E402
import api_run  # noqa: E402
import encoders  # noqa: E402
import stats  # noqa: E402
from runner import agent as agentmod, models, split as splitmod  # noqa: E402
from runner.cost import call_cost  # noqa: E402
from runner.prompts import AGENT_SYSTEM, prompt  # noqa: E402
from runner.providers import AnthropicProvider, OpenAICompatProvider, OpenAIProvider, OpenRouterProvider  # noqa: E402
from runner.store import build_failure, build_raw, recordable  # noqa: E402
from runner.types import ApiFailure, BudgetExceeded, CallError, ModelCfg, Truncated, TurnLimit  # noqa: E402
from test_runner import FakeClient, message, perfect_answers  # noqa: E402


def read_raw(root, alias="haiku55"):
    return {f.name: json.loads(f.read_text()) for f in sorted((root / "raw" / alias).glob("*.json"))}


def run_scores(root):
    subprocess.run([sys.executable, "score.py"], cwd=BENCH, check=True, capture_output=True,
                   env={**os.environ, "RESULTS_DIR": str(root)})
    return list(csv.DictReader((root / "scores.csv").open()))


@pytest.fixture
def provider(monkeypatch):
    """Patch both runners to use one Anthropic provider on a fake client."""
    def make(client):
        monkeypatch.setattr(api_run, "get_provider", lambda cfg: AnthropicProvider(client))
        monkeypatch.setattr(api_agent, "get_provider", lambda cfg: AnthropicProvider(client))
        return client
    return make


@pytest.fixture(autouse=True)
def _restore_registry():
    before = dict(models.REGISTRY), dict(models.PRICES)
    yield
    models.REGISTRY.clear(); models.REGISTRY.update(before[0])
    models.PRICES.clear(); models.PRICES.update(before[1])


# ---- 1. dev / held-out split ----------------------------------------------------------------------

def test_split_lists_every_synthetic_workbook_as_dev_and_fences_everything_else():
    sp = splitmod.load()
    on_disk = sorted(p.stem for p in (BENCH / "questions").glob("*.json"))
    assert sp["dev"] == on_disk and len(on_disk) == 14
    assert splitmod.role("01_sales_log", sp) == "dev"
    assert splitmod.role("sb_12345", sp) == "held_out" and splitmod.role("rw_budget", sp) == "held_out"
    assert splitmod.role("something_new", sp) == "held_out"        # unlisted means held out
    assert splitmod.role("dev_apv", sp) == "dev"                   # the reserved dev_ prefix (E33)
    assert splitmod.role("rw2_dam_x", sp) == "held_out" and splitmod.role("rw3_enron_x", sp) == "held_out"


def test_subset_is_seeded_sorted_and_independent_of_input_order():
    pool = [f"sb_{i}" for i in range(50)]
    a = splitmod.subset(pool, 10, seed=1)
    assert a == splitmod.subset(list(reversed(pool)), 10, seed=1) == sorted(a) and len(set(a)) == 10
    assert a != splitmod.subset(pool, 10, seed=2)
    assert splitmod.subset(pool, None, 1) == sorted(pool) and splitmod.subset(pool, 99, 1) == sorted(pool)


def test_select_defaults_to_dev_and_needs_final_for_held_out():
    allwb = ["01_sales_log", "sb_1", "sb_2", "sb_3"]
    assert splitmod.select(None, None, allwb, False, None, None) == ["01_sales_log"]
    assert splitmod.select(None, None, allwb, True, None, None) == ["01_sales_log", "sb_1", "sb_2", "sb_3"]
    assert len(splitmod.select(None, None, allwb, True, 2, 7)) == 1 + 2
    with pytest.raises(SystemExit, match="held-out"):
        splitmod.select("sb_1", None, allwb, False, None, None)
    with pytest.raises(SystemExit, match="no development workbooks"):
        splitmod.select(None, None, ["sb_1"], False, None, None)
    with pytest.raises(SystemExit, match="--sample"):
        splitmod.select(None, ["01_sales_log"], allwb, True, None, None)


def test_api_run_refuses_held_out_without_final_before_any_call(tmp_path, provider, capsys):
    client = provider(FakeClient())
    rc = api_run.main(["--workbooks", "sb_123", "--encs", "csv", "--models", "haiku55", "--out", str(tmp_path)])
    assert rc == 2 and client.requests == [] and "--final" in capsys.readouterr().out


def test_final_refuses_a_dirty_tree_unless_allowed_and_records_it(tmp_path, provider, monkeypatch, capsys):
    client = provider(FakeClient(perfect_answers))
    monkeypatch.setattr(api_run, "git_dirty", lambda *a, **k: True)
    monkeypatch.setattr("runner.runmeta.git_dirty", lambda *a, **k: True)
    args = ["--final", "--workbooks", "03_pnl_quarterly", "--encs", "csv", "--models", "haiku55", "--out", str(tmp_path)]
    assert api_run.main(args) == 2 and client.requests == [] and "uncommitted" in capsys.readouterr().out
    assert api_run.main(args + ["--allow-dirty"]) == 2 and "--prices-checked" in capsys.readouterr().out
    assert api_run.main(args + ["--allow-dirty", "--prices-checked", "11/11/2026"]) == 2
    assert api_run.main(args + ["--allow-dirty", "--prices-checked", "2026-11-11"]) == 0
    (raw,) = read_raw(tmp_path).values()
    assert raw["run"]["git_dirty"] is True and raw["run"]["final"] is True
    (man,) = (tmp_path / "runs").glob("*.json")
    assert json.loads(man.read_text())["invocation"]["prices_checked"] == "2026-11-11"


def test_estimates_use_the_api_pilot_where_it_ran_the_model_and_arm():
    from runner.pilot import measured
    out, usd, n = measured("sonnet55", "cellprose_v03")              # the pilot ran it under its old id
    assert n == 30 and out > 500 and usd > 0
    assert measured("sonnet55", "agent_xlsx_viewer") == measured("sonnet55", "agent_xlsx")
    assert measured("haiku45", "csv") is None
    from runner.cost import estimate
    cfg = models.get("haiku55")
    assert estimate([(cfg, "s", "u" * 400, 2000)]).expected_output_tokens == 2000
    assert estimate([(cfg, "s", "u" * 400)]).expected_output_tokens == cfg.est_output_tokens


def test_freeze_hashes_damodaran_workbooks_by_content_and_fetch_checks_it(tmp_path):
    import shutil
    import openpyxl
    import freeze
    wb = openpyxl.Workbook()
    wb.active["A1"], wb.active["A2"], wb.active["A3"] = 2, 3, "=A1*A2"
    a, b = tmp_path / "a.xlsx", tmp_path / "b.xlsx"
    wb.save(a)
    shutil.copy(a, b)
    assert freeze.cell_sha256(a) == freeze.cell_sha256(b)
    wb.active["A2"] = 4
    wb.save(b)
    assert freeze.cell_sha256(a) != freeze.cell_sha256(b)
    assert freeze.by_content(freeze.RW2 / "workbooks" / "rw2_dam_risk.xlsx")
    assert not freeze.by_content(freeze.RW2 / "workbooks" / "rw2_enron_x.xlsx")
    sel = json.loads((freeze.RW2 / "selection.json").read_text())["workbooks"]
    dam = [e for e in sel.values() if e["source"] == "damodaran"]
    assert len(dam) == 15 and all(len(e["source_sha256"]) == 64 and len(e["cell_sha256"]) == 64 for e in dam)


# ---- 2. failed calls are recorded and scored 0 --------------------------------------------------------

def test_truncated_call_is_recorded_with_its_tokens_and_scores_zero(tmp_path, provider):
    provider(FakeClient(message(stop="max_tokens", inp=900, out=400)))
    rc = api_run.main(["--workbooks", "03_pnl_quarterly", "--encs", "csv", "--models", "haiku55", "--out", str(tmp_path)])
    assert rc == 1
    (raw,) = read_raw(tmp_path).values()
    assert raw["failed"] is True and raw["failure"]["kind"] == "truncated" and raw["result"] == ""
    assert raw["usage"]["input_tokens"] == 900 and raw["usage"]["output_tokens"] == 400
    assert raw["cost"] == pytest.approx((900 * 0.10 + 400 * 0.50) / 1e6)          # the tokens are still paid for
    rows = run_scores(tmp_path)
    assert rows and all(float(r["score"]) == 0.0 and r["failed"] == "1" for r in rows)
    summary = list(csv.DictReader((tmp_path / "summary.csv").open()))
    assert all(int(r["failed_questions"]) > 0 for r in summary)


def _api_error(name, status=None, module="anthropic"):
    """An exception class shaped like the SDK's: its module and, for HTTP errors, a status_code."""
    def init(self, msg):
        Exception.__init__(self, msg)
        if status is not None:
            self.status_code = status
    return type(name, (Exception,), {"__module__": module, "__init__": init})


class Raising(FakeClient):
    def __init__(self, exc):
        super().__init__()
        self.exc = exc

    def stream(self, **kw):
        self.requests.append(kw)
        raise self.exc


def test_refusal_cache_leak_and_api_errors_are_recorded(tmp_path, provider):
    api_error = _api_error("BadRequestError", 400)

    class Boom(FakeClient):
        def stream(self, **kw):
            raise api_error("prompt is malformed")

    for name, client, kind in [("refusal", FakeClient(message(stop="refusal")), "refused"),
                               ("leak", FakeClient(message(cache_read=10)), "cache_leak"),
                               ("api", Boom(), "error")]:
        out = tmp_path / name
        provider(client)
        assert api_run.main(["--workbooks", "03_pnl_quarterly", "--encs", "csv", "--models", "haiku55", "--out", str(out)]) == 1
        (raw,) = read_raw(out).values()
        assert raw["failed"] and raw["failure"]["kind"] == kind
        if name == "api":
            assert raw["usage"]["input_tokens"] == 0 and raw["cost"] == 0 and "malformed" in raw["failure"]["message"]


# ---- infrastructure failures and resume (PROTOCOL.md sections 5 and 8) -----------------------------

def test_infrastructure_failures_are_told_apart_from_the_models_own():
    from runner.store import infrastructure
    for exc in [_api_error("APIConnectionError")("reset"), _api_error("APITimeoutError")("slow"),
                _api_error("ConnectError", module="httpx")("dns"), _api_error("RateLimitError", 429)("slow down"),
                _api_error("AuthenticationError", 401)("bad key"), _api_error("PermissionDeniedError", 403)("no"),
                _api_error("InternalServerError", 500)("oops"), _api_error("OverloadedError", 529)("overloaded"),
                _api_error("BadRequestError", 400)("Your credit balance is too low to access the API"),
                _api_error("RateLimitError", 429, "openai")("You exceeded your current quota (insufficient_quota)")]:
        assert infrastructure(exc), exc
    wrapped = ApiFailure("APIConnectionError: reset", None)
    wrapped.__cause__ = _api_error("APIConnectionError")("reset")
    assert infrastructure(wrapped)                                   # the agent loop wraps the SDK error
    for exc in [_api_error("BadRequestError", 400)("prompt is too long"), Truncated("x"), TurnLimit("x"),
                BudgetExceeded("x"), RuntimeError("billing")]:  # a plain error naming billing has no status: not infra
        assert not infrastructure(exc), exc


def test_an_infrastructure_failure_is_logged_not_recorded_and_stays_to_do(tmp_path, provider, capsys):
    args = ["--workbooks", "03_pnl_quarterly", "--encs", "csv", "--models", "haiku55", "--out", str(tmp_path)]
    provider(Raising(_api_error("APIConnectionError")("connection reset")))
    assert api_run.main(args) == 1
    out = capsys.readouterr().out
    assert not list((tmp_path / "raw").rglob("*.json"))
    run_id = out.split("--resume ")[1].split()[0]
    (line,) = (tmp_path / "runs" / f"{run_id}.infra.jsonl").read_text().splitlines()
    assert json.loads(line)["type"] == "APIConnectionError" and json.loads(line)["cost"] == 0
    provider(FakeClient(perfect_answers))
    assert api_run.main(args + ["--resume", run_id]) == 0
    (raw,) = read_raw(tmp_path).values()
    assert raw["run"]["run_id"] == run_id and not raw.get("failed")
    man = json.loads((tmp_path / "runs" / f"{run_id}.json").read_text())
    assert len(man["resumes"]) == 1 and "--resume" in man["resumes"][0]["argv"]


def test_resume_refuses_other_settings_changed_code_or_an_old_run(tmp_path, provider, monkeypatch, capsys):
    import runner.runmeta as runmeta
    args = ["--workbooks", "03_pnl_quarterly", "--encs", "csv", "--models", "haiku55", "--out", str(tmp_path)]
    provider(Raising(_api_error("OverloadedError", 529)("overloaded")))
    api_run.main(args)
    run_id = capsys.readouterr().out.split("--resume ")[1].split()[0]
    assert api_run.main(args + ["--encs", "markitdown", "--resume", run_id]) == 2
    assert "other settings (encodings)" in capsys.readouterr().out
    assert api_run.main(args + ["--resume", "nope"]) == 2
    monkeypatch.setattr(runmeta, "git_sha", lambda: "0000000")
    assert api_run.main(args + ["--resume", run_id]) == 2 and "code changed" in capsys.readouterr().out
    monkeypatch.undo()
    provider(Raising(_api_error("OverloadedError", 529)("overloaded")))
    path = tmp_path / "runs" / f"{run_id}.json"
    man = json.loads(path.read_text())
    man["run"]["started_at"] = "2026-01-01T00:00:00+00:00"
    path.write_text(json.dumps(man))
    assert api_run.main(args + ["--resume", run_id]) == 2 and "48 h window" in capsys.readouterr().out
    assert not list((tmp_path / "raw").rglob("*.json"))


def test_a_vendor_is_stopped_after_five_infrastructure_failures_in_a_row(tmp_path, provider, capsys):
    client = provider(Raising(_api_error("BadRequestError", 400)("Your credit balance is too low")))
    wbs = ["01_sales_log", "02_employees", "03_pnl_quarterly", "04_saas_model", "05_multisheet_model",
           "06_budget_vs_actual", "07_messy_report", "08_loan_schedule"]
    assert len(wbs) > api_run.INFRA_STOP
    rc = api_run.main(["--workbooks", ",".join(wbs), "--encs", "csv", "--models", "haiku55", "--out", str(tmp_path),
                       "--workers", "1"])
    out = capsys.readouterr().out
    assert rc == 1 and not list((tmp_path / "raw").rglob("*.json"))
    assert len(client.requests) == api_run.INFRA_STOP and "5 infrastructure failures in a row" in out
    assert f"({api_run.INFRA_STOP} infrastructure failures, {len(wbs) - api_run.INFRA_STOP} skipped" in out


def test_an_agent_call_cut_off_by_the_network_is_not_recorded_but_its_spend_is_logged(tmp_path, provider, capsys):
    class Flaky(ScriptedClient):
        def stream(self, **kw):
            if not self.script:
                raise _api_error("APIConnectionError")("reset")
            return super().stream(**kw)

    provider(Flaky([tool_message([{"command": "true"}])]))
    rc = api_agent.main(["--workbooks", "03_pnl_quarterly", "--variants", "agent_xlsx", "--models", "haiku55",
                         "--out", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 1 and not list((tmp_path / "raw").rglob("*.json")) and "--resume" in out
    run_id = out.split("--resume ")[1].split()[0]
    (line,) = (tmp_path / "runs" / f"{run_id}.infra.jsonl").read_text().splitlines()
    assert json.loads(line)["cost"] > 0                              # the completed turn was paid for


def test_a_bug_in_the_runner_is_not_recorded_as_a_model_failure(tmp_path, provider):
    class Bug(FakeClient):
        def stream(self, **kw):
            raise TypeError("a bug, not a model failure")

    provider(Bug())
    rc = api_run.main(["--workbooks", "03_pnl_quarterly", "--encs", "csv", "--models", "haiku55", "--out", str(tmp_path)])
    assert rc == 1 and not list((tmp_path / "raw").rglob("*.json"))
    assert recordable(Truncated("x")) and not recordable(TypeError("x"))


def test_build_failure_without_a_response_has_zero_usage():
    d = build_failure(models.get("haiku55"), "wb", "csv", "prompt", RuntimeError("x"), {"run_id": "r"})
    assert d["failed"] and d["usage"]["input_tokens"] == 0 and d["cost"] == 0 and d["modelUsage"]


# ---- 3. input checksums, dirty flag, manifest -----------------------------------------------------------

def test_run_writes_manifest_with_input_checksums_and_prompt_hash(tmp_path, provider):
    provider(FakeClient(perfect_answers))
    assert api_run.main(["--workbooks", "03_pnl_quarterly", "--encs", "csv,markitdown,none", "--models", "haiku55",
                         "--out", str(tmp_path)]) == 0
    raws = read_raw(tmp_path)
    runs = {r["run"]["run_id"] for r in raws.values()}
    (manifest_path,) = (tmp_path / "runs").glob("*.json")
    manifest = json.loads(manifest_path.read_text())
    assert runs == {manifest["run"]["run_id"]} and manifest_path.stem in runs
    files = manifest["inputs"]["files"]
    assert set(files) == {"questions/03_pnl_quarterly.json", "encoded/03_pnl_quarterly.csv.txt",
                          "encoded/03_pnl_quarterly.markitdown.txt"}
    assert files["encoded/03_pnl_quarterly.csv.txt"] == hashlib.sha256(
        (BENCH / "encoded" / "03_pnl_quarterly.csv.txt").read_bytes()).hexdigest()
    run = next(iter(raws.values()))["run"]
    assert run["inputs_sha256"] == manifest["inputs"]["digest"] and run["split_sha256"]
    assert isinstance(run["git_dirty"], (bool, type(None))) and run["final"] is False
    csv_raw = raws["03_pnl_quarterly.csv.json"]
    assert csv_raw["prompt_sha256"] == hashlib.sha256(prompt("03_pnl_quarterly", "csv").encode()).hexdigest()


# ---- 4. paired bootstrap and verdicts -----------------------------------------------------------------------

def frame(a_cost, b_cost, a_acc=1.0, b_acc=1.0, n=12):
    import pandas as pd
    rows = []
    for i in range(n):
        wiggles = {"sheetmark_lean_gfm": 1 + 0.08 * ((i % 4) - 1.5), "csv": 1 + 0.08 * (((i * 3) % 5) - 2)}
        for enc, c, acc in (("sheetmark_lean_gfm", a_cost, a_acc), ("csv", b_cost, b_acc)):
            rows.append({"model": "m", "workbook": f"w{i}", "encoding": enc, "rep": "r0", "cost": c * wiggles[enc], "acc": acc})
    return pd.DataFrame(rows)


def test_bootstrap_calls_a_clear_saving_a_win_and_is_reproducible():
    r = stats.paired_comparison(frame(0.7, 1.0), "m", "sheetmark_lean_gfm", "csv")
    assert r["verdict"] == "win" and r["ratio_hi"] < 1 and r["ratio"] == pytest.approx(0.7, abs=0.01)
    assert r["ratio_lo"] <= r["ratio"] <= r["ratio_hi"]
    assert r == stats.paired_comparison(frame(0.7, 1.0), "m", "sheetmark_lean_gfm", "csv")      # fixed seed


def test_bootstrap_verdicts_for_loss_no_difference_and_accuracy_drop():
    assert stats.paired_comparison(frame(1.4, 1.0), "m", "sheetmark_lean_gfm", "csv")["verdict"] == "loss"
    assert stats.paired_comparison(frame(1.0, 1.0), "m", "sheetmark_lean_gfm", "csv")["verdict"] == "no difference"
    cheap_but_worse = stats.paired_comparison(frame(0.5, 1.0, a_acc=0.9, b_acc=1.0), "m", "sheetmark_lean_gfm", "csv")
    assert cheap_but_worse["ratio_hi"] < 1 and cheap_but_worse["verdict"] == "no difference"     # >1 point below: not a win
    within = stats.paired_comparison(frame(0.5, 1.0, a_acc=0.995, b_acc=1.0), "m", "sheetmark_lean_gfm", "csv")
    assert within["verdict"] == "win"


def test_bootstrap_interval_widens_with_fewer_workbooks_and_handles_zero_accuracy():
    wide = stats.paired_comparison(frame(0.8, 1.0, n=4), "m", "sheetmark_lean_gfm", "csv")
    narrow = stats.paired_comparison(frame(0.8, 1.0, n=40), "m", "sheetmark_lean_gfm", "csv")
    assert wide["ratio_hi"] - wide["ratio_lo"] >= narrow["ratio_hi"] - narrow["ratio_lo"]
    dead = stats.paired_comparison(frame(1.0, 1.0, a_acc=0.0), "m", "sheetmark_lean_gfm", "csv")
    assert dead["ratio"] == float("inf") and dead["verdict"] == "loss"
    assert stats.paired_comparison(frame(1, 1), "m", "sheetmark_lean_gfm", "toon") is None


def test_analyze_prints_verdicts_and_tokenizer_table_for_a_run(tmp_path, provider):
    provider(FakeClient(perfect_answers))
    assert api_run.main(["--sample", "--models", "haiku55", "--out", str(tmp_path)]) == 0
    run_scores(tmp_path)
    r = subprocess.run([sys.executable, "analyze.py"], cwd=BENCH, check=True, capture_output=True, text=True,
                       env={**os.environ, "RESULTS_DIR": str(tmp_path)})
    assert "cost per correct vs each baseline" in r.stdout and "vendor tokenizer count" in r.stdout
    verdicts = json.loads((tmp_path / "verdicts.json").read_text())
    assert verdicts and {v["verdict"] for v in verdicts} <= {"win", "loss", "no difference"}
    assert all(v["set"] in ("dev", "held_out", "all") for v in verdicts)
    assert (tmp_path / "tokenizer_counts.csv").exists()


def test_analyze_prices_a_call_from_its_recorded_prices(tmp_path, monkeypatch):
    models.register_openweight("ow_test", "acme/open-1", 0.3, 0.9)
    client = FakeChat(compat_response())
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: OpenAICompatProvider(client))
    assert api_run.main(["--workbooks", "03_pnl_quarterly", "--encs", "csv,sheetmark_lean_gfm", "--models", "ow_test",
                         "--out", str(tmp_path)]) == 0
    run_scores(tmp_path)
    r = subprocess.run([sys.executable, "analyze.py"], cwd=BENCH, capture_output=True, text=True,
                       env={**os.environ, "RESULTS_DIR": str(tmp_path)})
    assert r.returncode == 0, r.stderr        # this process registered the model; analyze.py's does not know it
    head = json.loads((tmp_path / "headline.json").read_text())["oneshot_all"]
    assert head[0]["cost"] == pytest.approx((1200 * 0.3 + 300 * 0.9) / 1e6)


# ---- 5. MarkItDown baseline -----------------------------------------------------------------------------------

def test_markitdown_encoding_is_the_real_converter_and_the_committed_files_match():
    pytest.importorskip("markitdown")
    assert "markitdown" in encoders.ENCODINGS
    text = encoders.encode(BENCH / "workbooks" / "03_pnl_quarterly.xlsx", "markitdown")
    assert text.startswith("## P&L") and "| Units |" in text
    assert text == (BENCH / "encoded" / "03_pnl_quarterly.markitdown.txt").read_text()
    assert prompt("03_pnl_quarterly", "markitdown").startswith('<workbook format="Markdown tables (MarkItDown)">')


def test_markitdown_version_is_pinned_to_the_one_that_made_the_committed_files():
    pytest.importorskip("markitdown")
    import importlib.metadata as md
    pin = next(l for l in (BENCH.parent / "pyproject.toml").read_text().splitlines() if l.startswith("bench"))
    assert f"markitdown=={md.version('markitdown')}" in pin


# ---- 6. agent mode ------------------------------------------------------------------------------------------------

def block(**kw):
    return SimpleNamespace(**kw)


def tool_message(commands, model="claude-haiku-5-5", inp=1000, out=100, name="bash"):
    content = [block(type="thinking", thinking="…", signature="s")]
    content += [block(type="tool_use", id=f"tu_{i}", name=name, input=c) for i, c in enumerate(commands)]
    return _msg(content, "tool_use", model, inp, out)


def final_message(text, model="claude-haiku-5-5", inp=1500, out=60):
    return _msg([block(type="text", text=text)], "end_turn", model, inp, out)


def _msg(content, stop, model, inp, out, cache_read=0):
    usage = SimpleNamespace(input_tokens=inp, output_tokens=out, cache_read_input_tokens=cache_read,
                            cache_creation_input_tokens=0, output_tokens_details=SimpleNamespace(thinking_tokens=out // 2),
                            model_dump=lambda: {"input_tokens": inp, "output_tokens": out})
    return SimpleNamespace(content=content, model=model, stop_reason=stop, usage=usage, _request_id="req_agent")


class ScriptedClient(FakeClient):
    """Replies with the scripted messages in order and keeps a snapshot of every request."""

    def __init__(self, script):
        super().__init__()
        self.script = list(script)

    def stream(self, **kw):
        kw = {**kw, "messages": list(kw["messages"])}
        self.requests.append(kw)
        from test_runner import _Stream
        return _Stream(self.script.pop(0))


def truth_json(wb):
    qs = json.loads((BENCH / "questions" / f"{wb}.json").read_text())
    return json.dumps({q["id"]: q["truth"] for q in qs})


def test_agent_loop_runs_tools_in_a_sandbox_and_sums_usage_over_turns():
    cfg = models.get("haiku55")
    client = ScriptedClient([tool_message([{"command": "ls; env"}], inp=1000, out=100),
                             tool_message([{"path": "../../etc/passwd"}], name="read_file", inp=1400, out=80),
                             final_message('{"q1": 1}', inp=1700, out=60)])
    os.environ["ANTHROPIC_API_KEY"] = "sk-test-secret"
    backend = agentmod.get_agent(cfg, AnthropicProvider(client))
    with agentmod.Sandbox({"book.xlsx": BENCH / "workbooks" / "03_pnl_quarterly.xlsx"}) as sb:
        run = agentmod.run_agent(cfg, backend, AGENT_SYSTEM, "question", sb)
    assert run.result.text == '{"q1": 1}'
    assert [t["input_tokens"] for t in run.turns] == [1000, 1400, 1700]
    u = run.result.usage
    assert (u.input_tokens, u.output_tokens, u.reasoning_tokens) == (4100, 240, 120)
    second = client.requests[1]["messages"][-1]["content"][0]["content"]
    assert "book.xlsx" in second and "sk-test-secret" not in second          # file visible, API key is not
    assert "outside the workbook folder" in client.requests[2]["messages"][-1]["content"][0]["content"]
    assert [t["tool"] for t in run.trace] == ["bash", "read_file"]
    for req in client.requests:
        assert req["cache_control"] == {"type": "ephemeral"}     # automatic caching on agent turns (PROTOCOL 5)
        assert {t["name"] for t in req["tools"]} == {"bash", "read_file"}
        assert req["model"] == cfg.model_id and req["thinking"] == cfg.thinking
    # thinking blocks go back to the API untouched
    assert client.requests[1]["messages"][1]["content"][0].type == "thinking"
    assert call_cost(cfg, u) == pytest.approx((4100 * 0.10 + 240 * 0.50) / 1e6)


def test_agent_turn_limit_and_budget_cap_raise_with_the_tokens_spent():
    cfg = models.get("haiku55")
    loop = [tool_message([{"command": "true"}]) for _ in range(10)]
    with agentmod.Sandbox({}) as sb:
        with pytest.raises(TurnLimit) as e:
            agentmod.run_agent(cfg, agentmod.get_agent(cfg, AnthropicProvider(ScriptedClient(loop))), "s", "u", sb, max_turns=3)
        assert e.value.result.usage.input_tokens == 3000 and len(e.value.result.raw_usage["turns"]) == 3
        costly = ModelCfg("pricey", "anthropic", "claude-haiku-5-5", 1000.0, 1000.0, max_tokens=100, thinking={"type": "adaptive"})
        with pytest.raises(BudgetExceeded) as e2:
            agentmod.run_agent(costly, agentmod.get_agent(costly, AnthropicProvider(ScriptedClient(loop))), "s", "u", sb,
                               max_call_usd=1.0)
        assert len(e2.value.result.raw_usage["turns"]) == 1          # the cap is checked before each turn


def test_agent_truncated_turn_keeps_earlier_turns_tokens():
    cfg = models.get("haiku55")
    script = [tool_message([{"command": "true"}], inp=1000, out=100),
              _msg([block(type="text", text="cut")], "max_tokens", "claude-haiku-5-5", 1200, 300)]
    with agentmod.Sandbox({}) as sb:
        with pytest.raises(Truncated) as e:
            agentmod.run_agent(cfg, agentmod.get_agent(cfg, AnthropicProvider(ScriptedClient(script))), "s", "u", sb)
    assert e.value.result.usage.input_tokens == 2200 and e.value.result.usage.output_tokens == 400


def test_agent_run_end_to_end_writes_scoreable_files_with_per_turn_accounting(tmp_path, provider):
    wb = "03_pnl_quarterly"
    script = []
    for _ in range(2):          # two variants, each: one tool turn, then the answer
        script += [tool_message([{"command": "ls"}]), final_message(truth_json(wb))]
    client = provider(ScriptedClient(script))
    rc = api_agent.main(["--workbooks", wb, "--models", "haiku55", "--out", str(tmp_path), "--workers", "1"])
    assert rc == 0
    raws = read_raw(tmp_path)
    assert set(raws) == {f"{wb}.agent_xlsx.json", f"{wb}.agent_cellprose_v03.json"}
    for d in raws.values():
        assert d["num_turns"] == 2 and len(d["run"]["provider_usage"]["turns"]) == 2 and d["tool_trace"][0]["tool"] == "bash"
        assert d["usage"]["input_tokens"] == 2500 and d["run"]["max_turns"] == 40
    first = client.requests[0]
    assert first["system"] == AGENT_SYSTEM and "./book.xlsx" in json.dumps(first["messages"][0]["content"]) or "./book.sheet.md" in json.dumps(first["messages"][0]["content"])
    (manifest,) = (tmp_path / "runs").glob("*.json")
    files = json.loads(manifest.read_text())["inputs"]["files"]
    assert f"workbooks/{wb}.xlsx" in files and f"encoded/{wb}.cellprose_v03.txt" in files
    rows = run_scores(tmp_path)
    assert rows and all(float(r["score"]) == 1.0 for r in rows) and {r["encoding"] for r in rows} == {"agent_xlsx", "agent_cellprose_v03"}


def test_agent_failures_are_recorded_and_the_guard_applies(tmp_path, provider, capsys):
    wb = "03_pnl_quarterly"
    provider(ScriptedClient([tool_message([{"command": "true"}]) for _ in range(5)]))
    rc = api_agent.main(["--workbooks", wb, "--variants", "agent_xlsx", "--models", "haiku55", "--out", str(tmp_path),
                         "--max-turns", "2"])
    assert rc == 1
    (d,) = read_raw(tmp_path).values()
    assert d["failed"] and d["failure"]["kind"] == "turn_limit" and d["num_turns"] == 2 and d["usage"]["input_tokens"] == 2000
    assert api_agent.main(["--workbooks", "sb_1", "--models", "haiku55", "--out", str(tmp_path / "x")]) == 2
    assert "--final" in capsys.readouterr().out


def test_agent_estimate_prices_earlier_runs_and_caps_the_worst_case(capsys):
    cfg = models.get("sonnet55")
    todo = [(cfg, "01_sales_log", "agent_xlsx", 0)] * 4
    expected, ceiling, lines = api_agent.estimate(todo, max_call_usd=0.5)
    assert 0 < expected <= ceiling == 2.0 and any("expected cost" in l for l in lines)
    assert api_agent.main(["--sample", "--models", "sonnet55", "--estimate-only", "--out", "/tmp/_unused_agent_est"]) == 0
    assert "worst case" in capsys.readouterr().out


def test_agent_rejects_providers_it_does_not_implement(capsys):
    models.register_openweight("ow_agent", "acme/open-1", 0.3, 0.9)
    assert api_agent.main(["--models", "ow_agent", "--sample", "--estimate-only"]) == 2
    assert "Anthropic and OpenAI" in capsys.readouterr().out


def test_openai_agent_backend_resends_history_with_reasoning_and_tool_outputs():
    cfg = ModelCfg("oai_agent", "openai", "gpt-test", 1.0, 4.0, max_tokens=1000, effort="medium",
                   prompt_caching="automatic (cannot be disabled); priced uncached")

    def resp(output, text="", inp=500, out=50):
        usage = SimpleNamespace(input_tokens=inp, output_tokens=out, input_tokens_details=SimpleNamespace(cached_tokens=100),
                                output_tokens_details=SimpleNamespace(reasoning_tokens=20), model_dump=lambda: {})
        return SimpleNamespace(status="completed", usage=usage, output=output, output_text=text, model="gpt-test-1",
                               _request_id="r")

    class Fake:
        def __init__(self):
            self.requests, self.responses = [], self
            self.script = [resp([SimpleNamespace(type="reasoning", id="rs_1"),
                                 SimpleNamespace(type="function_call", call_id="c1", name="bash",
                                                 arguments='{"command": "echo hi"}')]),
                           resp([SimpleNamespace(type="message", content=[SimpleNamespace(type="output_text")])], '{"q1": 2}')]

        def create(self, **kw):
            self.requests.append({**kw, "input": list(kw["input"])})
            return self.script.pop(0)

    client = Fake()
    with agentmod.Sandbox({}) as sb:
        run = agentmod.run_agent(cfg, agentmod.get_agent(cfg, OpenAIProvider(client)), AGENT_SYSTEM, "u", sb)
    assert run.result.text == '{"q1": 2}' and len(run.turns) == 2
    assert run.result.usage.cache_read_tokens == 200 and run.result.usage.input_tokens == 800     # cached split out, summed
    req2 = client.requests[1]
    assert req2["store"] is False and req2["include"] == ["reasoning.encrypted_content"] and req2["reasoning"] == {"effort": "medium"}
    kinds = [i.get("type") for i in req2["input"] if isinstance(i, dict)]
    assert kinds == [None, "reasoning", "function_call", "function_call_output"]
    assert req2["input"][-1]["output"].strip() == "hi"
    assert req2["tools"][0]["type"] == "function" and req2["tools"][0]["name"] == "bash"


# ---- 7. open-weight provider ----------------------------------------------------------------------------------

def compat_response(text="{}", finish="stop", prompt_tokens=1200, cached=200, completion=300, reasoning=100, refusal=None):
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion,
                            prompt_tokens_details=SimpleNamespace(cached_tokens=cached),
                            completion_tokens_details=SimpleNamespace(reasoning_tokens=reasoning),
                            model_dump=lambda: {"prompt_tokens": prompt_tokens})
    choice = SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=text, refusal=refusal))
    return SimpleNamespace(choices=[choice], usage=usage, model="acme/open-1", id="chatcmpl-1")


class FakeChat:
    def __init__(self, reply):
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.reply = reply

    def create(self, **kw):
        self.requests.append(kw)
        return self.reply


def test_openweight_alias_parses_and_prices_from_the_command_line_form():
    cfg = models.register_from_arg("llama=meta-llama/Llama-4-70B,0.6,0.9")
    assert (cfg.provider, cfg.model_id, cfg.price_in, cfg.price_out) == ("openai_compat", "meta-llama/Llama-4-70B", 0.6, 0.9)
    assert models.price_for("meta-llama/Llama-4-70B") == (0.6, 0.9)
    with pytest.raises(SystemExit):
        models.register_from_arg("broken")
    with pytest.raises(SystemExit, match="already exists"):
        models.register_from_arg("llama=x,1,1")


def test_compat_provider_normalises_usage_and_sends_no_sampling_parameters():
    cfg = models.register_openweight("ow", "acme/open-1", 0.3, 0.9)
    client = FakeChat(compat_response('{"q1": 1}'))
    res = OpenAICompatProvider(client).complete(cfg, "sys", "usr")
    body = client.requests[0]
    assert body == {"model": "acme/open-1", "max_tokens": 32000,
                    "messages": [{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}]}
    assert (res.usage.input_tokens, res.usage.cache_read_tokens, res.usage.output_tokens, res.usage.reasoning_tokens) == (1000, 200, 300, 100)
    assert call_cost(cfg, res.usage) == pytest.approx((1200 * 0.3 + 300 * 0.9) / 1e6)
    assert res.raw_usage["tokenizer_input_tokens"] is None and cfg.settings()["prompt_caching"].startswith("host-dependent")
    with pytest.raises(Truncated):
        OpenAICompatProvider(FakeChat(compat_response(finish="length"))).complete(cfg, "s", "u")
    with pytest.raises(CallError, match="refused"):
        OpenAICompatProvider(FakeChat(compat_response(finish="content_filter"))).complete(cfg, "s", "u")


def test_compat_provider_needs_an_endpoint_and_runs_through_api_run(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit, match="CELLPROSE_COMPAT_BASE_URL"):
        OpenAICompatProvider(env={})
    client = FakeChat(compat_response())
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: OpenAICompatProvider(client))
    assert api_run.main(["--openweight", "ow2=acme/open-1,0.3,0.9", "--models", "ow2", "--workbooks", "03_pnl_quarterly",
                         "--encs", "csv", "--out", str(tmp_path)]) == 0
    (raw,) = read_raw(tmp_path, "ow2").values()
    assert raw["provider"] == "openai_compat" and raw["run"]["price_in_per_mtok"] == 0.3
    assert raw["run"]["returned_model"] == "acme/open-1" and raw["run"]["settings"]["prompt_caching"].startswith("host")


# ---- OpenRouter (open-weight models) -------------------------------------------------------------------------

def or_response(text="{}", **kw):
    r = compat_response(text, **kw)
    r.provider = "Fireworks"
    r.model_extra = {"provider": "Fireworks"}
    r.usage.model_dump = lambda: {"prompt_tokens": 1200, "cost": 0.0009}
    return r


def test_openrouter_registry_entries_are_pinned_and_explicit():
    ors = [c for c in models.REGISTRY.values() if c.provider == "openrouter"]
    assert len(ors) >= 3
    for cfg in ors:
        assert not cfg.model_id.startswith("~")                                  # no moving alias
        assert ":" not in cfg.model_id or cfg.model_id.endswith(":free")         # no :batch or other routing suffix
        assert cfg.extra["reasoning"]["effort"] and cfg.extra["provider"]["require_parameters"]
        assert cfg.settings()["extra"] == cfg.extra and cfg.price_in > 0 and cfg.price_out > 0


def test_openrouter_request_asks_for_usage_and_passes_routing_and_reasoning():
    cfg = models.get("or_dsv4pro")
    body = OpenRouterProvider.request(cfg, "sys", "usr")
    assert body["model"] == "deepseek/deepseek-v4-pro" and body["max_tokens"] == 32000
    assert body["extra_body"]["usage"] == {"include": True} and body["extra_body"]["reasoning"] == cfg.extra["reasoning"]
    assert "temperature" not in body


def test_openrouter_host_pinning_forbids_fallback_and_is_recorded():
    models.pin_openrouter_hosts(["Fireworks", "Together"])
    cfg = models.get("or_kimik26")
    routing = OpenRouterProvider.request(cfg, "s", "u")["extra_body"]["provider"]
    assert routing == {"require_parameters": True, "order": ["Fireworks", "Together"], "allow_fallbacks": False}
    assert cfg.settings()["extra"]["provider"]["allow_fallbacks"] is False


def test_openrouter_call_records_upstream_host_and_charge_and_needs_a_key():
    with pytest.raises(SystemExit, match="OPENROUTER_API_KEY"):
        OpenRouterProvider(env={})
    cfg = models.get("or_gptoss120")
    client = FakeChat(or_response())
    res = OpenRouterProvider(client).complete(cfg, "s", "u")
    assert res.raw_usage["upstream_provider"] == "Fireworks" and res.raw_usage["openrouter_cost_usd"] == 0.0009
    assert call_cost(cfg, res.usage) == pytest.approx((1200 * 0.037 + 300 * 0.17) / 1e6)
    assert client.requests[0]["extra_body"]["usage"] == {"include": True}


def test_openrouter_empty_body_is_a_recordable_failure_not_a_crash():
    bad = SimpleNamespace(choices=[], usage=None, model="x", id="1", error={"code": 502})
    with pytest.raises(ApiFailure) as e:
        OpenRouterProvider(FakeChat(bad)).complete(models.get("or_glm51"), "s", "u")
    assert recordable(e.value)


def test_openrouter_models_run_through_api_run_and_agent_mode_rejects_them(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(api_run, "get_provider", lambda cfg: OpenRouterProvider(FakeChat(or_response('{"q1": 1}'))))
    assert api_run.main(["--models", "or_dsv4pro", "--workbooks", "03_pnl_quarterly", "--encs", "csv",
                         "--openrouter-hosts", "Fireworks", "--out", str(tmp_path)]) == 0
    (raw,) = read_raw(tmp_path, "or_dsv4pro").values()
    assert raw["provider"] == "openrouter"
    assert raw["run"]["settings"]["extra"]["provider"]["order"] == ["Fireworks"]
    capsys.readouterr()
    assert api_agent.main(["--models", "or_dsv4pro", "--sample", "--estimate-only"]) == 2


# ---- 8. vendor tokenizer counts next to billed usage -----------------------------------------------------------

def test_anthropic_call_stores_its_own_token_count_and_survives_a_counting_error():
    cfg = models.get("haiku55")
    res = AnthropicProvider(FakeClient(message(inp=1010))).complete(cfg, "s", "u")
    assert res.raw_usage["tokenizer_input_tokens"] == 1000 and res.raw_usage["tokenizer"] == "anthropic count_tokens"
    assert res.usage.input_tokens == 1010          # billed usage is kept separately

    class NoCount(FakeClient):
        def count_tokens(self, **kw):
            raise RuntimeError("rate limited")

    res = AnthropicProvider(NoCount(message())).complete(cfg, "s", "u")
    assert res.raw_usage["tokenizer_input_tokens"] is None and res.text == "{}"


def test_openai_call_stores_the_o200k_count_under_the_common_key():
    from test_runner import FakeOpenAI, OAI, oai_response
    res = OpenAIProvider(FakeOpenAI(oai_response())).complete(OAI, "s", "u")
    assert res.raw_usage["tokenizer"].startswith("o200k_base") and "tokenizer_input_tokens" in res.raw_usage
    assert res.raw_usage["tokenizer_input_tokens"] == res.raw_usage["tokenizer_input_tokens_o200k"]


def test_estimate_only_for_openrouter_works_without_a_key_using_a_character_estimate(monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert api_run.main(["--models", "or_gptoss120", "--sample", "--estimate-only"]) == 0
    out = capsys.readouterr().out
    assert "estimated from characters" in out and "expected cost" in out


def test_agent_cost_applies_the_long_prompt_rate_per_turn_not_to_the_summed_usage():
    """Three 60k-token turns on Haiku 5.5 are each under its 100k threshold, so none pays the long rate even though
    the summed input is 180k."""
    cfg = models.get("haiku55")
    script = [tool_message([{"command": "true"}], inp=60_000, out=100), tool_message([{"command": "true"}], inp=60_000, out=100),
              final_message('{"q1": 1}', inp=60_000, out=100)]
    with agentmod.Sandbox({}) as sb:
        run = agentmod.run_agent(cfg, agentmod.get_agent(cfg, AnthropicProvider(ScriptedClient(script))), "s", "u", sb)
    assert run.result.cost == pytest.approx(3 * (60_000 * 0.10 + 100 * 0.50) / 1e6)
    assert call_cost(cfg, run.result.usage) > 4 * run.result.cost        # the wrong (summed) pricing, for contrast
    raw = build_raw(cfg, "03_pnl_quarterly", "agent_xlsx", "u", run.result, {})
    assert raw["cost"] == pytest.approx(run.result.cost)
    assert raw["run"]["long_prompt_tier"] == {"threshold": 100_000, "price_in": 0.5, "price_out": 2.5}


def test_v03_is_the_default_cellprose_text_everywhere():
    """Owner's decision (Oct 27, 2026): new runs compare the shipped v0.3 text; v0.2 stays available for old runs."""
    from runner.prompts import AGENT_FILES
    RAW = Path(api_agent.__file__).parent / "results" / "raw"
    assert api_run.SAMPLE_ENCS == ["csv", "cellprose_v03"]
    assert api_agent.DEFAULT_VARIANTS == ["agent_xlsx", "agent_cellprose_v03"]
    assert "agent_sheetmark" in api_agent.VARIANTS and "agent_sheetmark" not in api_agent.DEFAULT_VARIANTS
    assert AGENT_FILES["agent_cellprose_v03"] == ("book.sheet.md", "encoded", "{wb}.cellprose_v03.txt")
    tin, tout, _ = api_agent.historic_tokens("agent_cellprose_v03", RAW)
    base_in, base_out, _ = api_agent.historic_tokens("agent_sheetmark", RAW)
    assert tin < base_in and tout == base_out


def test_view_xlsx_shows_formulas_next_to_cached_values_and_lists_sheets():
    wb = Path(api_agent.__file__).parent / "workbooks" / "04_saas_model.xlsx"
    listing = agentmod.view_xlsx(wb)
    assert listing and all(": " in line for line in listing.splitlines())
    sheet = listing.splitlines()[0].split(": ")[0]
    bodies = [agentmod.view_xlsx(wb, line.split(": ")[0]) for line in listing.splitlines()]
    assert any(" = =" in b and " -> " in b for b in bodies)      # a formula line carries its cached value
    assert "error: no sheet" in agentmod.view_xlsx(wb, "Nope")
    one = agentmod.view_xlsx(wb, sheet, "A1:A1")
    assert len(one.splitlines()) <= 1


def test_viewer_variant_offers_view_xlsx_only_to_its_own_calls(tmp_path, provider):
    wb = "03_pnl_quarterly"
    script = []
    for _ in range(2):          # agent_xlsx, then agent_xlsx_viewer: one tool turn each, then the answer
        script += [tool_message([{"sheet": ""}], name="view_xlsx"), final_message(truth_json(wb))]
    client = provider(ScriptedClient(script))
    rc = api_agent.main(["--workbooks", wb, "--models", "haiku55", "--variants", "agent_xlsx,agent_xlsx_viewer",
                         "--out", str(tmp_path), "--workers", "1"])
    assert rc == 0
    tools = [{t["name"] for t in r["tools"]} for r in client.requests]
    assert {"bash", "read_file"} in tools and {"bash", "read_file", "view_xlsx"} in tools
    raws = read_raw(tmp_path)
    assert set(raws) == {f"{wb}.agent_xlsx.json", f"{wb}.agent_xlsx_viewer.json"}
    viewer = raws[f"{wb}.agent_xlsx_viewer.json"]
    assert viewer["tool_trace"][0]["tool"] == "view_xlsx" and viewer["tool_trace"][0]["output_chars"] > 0
    (manifest,) = (tmp_path / "runs").glob("*.json")
    files = json.loads(manifest.read_text())["inputs"]["files"]
    assert f"workbooks/{wb}.xlsx" in files and not any(k.startswith("encoded/") for k in files)


def test_old_ids_resolve_to_the_renamed_ones():
    """The Nov 2026 rename keeps E28-E32 raw results scorable: old ids map to the same texts under new names."""
    from runner.ids import canon
    assert canon("sheetmark_v03") == "cellprose_v03_nolegend" and canon("sheetmark_v031") == "cellprose_v03"
    assert canon("agent_sheetmark_v031") == "agent_cellprose_v03" and canon("csv") == "csv"
    from runner.prompts import AGENT_FILES, agent_source
    assert agent_source("01_sales_log", "agent_sheetmark_v031") == agent_source("01_sales_log", "agent_cellprose_v03")
    assert "agent_cellprose_v03_nolegend" in AGENT_FILES


def test_preflight_check_flags_missing_arms_failures_wrong_models_and_no_cache_reads(tmp_path):
    import preflight

    def raw(model, enc, provider="anthropic", failed=False, returned=None, turns=0, cache_read=0):
        d = {"model": model, "encoding": enc, "provider": provider, "num_turns": turns,
             "usage": {"cache_read_input_tokens": cache_read},
             "run": {"requested_model": "m-1", "returned_model": returned or "m-1"}}
        if failed:
            d.update(failed=True, failure={"kind": "truncated", "message": "hit max_tokens"})
        path = tmp_path / "raw" / model / f"01_sales_log.{enc}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d))

    arms = preflight.ONE_SHOT.split(",") + preflight.AGENT.split(",")
    for m in preflight.MODELS.split(","):
        for arm in arms:
            raw(m, arm, turns=5 if arm.startswith("agent_") else 0, cache_read=900)
    assert preflight.check(tmp_path) == []
    raw("haiku55", "agent_xlsx", turns=5, cache_read=0)
    raw("sonnet55", "csv", failed=True)
    raw("gpt6luna", "csv", provider="openai", returned="gpt-5")
    (tmp_path / "raw" / "gpt61sol" / "01_sales_log.markitdown.json").unlink()
    (tmp_path / "runs").mkdir()
    (tmp_path / "runs" / "r.infra.jsonl").write_text(json.dumps({"model": "gpt61sol", "arm": "markitdown",
                                                                 "message": "insufficient_quota"}) + "\n")
    problems = "\n".join(preflight.check(tmp_path))
    for part in ["haiku55/agent_xlsx: 5 turns and no cache reads", "sonnet55/csv: failed (truncated",
                 "gpt6luna/csv: asked for m-1, got gpt-5", "gpt61sol/markitdown: no result", "insufficient_quota"]:
        assert part in problems


def test_whole_number_answers_must_match_exactly_and_others_keep_the_tolerance():
    import score
    q = {"type": "lookup", "cell": "S!A1", "truth": 8002468}
    assert score.score(q, 8002468)["score"] == 1 and score.score(q, "8,002,468")["score"] == 1
    assert score.score(q, 8002469)["score"] == 0 and score.score(q, 8030000)["score"] == 0
    assert score.score({**q, "truth": 2274}, 2275)["score"] == 0
    assert score.score({**q, "truth": 289.585892115731}, 289.6)["score"] == 1        # 0.5% still applies
    assert score.score({**q, "truth": 0}, 0.004)["score"] == 1


def test_array_formulas_hash_the_same_on_every_load(tmp_path):
    import openpyxl
    from openpyxl.worksheet.formula import ArrayFormula
    import freeze
    wb = openpyxl.Workbook()
    wb.active["A1"], wb.active["A2"] = 1, 2
    wb.active["B1"] = ArrayFormula("B1:B2", "=A1:A2*2")
    wb.save(tmp_path / "a.xlsx")
    assert freeze.cell_sha256(tmp_path / "a.xlsx") == freeze.cell_sha256(tmp_path / "a.xlsx")


def test_spreadsheetbench_drops_leave_111_questions_and_restate_the_request_on_the_first():
    sb = BENCH / "external" / "spreadsheetbench" / "questions"
    if not sb.exists():
        pytest.skip("SpreadsheetBench set not built (CC BY-SA, not in git)")
    files = {p.stem: json.loads(p.read_text()) for p in sb.glob("*.json")}
    assert len(files) == 28 and sum(len(q) for q in files.values()) == 111
    assert not {"sb_56786", "sb_52964"} & set(files) and "sb_54925" in files
    for qs in files.values():
        assert [q["id"] for q in qs] == [f"q{i}" for i in range(1, len(qs) + 1)]
        assert qs[0]["q"].startswith("A user asked:") and all(q["q"].startswith("Same request as q1") for q in qs[1:])


def test_addendum_noimpact_drops_only_impact_rows(tmp_path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))
    import addendum_noimpact
    import pandas as pd
    run = tmp_path / "run"
    (run / "raw").mkdir(parents=True)
    pd.DataFrame({"rep": ["r0"] * 3, "model": ["m"] * 3, "workbook": ["w"] * 3, "encoding": ["e"] * 3,
                  "qid": ["q1", "q2", "q3"], "task": ["lookup", "impact", "trace"], "score": [1.0, 1.0, 0.0]}
                 ).to_csv(run / "scores.csv", index=False)
    out = addendum_noimpact.main(str(run))
    kept = pd.read_csv(out / "scores.csv")
    assert list(kept.task) == ["lookup", "trace"]
    assert (out / "raw").resolve() == (run / "raw").resolve()


def test_addendum_freeze_covers_the_benchmark_freeze_and_the_tools():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks"))
    import freeze
    import freeze_addendum
    names = {p.name for p in freeze_addendum.paths()}
    assert set(map(str, freeze.paths())) <= set(map(str, freeze_addendum.paths()))
    assert {"PROTOCOL_ADDENDUM.md", "tools.py", "addendum_noimpact.py", "freeze_addendum.py"} <= names
