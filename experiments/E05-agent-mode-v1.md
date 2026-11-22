# E05: Agent mode, first run

**Date:** 2026-10-07 · **Session:** 1 · **Status:** superseded by the repeated agent runs in [E09](E09-same-session-repeats.md)

## Question

Agents often get a file on disk and explore it with tools. How much does that cost compared with giving them Sheetmark, either as a file to explore or as text in the prompt?

## Setup

| Item | Value |
| --- | --- |
| Variants | `agent_xlsx`: the recalculated .xlsx in an empty folder. `agent_sheetmark`: the compact Sheetmark file (draft without `Sheet:` prefix) |
| Tools | Bash and Read; python3 and openpyxl available; max 40 turns ([`run_agent.py`](../benchmarks/run_agent.py)) |
| Workbooks, questions | All 14, same questions and answer rules as one-shot |
| Usage | Summed over every turn |

## Results (session 1, cost uncached)

| Model | Variant | Accuracy | Turns | Tokens per task | Cost per correct answer |
| --- | --- | --- | --- | --- | --- |
| Haiku | Raw .xlsx | 97.1% | 6.1 | 78,400 | — |
| Haiku | Sheetmark file | 91.9% | 4.0 | 61,000 | +8% |
| Sonnet | Raw .xlsx | 100% | 2.5 | 14,900 | — |
| Sonnet | Sheetmark file | 100% | 2.2 | 11,000 | −25% |

For comparison, in the same session the compact Sheetmark text placed directly in the prompt used about 13,700 (Haiku) and 4,000 (Sonnet) tokens per task, in one turn.

## Problems found

- **Haiku invented a sheet name.** It answered with `Sheet1!D15` for a sheet called `Report`, because the draft format wrote the heading as `# Report`, which read like a document title. This led to [E07](E07-sheet-prefix-bug.md).
- **Answers were lost to parsing.** Sonnet printed a corrected second JSON object after its first, and the original parser read neither ([E06](E06-answer-parser-fix.md)).
- **Bills were distorted by caching.** Billed cost included prompt-cache effects; the numbers above use uncached pricing ([E10](E10-cache-neutral-cost.md)).

## Conclusion

- Exploring raw .xlsx with tools is the most expensive path.
- Sheetmark in the prompt is the cheapest.
- A Sheetmark file on disk helped Sonnet but not Haiku in this draft form. The re-run after the fixes is in [E09](E09-same-session-repeats.md).

Raw results: `benchmarks/results/raw/<model>/*.agent_xlsx.json` and, for the draft-format Sheetmark runs, `benchmarks/results/archive_v1/<model>/*.agent_sheetmark.json`.
