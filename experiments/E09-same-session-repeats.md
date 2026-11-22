# E09: Same-session repeats; session drift found

**Date:** 2026-10-08, 00:20–00:30 IST · **Session:** 2 (repeats `r1`, `r2`) · **Status:** current. These are the numbers in [DESIGN.md](../docs/DESIGN.md) and the website

> **Not comparable with E16/E17.** E09 ran through the Claude CLI; E16 and E17 ran through the direct-API runner, in other invocations, with different prompts overhead and prices. The savings differ (for example Sonnet 5.5: −5% here, −3% in E16), and the bigger models are level on cost in E16. Cite each with its own limits and do not pool them. See the "Benchmark results" section of [DESIGN.md](../docs/DESIGN.md).

## Question

Do the session-1 results hold up with repeats, and with the fixes from [E06](E06-answer-parser-fix.md) and [E07](E07-sheet-prefix-bug.md) in place?

## Setup

| Item | Value |
| --- | --- |
| Formats | `csv`, `markdown`, `toon`, `sheetmark` (v0.1 padded), `sheetmark_lean_gfm` (v0.2 compact, with `Sheet:` prefix) |
| Agent variants | `agent_xlsx`; `agent_sheetmark` (now the v0.2 compact file) |
| Workbooks | All 14 |
| Models | Haiku 5.5 (`claude-haiku-5-5`) and Sonnet 5.5 (`claude-sonnet-5-5`) for `r1` and `r2`; the session-1 `r0` Haiku runs were mostly Haiku 4.5 (`claude-haiku-4-5-20251001`) |
| Repeats | `r1` and `r2`, run in the same session for every format. The compact format and agent-Sheetmark also got a new `r0` in this session |
| Commands | `REP=1 ENCS=csv,markdown,toon,sheetmark,sheetmark_lean_gfm python3 run.py haiku` (and `REP=2`, and Sonnet); `REP=1 python3 run_agent.py haiku` |

## Haiku 4.5 versus Haiku 5.5

Haiku's CSV runs averaged **12,290 output tokens** per task in session 1 and about **2,250** in session 2, on identical prompts. Sonnet's were steady (~650 both times). The raw files show why: most session-1 Haiku calls ran on Haiku 4.5, and every session-2 call ran on Haiku 5.5, which reasons far less on these prompts. Comparing a session-2 run against a session-1 baseline would have overstated Sheetmark's savings 2–3×. That's the source of the early 36–56% figures that were later withdrawn.

**Rule adopted:** only compare runs of the same model from the same session. Every published run does all formats together ([`report.py`](../benchmarks/report.py) uses `r1` and `r2` only), and the API runner ([E13](E13-api-runner-sample.md)) pins the exact model ID of every call and benchmarks Haiku 4.5, Haiku 5.5 and Sonnet 5.5 side by side.

## Results (r1 + r2, cost uncached per [E10](E10-cache-neutral-cost.md), 28 calls per cell)

One-shot, all 14 workbooks, vs CSV:

| Model | Format | Accuracy | Output tokens | Cost per correct answer |
| --- | --- | --- | --- | --- |
| Haiku 5.5 | CSV | 97.4% | — | — |
| Haiku 5.5 | Markdown | 98.3% | −9% | −1% |
| Haiku 5.5 | TOON | 93.1% | +5% | +9% |
| Haiku 5.5 | Sheetmark v0.1 | 99.6% | −30% | −11% |
| Haiku 5.5 | **Sheetmark v0.2** | **98.9%** | **−31%** | **−17%** |
| Sonnet 5.5 | CSV | 98.2% | — | — |
| Sonnet 5.5 | Markdown | 98.8% | 0% | +7% |
| Sonnet 5.5 | TOON | 97.4% | +2% | +3% |
| Sonnet 5.5 | Sheetmark v0.1 | 99.7% | −28% | −1% |
| Sonnet 5.5 | **Sheetmark v0.2** | **99.7%** | **−21%** | **−5%** |

Hard workbooks only: v0.2 is **−26%** on Haiku (99.8% vs 94.1% accuracy) and **−16%** on Sonnet (100% vs 94.6%).

Agent mode, vs raw .xlsx with tools:

| Model | Variant | Accuracy | Turns | Tokens per task | Cost per task |
| --- | --- | --- | --- | --- | --- |
| Haiku 5.5 | Raw .xlsx | 99.8% | 3.3 | 24,900 | $0.0033 |
| Haiku 5.5 | Sheetmark file | 98.9% | 2.5 | 16,600 | $0.0024 |
| Haiku 5.5 | Sheetmark in prompt | 98.9% | 1 | 8,300 | $0.0015 |
| Sonnet 5.5 | Raw .xlsx | 99.7% | 2.8 | 15,200 | $0.036 |
| Sonnet 5.5 | Sheetmark file | 98.8% | 2.4 | 12,400 | $0.028 |
| Sonnet 5.5 | Sheetmark in prompt | 99.7% | 1 | 4,100 | $0.012 |

Accuracy by task, both models (r1 + r2): CSV scored 68% on the typed-in-vs-formula task, Markdown 74%, TOON 75%, and both Sheetmark versions 100%.

## Conclusion

- Sheetmark v0.2 is cheaper and more accurate than CSV on both models, and the margin widens on hard workbooks.
- The saving comes from less reasoning: v0.2 has 13–14% more input but 21–31% less output.
- Agents reading a Sheetmark file lose about 1 point of accuracy against raw .xlsx, on trace and impact questions. This is still open.

## Reproduce

```bash
cd benchmarks && python3 score.py && python3 report.py
```

Raw results: `benchmarks/results/raw/<model>/*.r1.json` and `*.r2.json`.
