# Cellprose benchmark protocol

Frozen 11 Nov 2026, before any call of the benchmark run. This document says how the benchmark is run, scored and reported, so the result does not depend on choices made after seeing the numbers. Any change after the run starts is a deviation and is listed in the write-up.

The format, prompt, runner and scorer were developed on separate development workbooks (section 3). The benchmark workbooks and questions were not used for that.

## 1. Question

For each model, does Cellprose v0.3 let the model answer questions about a workbook correctly for less money than the tools a user would otherwise reach for?

| Role | Arm | What it is | Runner |
| --- | --- | --- | --- |
| Compared | `cellprose_v03` | The v0.3 writer's text (`src/cellprose/writer.py`, `docs/SPEC.md`, including the row-number legend of section 3.1), sent in the prompt | `api_run.py` |
| Primary baseline | `markitdown` | Microsoft MarkItDown 0.1.7's own output for the `.xlsx`, sent in the prompt | `api_run.py` |
| Primary baseline | `agent_xlsx` | The `.xlsx` on disk and an agent with `bash` and `read_file` tools (python3 and openpyxl available), exploring until it answers | `api_agent.py` |
| Primary baseline | `agent_xlsx_viewer` | `agent_xlsx` plus a `view_xlsx` tool that prints each cell's formula next to its cached value, as the agents in SpreadsheetBench 2 get, so a win cannot be put down to a plain shell being a weak baseline | `api_agent.py` |
| Reference | `csv` | Sheet-per-section CSV, sent in the prompt | `api_run.py` |
| Reported, not tested | `agent_cellprose_v03` | The Cellprose text as a file, read through the same agent tools | `api_agent.py` |
| Control | `none` | The questions without the workbook. It shows how much can be guessed; it is not compared, but its accuracy is shown beside every arm's (section 10) | `api_run.py` |

**Caveat on the agent baselines:** a one-shot call and an agent loop spend tokens differently (the loop re-reads a growing context every turn). The comparison is on cost per correct answer, which is what a user pays, but a win over an agent says nothing about which of the two reads a workbook better at equal cost.

## 2. Metric

The headline metric is **cost per correct answer**, per model:

```
cost per correct = mean cost per call / mean accuracy
cost per call    = (all input tokens × input price + all output tokens × output price) / 1e6
```

- Output tokens include reasoning tokens.
- Every input token is priced as **uncached input**, whatever the provider reports. Prices come from `runner/models.py` as frozen and are recorded with every call.
- Accuracy is the mean question score (section 6).
- Also reported per model and arm: accuracy, input tokens, output tokens, and cost per call.

## 3. Data

| Corpus | What it is | Size |
| --- | --- | --- |
| Real-world (`rw2_`) | 15 Damodaran valuation workbooks and 15 formula-heavy workbooks from the Enron corpus (figshare 1221767, CC BY 4.0), one per author | 30 workbooks, 163 questions |
| SpreadsheetBench (`sb_`) | Cell-level tasks from SpreadsheetBench verified_400, restated as value questions by `external/spreadsheetbench.py` | 28 workbooks, 111 questions |

- **No `rw2_` question is written by hand.** `benchmarks/external/realworld2.py` picks workbooks from a seeded draw and questions by fixed rules: per workbook 1 lookup, 1 address, 2 trace, 1 impact and 1 hardcode question. Ground truth comes from the file: cached values, direct precedents, a LibreOffice recalculation for impact, and typed numbers for hardcode.
- **Exclusion list.** Each build script has an exclusion list (`EXCLUDE`): generated questions that are not part of the set, each with its reason. The set is exactly the rules' output minus that list, so it can be rebuilt and checked against the freeze manifest.
- **Development data** (synthetic workbooks from `gen_workbooks.py` and `gen_hard.py`, and other real-world sets) may be used to tune the format, prompt and runner. It is listed in `benchmarks/split.json`; every `rw2_` and `sb_` workbook is held out.
- `api_run.py` and `api_agent.py` refuse a held-out workbook unless `--final` is passed, and `--final` refuses a working tree with uncommitted changes.
- **Where the data lives.** The Enron workbooks (CC BY 4.0) are in the repository. The SpreadsheetBench-derived files are CC BY-SA 4.0 and are published separately under that licence. The Damodaran files carry no licence and are not redistributed: `realworld2.py fetch` downloads each `.xls` from Damodaran's public site, checks it against the SHA-256 recorded at the freeze, converts it to `.xlsx` with LibreOffice and checks that the result has the frozen content (`cell_sha256`: every cell's formula, value, cached value, number format and comment, plus merges, validation and names). A conversion never gives the same bytes twice, so these 15 workbooks are frozen by content; every other file is frozen by its bytes (section 9).

