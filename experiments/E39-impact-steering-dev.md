# E39: impact steering and a lookup tool for the lean agent (development data)

**Status:** partial (2026-11-24). Development data only, exploratory. No frozen file, protocol text or held-out set was touched.

## Question
E37 found the Cellprose-tools agent (`agent_cellprose_lean`) cheaper than the shell agents but short on accuracy for Haiku and Sonnet on impact questions and for Haiku and Luna on address questions. On the real-world set `whatif` was called in 58 of 60 workbook calls by Sol and Luna (impact accuracy 100%) but in only 9 (Sonnet) and 18 (Haiku) of 60. Does steering the model to `whatif`, and a `lookup` tool for "row X, column Y" questions, close the gap?

## Arms (one session, same invocation)
- `agent_cellprose_lean`: control, unchanged.
- `agent_cellprose_lean2s`: adds a system-prompt line ("for a which-cells-would-change question call whatif and answer with the cells it returns") and a sharper `whatif` description.
- `agent_cellprose_lean2`: lean2s plus `lookup(row_label, column_header, sheet)` (`tools.lookup`), which returns candidate intersection cells. Its first candidate matched the truth on 10 of 20 dev address questions.

## Data and run
`dev_e_` (`external/devdata2`, 20 workbooks, 120 questions), 2 repeats, Haiku 5.5, Sonnet 5.5, GPT-6 Luna, GPT-6.1 Sol. Out dir `results/e39_devrun`. Spend $7.82 at list price (Anthropic $5.28, OpenAI $2.54). The Anthropic per-vendor cap of $5 stopped the run: **Sonnet has 25 of 40 calls per arm, 45 calls were not made**. Resume id `20261124T163558Z-52e13f`.

## Results (accuracy %, mean cost per call, turns)
| Model | Arm | All | Impact | Address | Cost/call | Turns |
| --- | --- | --- | --- | --- | --- | --- |
| Haiku | lean | 91.3 | 91 | 68 | $0.0035 | 3.4 |
| Haiku | lean2s | 94.5 | 98 | 80 | $0.0030 | 3.3 |
| Haiku | lean2 | 91.5 | 100 | 65 | $0.0030 | 3.4 |
| Sonnet (25/40 calls) | lean | 92.2 | 96 | 68 | $0.0689 | 3.8 |
| Sonnet (25/40 calls) | lean2s | 87.5 | 96 | 56 | $0.0758 | 4.7 |
| Sonnet (25/40 calls) | lean2 | 91.3 | 100 | 60 | $0.0514 | 3.2 |
| Luna | lean | 86.8 | 100 | 55 | $0.0022 | 3.0 |
| Luna | lean2s | 91.6 | 100 | 70 | $0.0023 | 3.2 |
| Luna | lean2 | 90.5 | 100 | 62 | $0.0017 | 2.9 |
| Sol | lean | 94.0 | 100 | 75 | $0.0192 | 2.5 |
| Sol | lean2s | 94.1 | 100 | 75 | $0.0195 | 2.6 |
| Sol | lean2 | 93.7 | 100 | 72 | $0.0186 | 2.6 |

## What it says (exploratory)
- Steering helps Haiku's impact questions (91 to 98-100) and costs nothing. Sol and Luna were already at 100. Sonnet is incomplete.
- `lookup` did not help address questions (Haiku 65, Sonnet 60 vs 80 and 56 for steering alone); do not ship it as is.
- Address differences between arms are mostly noise at 20 questions per cell and 2 repeats. The address weakness on this set (55-75%) is larger than on the real-world set.
- Changes to accuracy overall are within a few points and the arms differ by single questions; none of this is a held-out result.

## Limitations
Development data, 2 repeats, Sonnet incomplete, Anthropic cap overshot by $0.28. `whatif` shares its method with the impact truth.
