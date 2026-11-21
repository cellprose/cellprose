# E21: Format checks (live GitHub, format gaps, agent-mode gap, model ids)

**Date:** 2026-10-11 · **Type:** analysis of existing results, no paid calls · **Status:** done, two items need a public repo

## Question

Five open checks: does the browser extension and the pipe-less layout work on live github.com (A9, A11), are the documented format gaps still true (A14), why do agents lose about 1 point reading the file on disk (A22), and can the Haiku 5.5 and Sonnet 5.5 snapshot ids be recorded (A25)?

## A9 and A11: live github.com, not checked

`github.com/Utkarsh-Gaikwad/sheetmark` is private (an unauthenticated request returns 404), and the session has no way to render Markdown on GitHub without publishing it (`api.github.com/markdown` is blocked here). Nothing was published. What stays open:

1. Put the fixture below in a public gist or repo as `pipeless.sheet.md`.
2. Check that it renders as one table per heading, with the short row `3|Price|45|45|45|45` padded to an empty last cell and `5|` kept as a row.
3. With `viewer/extension` loaded unpacked in Chrome, open the same file and check the extension swaps in its viewer without breaking the page.

````markdown
## A1:F5

#|A|B|C|D|E|F
-|-|-|-|-|-|-
1||Q1|Q2|Q3|Q4|Total
2|Units|1200|1296|1399.68|1511.65|5407.33
3|Price|45|45|45|45
4|Revenue|54000|58320|62985.6|68024.4|243330
5|
````

Local evidence stays as in `format-research.md`: `cmark-gfm` renders it, which is GitHub's parser, but the page itself is unchecked. Do this before the spec changes (A10).

## A14: format gaps

All three are already in SPEC.md §12, and each is true today. The backlog's third gap is stale: loose cells keep their number format since v0.2 (SPEC §8). `tests/test_reader.py::test_known_limits_are_as_the_spec_says` now pins all three, so a change in behaviour has to change the spec.

| Gap | Behaviour today |
| --- | --- |
| Line breaks | CRLF and CR read back as LF |
| Cached formula values | A decoded `.xlsx` has none until a spreadsheet app computes them |
| Loose-cell number formats | Kept |

## A22: agent mode, 1-point gap

Data: the agent rows of `benchmarks/results/scores.csv` (E09), 3 repeats, 14 workbooks, 279 question-repeats per model and variant. The files hold the final answers only, not the tool calls, so *how* the agents read fill ranges cannot be seen. What can be seen:

| Model | Raw .xlsx | Sheetmark file | Gap |
| --- | --- | --- | --- |
| Haiku 5.5 | 99.0% | 98.5% | -0.5 |
| Sonnet 5.5 | 99.8% | 99.0% | -0.9 |

- **Most misses are shared.** `04 q6`, `08 q7` and `10 q6` lose the same points in both variants (the same partial impact lists), so they say nothing about the format.
- **The Sheetmark-only misses are few, and they are not one cause:**
  - `06 q7` (Haiku, 3 repeats at 0.25, 0.25, 0.92): the answer listed only `C11` and missed `I3`, `J3`, `K3` and the totals. The formula `H2:I9 = B2+D2+F2` covers two columns, so `I3` reads `C3+E3+G3` only after shifting; this is the clearest sign of a fill-range reading error.
  - `03 q5` (Sonnet, 2 of 3 repeats): both scored 0. The r1 answer was `C6`, `C7` (the Q2 column) instead of `D6`, `D7` for Q3 EBITDA, whose formula comes from the fill range `B8:E8 = B6-B7`: an off-by-one column shift. The r2 answer was not inspected.
  - `05 q6` (Sonnet, 2 of 3): impact answered as ranges (`Costs!B4:D4`, ...) at 0.91, so some dependent cells were missed.
  - `08 q4` (Haiku, 1 of 3): wrong sheet name (`Sheet1!D12`); `07 q5` (Haiku, 1 of 3): answered `E26:E33` where the truth is `E34`. Neither obviously points at the format.
- **Raw .xlsx has its own misses** that Sheetmark does not (`13_scenario_switch` on Haiku, one repeat at 0 on two questions), which cancels part of the gap.

Reading: the gap is about 9 question-repeats out of 558 and no repeat spread is reported for it. The fill-range hypothesis has support from two workbooks (06, 03), but it is a hypothesis: the transcripts are not kept. It also matches what the skill already warns about (`skills/sheetmark/SKILL.md`: "shift the references by the cell's distance from the first cell").

**What a run would add (not done, paid):** store the tool-call transcript in `benchmarks/api_agent.py` runs, rerun only the five workbooks above on Haiku 5.5 and Sonnet 5.5 for 5 repeats in one session, and compare with a skill that adds a worked two-column fill range. About 5 workbooks x 2 models x 5 repeats x 2 variants = 100 agent calls; at the E09 agent cost (about $0.002 to $0.03 per task) that is a few dollars at most, under the $5 ask limit, but spend tier is the owner's decision (backlog 0.3).

## A25: snapshot ids

Every stored call (216 each for `claude-haiku-5-5` and `claude-sonnet-5-5`) returned the bare alias as its model, so the API gives no dated id to record. Haiku 4.5 is pinned as `claude-haiku-4-5-20251001`. Consequences: a run is tied to the date it was made, and results from different days are not comparable even under the same alias. This is already in line with the rule to never compare runs from different sessions; `docs/PROTOCOL.md` now says it next to the pinning rule.