## 4. Models and settings

Four models, two per vendor: `haiku55` (Claude Haiku 5.5), `sonnet55` (Claude Sonnet 5.5), `gpt6luna` (GPT-6 Luna) and `gpt61sol` (GPT-6.1 Sol). Each is a pinned alias in `runner/models.py` with an exact model ID, list price, `max_tokens`, and an explicit thinking or effort setting. Temperature is left at the provider default. Some model IDs have no dated snapshot, so the run is tied to its date. Results are reported **per model** and never pooled across models.

On the day of the run the owner checks these prices against the vendors' pricing pages and passes the date to every invocation (`--prices-checked YYYY-MM-DD`, required with `--final`), which records it in the run manifest. A price that differs from the frozen one is a deviation: the metric keeps the frozen prices, and the write-up also gives each ratio at the new prices. Cost is computed per request (per turn in agent mode), including long-prompt rates where a vendor has them.

## 5. Procedure

1. **Prompt.** Every call uses `runner/prompts.py` unchanged: the same system prompt and rules for every arm. Only the workbook block and its format label differ. All questions for a workbook go in one call, and the answer is one JSON object. Agent mode uses `AGENT_SYSTEM` and `agent_prompt` in the same file: the same questions and answer rules, with the workbook named as a file.
2. **One invocation per runner and corpus.** For each corpus, all one-shot arms (including `none`) run in one `api_run.py` invocation and all agent arms in one `api_agent.py` invocation, each with one run id. All four invocations start the same day, from the same commit, with the same settings, and form one run: the one-shot and agent invocations of a corpus are compared with each other. Results from any other invocation (an earlier pilot, another day) are never compared with them, even for the same model, and the two corpora are reported separately, never pooled.
3. **Repeats.** Three repeats (`--reps 3`) for every arm, `none` included, repeat-major, so a provider change mid-run hits every arm alike.
4. **Caching.** Caching changes what is billed, not what the model sees or answers, and the metric (section 2) prices every token as uncached whatever was cached. Anthropic agent turns use automatic prompt caching (5-minute TTL), because an agent call re-sends its growing conversation every turn; Anthropic one-shot calls send no `cache_control`, and any cache read or write there is an error. OpenAI caches automatically and cannot be turned off. Cached tokens are recorded, and the amount actually billed is reported beside the metric, never in its place.
5. **Recorded per call:** requested and returned model ID, settings, prices used, raw usage, cost, run id, git commit, dirty-tree flag, and the SHA-256 of the prompt sent. Each run writes `<out>/runs/<run id>.json` with how it was invoked and the SHA-256 of every input it can send. Next to billed usage, each Anthropic call stores the `count_tokens` count and each OpenAI call the `o200k_base` count, so a saving can be checked against each vendor's own tokenizer. Agent mode records every turn's tokens and the commands run, at most 40 turns and $1 of list-price spend per call.
6. **Failures.** A call that errors is retried by the SDK (3 retries). A call that still fails is one of two kinds:
   - **The model's failure:** truncated at `max_tokens`, refused, every turn used without a final answer, the per-call spend cap reached, or a request the API rejects as invalid. It is recorded, scores 0 on every question, and its tokens count toward cost. Failures are listed per model and arm in the write-up.
   - **An infrastructure failure**, which says nothing about the model: no network after the retries, a timeout, a bad key, no credit or quota, a rate limit, an overload, or a server error (HTTP 401, 402, 403, 408, 409, 429 or 5xx, or an error that names credit, billing, quota or a spend limit). It is not recorded, so the call stays to do. It is logged in `<out>/runs/<run id>.infra.jsonl` with what the attempt spent; that spend counts toward the vendor cap but not toward the metric, and the log's total is reported in the write-up.
7. **Resuming.** A run whose calls are not all recorded is continued with the same command plus `--resume <run id>`. It keeps the run id and makes only the calls with no record on disk; a recorded failure is done and is not retried. The runner refuses to resume when the commit, the dirty-tree flag, the settings or the inputs differ from the run's start, or when the run started more than 48 hours earlier; such a run is incomplete (section 8). Every resume is logged in `<out>/runs/<run id>.json`, and the write-up lists them.

## 6. Scoring

Scoring is `score.py`:

