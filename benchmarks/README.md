# Benchmarks


> **Naming.** The format was called Sheetmark when these benchmarks ran. Encoding ids (`sheetmark_lean_gfm`, `agent_sheetmark`, …), result files, the encoded texts and the prompts sent to models keep that name on purpose, so that old and new runs stay comparable. Only code that imports the package (`cellprose`), display labels and the runner's environment variables (now `CELLPROSE_*`, formerly `SHEETMARK_*`) were renamed.
Measures how accurately, and at what total cost, models answer questions about spreadsheets given in
different text encodings. The headline metric is **cost per correct answer**: input + output + reasoning
tokens, priced at list rates, divided by accuracy.

## Pipeline

```bash
python3 gen_workbooks.py && python3 gen_hard.py   # 14 synthetic workbooks + question specs
python3 ground_truth.py                            # recalc with LibreOffice; compute answers
python3 encoders.py                                # every encoding -> encoded/
python3 ci_sample.py                                # free: writer token counts vs ci_baseline.json (the CI check; --update after a deliberate change)
python3 api_run.py --sample --models haiku55        # cheap check: 3 workbooks x 2 encodings (API, results/sample/)
RESULTS_DIR=results/sample python3 score.py         # score a sample run without touching results/scores.csv
python3 api_run.py --models haiku45,haiku55,sonnet55   # full one-shot grid via the API (REP=1 for repeats)
python3 api_agent.py --sample --models haiku55 --estimate-only   # agent mode via the API: file on disk + bash/read_file tools
python3 api_run.py --final --subset 10 --models haiku55 ...       # the publishable run: held-out workbooks need --final (docs/PROTOCOL.md)
python3 run.py haiku,sonnet                        # legacy one-shot calls (Claude CLI, no tools)
python3 run_agent.py haiku,sonnet                  # legacy agent mode through the Claude CLI
REP=1 ENCS=csv,cellprose_v03 python3 run.py sonnet   # extra repeats -> *.r1.json
python3 score.py                                   # results/scores.csv, summary.csv
python3 analyze.py                                 # tables, paired-bootstrap verdicts, vendor tokenizer counts
python3 report.py                                  # numbers used in docs/DESIGN.md
```

Requires Python 3 with openpyxl and pandas (`pip install -e ".[bench]"` adds the Anthropic and OpenAI SDKs, `tiktoken` and the pinned `markitdown`), LibreOffice (`soffice`) and Node with `npm install`. `api_run.py` needs `ANTHROPIC_API_KEY`; the legacy runners need the Claude CLI.

## Files

| File | Purpose |
| --- | --- |
| `gen_workbooks.py`, `gen_hard.py` | Build workbooks with formulas; hard set hides logic that can't be guessed from values |
| `ground_truth.py` | Lookup = recalculated value; trace = parsed precedents; impact = perturb input, recalc, diff; hardcode = typed numbers in a range |
| `encoders.py` | CSV, Markdown, Markdown-KV, TOON, Sheetmark variants and `markitdown` (the real MarkItDown converter, version pinned in `pyproject.toml`). `cellprose_v03_nolegend` (then `sheetmark_v03`) is the shipped v0.3 format and the compared encoding for new runs; `sheetmark_lean_gfm` is the v0.2 text, kept for earlier runs |
| `ci_sample.py`, `ci_baseline.json` | Free CI check for writer PRs: token counts of every benchmark workbook against the committed baseline. Costs cost only; accuracy still needs the paid sample above |
| `api_run.py`, `runner/` | Direct-API one-shot runner: pinned model IDs, explicit reasoning settings, no prompt caching, exact model and usage recorded per call. `runner/models.py` is the model registry; `--sample` for cheap checks; refuses to run above `--max-usd` (default 5) |
| `api_agent.py`, `runner/agent.py` | Agent-mode API runner: the workbook is a file, the model has `bash` and `read_file` tools; pinned models, Anthropic prompt caching (priced uncached in the metric), tokens recorded per turn, Claude and OpenAI. Runs model-written commands locally, so use a container |
| `split.json`, `runner/split.py` | Which workbooks are development and which are held out; the `--final` guard and the seeded subset draw |
| `external/realworld.py`, `external/realworld/` | The real-world held-out set: 17 public workbooks and 67 questions (`rw_*`). `spec.json` holds the questions and the rule behind them, `questions/` the ground truth computed from the files, `review.md` what a reviewer read. Run with `CELLPROSE_CORPUS=external/realworld`; `python3 external/realworld.py build` recreates `workbooks/` and `encoded/` (not in git) |
| `stats.py` | Paired bootstrap intervals and the win / loss / no-difference verdict |
| `run.py`, `run_agent.py` | Legacy runners that shell out to the Claude CLI |
| `score.py` | Parses the last JSON object in each reply; F1 for list answers |
| `analyze.py`, `report.py` | Tables, verdicts and tokenizer counts; `report.py` reproduces the design-doc numbers |
| `results/raw/<model>/<workbook>.<encoding>[.rN].json` | Every raw response with usage |
| `results/archive_v1/` | Superseded runs of an earlier compact draft (no `Sheet:` prefix) |

## Protocol

The publishable run follows [docs/PROTOCOL.md](../docs/PROTOCOL.md): test-set split, models, repeats, failure handling, statistics and reporting, fixed before the run.

