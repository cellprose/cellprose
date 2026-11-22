# Benchmark protocol, addendum A: Cellprose with its own tools

Frozen 11 Nov 2026, before any call of this addendum run. Everything not stated here is as in [PROTOCOL.md](PROTOCOL.md), whose own run is finished and is not changed by this addendum.

## 1. Why there is an addendum

The benchmark run compared Cellprose with agents that read the `.xlsx` (`agent_xlsx`, `agent_xlsx_viewer`) in two ways: Cellprose text sent once in the prompt (`cellprose_v03`), and the Cellprose file read through the same shell tools as the baselines (`agent_cellprose_v03`). It did not include the agent setup built for Cellprose in development (experiment E34): the workbook's index in the first message and Cellprose's own tools, with no shell. This addendum measures that setup against the same two agent baselines.

The decision to run the addendum was made after the benchmark run's results were seen. The arm itself was built and tested on development data only, before the benchmark run (E34, 7 Nov 2026), and its code is unchanged since. The write-up states this next to the addendum's results.

## 2. Question

For each model, does an agent using Cellprose's own tools answer questions about a workbook correctly for less money than an agent that reads the `.xlsx` with a shell?

| Role | Arm | What it is | Runner |
| --- | --- | --- | --- |
| Compared | `agent_cellprose_lean` | The workbook's index (`cellprose.tools.index`) in the first message, then four tools and no shell: `read_range` (one or more A1 ranges, as Cellprose text, without format blocks), `find` (cells containing a text), `trace` (precedents or dependents, as ranges) and `whatif` (change one input cell, recalculate with LibreOffice, list the cells whose value changes). System prompt `runner/prompts.py::LEAN_SYSTEM`. | `api_agent.py` |
| Baseline | `agent_xlsx` | As in PROTOCOL.md section 1 | `api_agent.py` |
| Baseline | `agent_xlsx_viewer` | As in PROTOCOL.md section 1 | `api_agent.py` |

All three arms run in the same session, with the same models, data, turn limit (40 turns) and per-call cap ($1 at list price) as the benchmark run's agent arms. No result from the benchmark run is compared with a result from this addendum.

## 3. Models, data, repeats and prices

- **Models:** Claude Haiku 5.5, Claude Sonnet 5.5, GPT-6 Luna and GPT-6.1 Sol, with the IDs and prices in `runner/models.py`. The prices were checked against the vendors' pricing pages on 2026-11-11.
- **Data:** both corpora of the benchmark run, unchanged: 30 real-world workbooks with 163 questions, and 28 SpreadsheetBench workbooks with 111 questions. They are reported separately.
- **Repeats:** 2 for every arm. This is the scope cut that PROTOCOL.md section 8 allows for agent arms.

## 4. Metric, scoring and verdict

These are as in PROTOCOL.md sections 2, 6 and 7: cost per correct answer, every token priced as uncached at list price, and a paired bootstrap over workbooks with the same seed and number of resamples. A **win** needs the whole interval below 1 and no more than 1 point of accuracy lost. A **loss** needs the whole interval above 1. Anything else is **no difference**.

**Impact questions.** `whatif` uses the same method as the impact ground truth (a LibreOffice recalculation of an openpyxl-saved copy). That makes impact questions close to free for the compared arm. The baselines could run LibreOffice from their shell, but in development they did not. So:

- **Real-world corpus, primary verdict:** impact questions are left out of the accuracy average for every arm. Cost per call is unchanged, because those calls answered all the questions. `addendum_noimpact.py` builds this view from the scored run.
- **Real-world corpus, secondary verdict:** all questions. It is reported beside the primary verdict.
- **SpreadsheetBench:** has no impact questions, so its verdict uses all questions.

## 5. Running

Two invocations of `api_agent.py --final`, one per corpus, each with `--variants agent_cellprose_lean,agent_xlsx,agent_xlsx_viewer --reps 2 --models haiku55,sonnet55,gpt6luna,gpt61sol --prices-checked 2026-11-11`. Results go to `results/addendum_rw2` and `results/addendum_sb`.

Failures, infrastructure failures and resuming are as in PROTOCOL.md section 5, items 6 and 7. Every resume is listed in the write-up.

## 6. Freeze

`benchmarks/freeze_addendum.py` writes `benchmarks/freeze/addendum.json`. It lists every file of the benchmark freeze, plus this document, `src/cellprose/tools.py` (the compared arm's tools), `src/cellprose/writer.py` (already in the benchmark freeze), `benchmarks/addendum_noimpact.py` and itself, with one digest over them, computed the same way as the benchmark digest. The digest is posted in a public, dated gist before the first call.

## 7. Reporting

The addendum's results are a separate section of `benchmarks/RESULTS.md`. They are never merged into the benchmark run's verdict table. The section contains:

- the posted digest and the run ids;
- per model and corpus: each arm's accuracy, tokens, cost and turns, and the primary verdicts, with the real-world all-questions verdict beside;
- accuracy by question type, failures, resumes and spend;
- the statement in section 1 that the addendum was decided after the benchmark run's results were seen;
- the limitations of PROTOCOL.md section 10, plus two more. First, the compared arm has a different system prompt and no shell, so it is a product setup (an agent with Cellprose's tools), not a one-variable change. Second, the impact caveat of section 4.

## 8. Reuse of the held-out data

This is the last new arm tested on these held-out workbooks. Any later change is checked on development data first, then on a new held-out set drawn and frozen before it is run.