- The **last** JSON object in the reply whose keys start with `q` is the answer. A missing or unparsable answer scores 0.
- **Value questions:** a whole-number answer (an ID, a count, a typed integer) must match within 0.01; any other number matches within 0.5% relative or 0.01 absolute, whichever is larger. Strings match case-insensitively after trimming.
- **Address questions:** the set of cells must match exactly.
- **List questions** (trace, impact, hardcode): F1 between the expanded cell sets. When the truth is empty, an empty answer scores 1 and a missing answer 0. A quoted sheet name such as `'Original OBA''s'!X` is read as the sheet `Original OBA's`.

## 7. Statistics

- **Unit:** one call (model × arm × workbook × repeat). Calls for the same workbook and repeat are paired across arms.
- **Interval:** a 95% interval for the ratio *Cellprose cost per correct / baseline cost per correct*, per model, per baseline and per corpus, from a paired bootstrap that resamples workbooks (10,000 resamples, seed 20261009, percentile interval; repeats are averaged within a workbook first). Accuracy differences get the same treatment. `stats.py` computes it; `analyze.py` prints it and saves `verdicts.json`.
- **A win** is an interval for the ratio entirely below 1 **and** Cellprose accuracy no more than 1 point below the baseline. **A loss** is an interval entirely above 1. Anything else is **no difference**.
- Every model is reported as a win, loss or no difference against each baseline. No model is left out, and no claim is made across models.
- A ratio is infinite when a side answers nothing correctly; such a side counts as a loss for that side.

| Result | Allowed wording |
| --- | --- |
| A win | "On N held-out workbooks, Cellprose cost X% less per correct answer than [baseline] (95% CI a to b) with [model]", always per model and per corpus |
| No difference | "About as accurate, at similar cost", per model |
| Never | A result pooled across models; "beats every format"; any claim about a model not run; a token saving quoted without accuracy next to it |

## 8. Cost and spending

- `api_run.py --estimate-only` and `api_agent.py --estimate-only` print the expected cost and the worst case before any call. The owner approves the run with the exact figure. The planned cap is **$350** for the whole run.
- **Preflight.** Before the run, `benchmarks/preflight.py` makes one call per model and arm on one development workbook, in its own results directory, and checks that every key works and has credit, every arm returns a result, the returned model is the one requested, and Anthropic agent turns read from the cache. The run starts only after it passes. Its results are not part of the benchmark.
- `--vendor-cap-usd` stops new calls once a vendor's spend reaches the cap, and five infrastructure failures in a row from one vendor stop new calls to it. Either way the run can be resumed (section 5.7) once the cause is fixed and, for a cap, the owner approves more. A run that cannot be completed within its resume window is incomplete and is not published; it is redone under a new run id.
- **Scope cuts** are allowed only before the run starts, and each is stated in the write-up: fewer models (at least one cheap and one top model per vendor), agent arms at two repeats, or a fixed random subset of workbooks drawn with a recorded seed. `cellprose_v03`, `markitdown`, `agent_xlsx` and `agent_xlsx_viewer` are never dropped.

## 9. Freeze

The public repository has its own history, so a commit cannot prove when the protocol was fixed. Instead, `benchmarks/freeze.py` writes `benchmarks/freeze/benchmark.json`: the SHA-256 of this file, the spec, the writer, the encoders, the scorer and analysis code, the runners and preflight check, the lock file, the split, and every question and workbook file of both corpora (the Damodaran workbooks by content, as `<path>#cells`; section 3), plus one digest over them (the SHA-256 of the lines `<path> <sha256>\n` sorted by path). The owner posts the digest in a public, dated gist before the run, and the write-up cites it. Anyone can recompute it from the repository and the data of section 3.

## 10. Reporting

The write-up (`benchmarks/RESULTS.md`) contains:

- method (this document and the posted digest), models with exact IDs and prices, run ids, and dates;
- per model and corpus: the table of section 2 for every arm, the cost-per-correct ratio with its interval, and the verdict;
- results per question type (lookup, address, trace, impact, hardcode), and agent turns per call;
- the accuracy of the `none` control beside every arm's accuracy, so each figure is read against what can be answered without the workbook;
- the headline chart, one bar per model with its interval;
- failures, scope cuts, and every deviation from this protocol;
- limitations next to the headline number: test-set size, the date prices were checked, the one-shot against agent-loop caveat of section 1, and that savings may differ by tokenizer. The wording lives in `benchmarks/limitations.py`.

Raw responses are committed, except those for SpreadsheetBench-derived inputs (share-alike licence), whose run ids and checksums are committed instead.

## 11. Not covered

- **Batch APIs.** Not used: the runner makes direct calls at list price.
- **Open-weight models.** Not run. The OpenAI-compatible provider stays in the code but is not used.
- **Other formats** in `encoders.ENCODINGS` (Markdown, TOON and others) are not part of this run.