The protocol and data were frozen before the run, and the digest was posted publicly on 11 Nov 2026: [gist](https://gist.github.com/Utkarsh-Gaikwad/216cc9dc28d31f4cf616f44e77324c82) (`5239114b960aa3327d7f61db1209886a947ebdaaae90659951bfe19c7a1ce9b2`, 146 files). `python3 freeze.py` recomputes it.

## External datasets

Why public spreadsheet benchmarks are not used as they are, and how SpreadsheetBench is adapted: [external/README.md](external/README.md).

## Experiments

Each run of this benchmark is written up in [`../experiments/`](../experiments/), with its results and problems. The current numbers come from [E09](../experiments/E09-same-session-repeats.md).

## Runner notes

- **Pinned models.** `runner/models.py` holds the exact model ID, list price and thinking/effort setting for each alias (`haiku45`, `haiku55`, `sonnet55`). The raw file records the requested and the returned model ID.
- **No prompt caching.** The runner never sends `cache_control`, and a response that reports any cache read or write is treated as an error, not a result. Cost is still priced as uncached input in `analyze.py`.
- **One invocation, one run id.** Every call in an `api_run.py` invocation shares a `run.run_id`. Compare only runs of the same model that share a run id. `--resume <run id>` continues a run under its id (same commit, settings and inputs, within 48 h); `preflight.py` checks keys, credit, every arm and caching before a paid run.
- **Split.** `split.json` lists the development workbooks; every other workbook is held out and needs `--final`, which also refuses a dirty tree. Exploratory runs use development workbooks only.
- **Failures count.** A call that truncates, is refused or is rejected as invalid is written as a failure record and scored 0; its tokens still cost. A resumed run does not retry it. Infrastructure failures (network, key, credit, rate limit, overload, 5xx) are logged in `runs/<run id>.infra.jsonl` and not recorded, so a resume makes the call.
- **Run manifest.** Each run writes `<out>/runs/<run id>.json` with the git state, the SHA-256 of every question and encoded file it can send, and how it was invoked.
- **Open-weight models.** `--openweight alias=model_id,price_in,price_out` registers a model behind an OpenAI-compatible endpoint (`CELLPROSE_COMPAT_BASE_URL`, `CELLPROSE_COMPAT_API_KEY`). None is chosen yet.
- **OpenRouter.** Provider `openrouter` (`OPENROUTER_API_KEY`, optional `OPENROUTER_BASE_URL`) runs open-weight models through OpenRouter's OpenAI-compatible API. Registered aliases: `or_dsv4pro` (deepseek/deepseek-v4-pro), `or_kimik26` (moonshotai/kimi-k2.6), `or_glm51` (z-ai/glm-5.1), `or_gptoss120` (openai/gpt-oss-120b), and two free-tier ones, `or_nemotron_free` (nvidia/nemotron-3-super-120b-a12b:free) and `or_gemma31_free` (google/gemma-4-31b-it:free). The free ones actually cost $0 but are priced here at the paid listing so cost per correct answer stays comparable; they are rate-limited, their hosts may log prompts, and a free listing can disappear, so report them as a separate set and not in a cost headline. Prices are OpenRouter's public list (2026-10-10) and must be rechecked before a run. Each call sends reasoning effort `medium` and `require_parameters`, asks OpenRouter to report its charge, and records the upstream host and that charge in the raw file. `--openrouter-hosts Fireworks,Together` pins the host order and forbids fallback. `--estimate-only` works without a key (character estimate). Tested with fake clients only; **no live OpenRouter call has been made**. Agent mode does not support it.
- **Open-model caveats.** (1) Token counts are whatever OpenRouter reports for the model's own tokenizer, so input tokens are not comparable across models; compare cost per correct answer, not tokens. There is no vendor tokenizer count to cross-check billing. (2) OpenRouter picks the upstream host per call unless pinned, and hosts differ in price, quantisation and context limits, so repeats can differ for reasons that are not the model; pin hosts for the publishable run and report them. (3) Reasoning models spend many output tokens; `est_output_tokens` for these aliases is a placeholder until a sample run measures it. (4) Host caching and rate limits are not controlled; all input is priced uncached. (5) Do not mix these runs with the Claude/GPT runs in one paired comparison across sessions (CLAUDE.md).
- **Cost gate.** The runner prints the expected cost and a worst case before it calls anything, and refuses above `--max-usd`. Raise it only after the owner approves the spend.
- **Sample results** go to `results/sample/` and are scored with `RESULTS_DIR=results/sample`; they are not part of the E09 numbers.

## Known issues

- **Agent mode on the API is untested live.** `api_agent.py` and the OpenAI tool loop are covered by fake-client tests only; its cost estimate uses token averages from the earlier CLI runs. Make a small priced check before relying on it. Open-weight models have no agent mode.
- **LlamaSheets is not a baseline.** The service was retired in August 2026 (see docs/PROTOCOL.md section 1).
- **`results/headline.json` is not committed.** `analyze.py` writes it from every repeat in `results/raw`, which mixes the first-session Haiku 4.5 runs with the same-session Haiku 5.5 runs under one `haiku` label, so it is not a result. The published same-session numbers are `results/headline_r1r2.json` (written by `report.py`, repeats `r1` and `r2` only). Both are reproducible: run `score.py`, then `report.py`. Absolute dollars follow the prices in `runner/models.py` (the committed file was priced at Haiku 4.5 and Sonnet 4.5-era rates before Oct 9); the percentages do not change.
- **Held-out corpus from SpreadsheetBench.** `external/spreadsheetbench.py` now also writes the `markitdown` encoding; it runs after task selection and a task whose conversion fails is dropped and counted in `selection.json`. With the pinned revision no task was dropped for this (29 tasks, 120 questions).
- **Legacy results.** Files under `results/raw/{haiku,sonnet}` came from the CLI; the `haiku` alias covers two different models, so read the model ID in `modelUsage`.
- **Commit ids in older records.** Run manifests and experiment notes cite git commits (for example `716af38`, `eb07a30`) from the private repository this one was cut from, so they do not resolve here. The freeze digests (`benchmarks/freeze/`) depend only on file contents and paths, so they verify from this repository alone.
