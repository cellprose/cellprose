# E06: Answer-parser fix and rescoring

**Date:** 2026-10-07 · **Type:** scoring bug · **Status:** fixed; every number in these files uses the fixed parser

## What happened

Investigating an agent run that scored 0% on a whole workbook ([E05](E05-agent-mode-v1.md)) showed the model had answered correctly. It then wrote "Wait, q2 should refer to Y3 rent… Corrected:" and printed a second JSON object. The original parser grabbed everything from the first `{` to the last `}`, which isn't valid JSON when there are two objects, so the whole answer scored zero.

## Fix

[`score.py`](../benchmarks/score.py) `parse_json` now scans the reply and keeps the **last** valid JSON object whose keys look like question ids (`q1`, `q2`, …). That matches the model's final intent.

## Effect

All runs were rescored. The largest change: Sonnet with CSV on the hard workbooks went from 72.5% to 95.9%. Before the fix, that run made Sheetmark look far better than CSV. No conclusion in the other experiments depends on the bug, and all their numbers are post-fix.

## Lesson

Read the zero-score answers before believing a big gap. Several headline gaps in a benchmark can be scoring artefacts.
