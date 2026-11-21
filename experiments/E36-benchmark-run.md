# E36: The benchmark run

**Date:** 11 Nov 2026. **Protocol:** [docs/PROTOCOL.md](../docs/PROTOCOL.md). **Write-up:** [benchmarks/RESULTS.md](../benchmarks/RESULTS.md).

## Question

Does the Cellprose text format let a model answer questions about a spreadsheet correctly for less money than the tools a user would otherwise reach for?

## Setup

- Freeze digest `5239114b960aa3327d7f61db1209886a947ebdaaae90659951bfe19c7a1ce9b2`, posted publicly before the first call ([gist](https://gist.github.com/Utkarsh-Gaikwad/216cc9dc28d31f4cf616f44e77324c82)).
- Code at `716af38`; prices checked 2026-11-11.
- Models: Claude Haiku 5.5, Claude Sonnet 5.5, GPT-6 Luna, GPT-6.1 Sol.
- Arms: `cellprose_v03`, `markitdown`, `csv`, `none`, `agent_xlsx`, `agent_xlsx_viewer`, `agent_cellprose_v03`.
- Repeats: 3.
- Data: the real-world set (30 workbooks, 163 questions) and SpreadsheetBench (28 workbooks, 111 questions).
- Preflight: `results/preflight/20261111/`.

## Results

See [benchmarks/RESULTS.md](../benchmarks/RESULTS.md) for every table, the chart and the limitations.

- **Against MarkItDown:** a win in 7 of 8 model-and-corpus pairs (ratio 0.32–0.60). The eighth, Sonnet on SpreadsheetBench, is no difference: its interval is below 1, but it is 1.1 accuracy points lower.
- **Against CSV:**
  - Real-world: a win for Sonnet and Luna.
  - SpreadsheetBench: a win for Haiku.
  - Everything else is no difference.
- **Against the agent arms:** a win for Sonnet on the real-world set against both. The other 14 comparisons are no difference.
- **Losses:** none.
- **Real-world one-shot accuracy:** 93.8–99.3% with Cellprose, against 65.9–84.1% with CSV.

## Problems found

- **Model failures:** five calls were truncated at `max_tokens` and scored 0. None was a Cellprose call.
- **Credit:** both vendors' credit ran out mid-run.
  - The affected calls were logged as infrastructure failures and resumed under the same run ids: 224 Anthropic calls and 44 OpenAI calls.
  - Both resumes happened within five hours of the start.
- **Stopped process:** the real-world one-shot process was stopped by the 2-hour limit on a background job in this session, and was then resumed.
- **Spend:** $115.22 at list price ($94.22 billed), against an estimate of about $172.

## Raw results

- `benchmarks/results/run_rw2/` holds the raw responses, run manifests, scores and analysis output.
- `benchmarks/results/run_sb/` holds the run manifests, summary, verdicts, analysis output and checksums. Its raw responses are not committed, because the inputs are under a share-alike licence.
- `benchmarks/results/logs/` holds the runner logs.

## Reproduce

See the Reproducing section of [benchmarks/RESULTS.md](../benchmarks/RESULTS.md).
