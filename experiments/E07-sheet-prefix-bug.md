# E07: Missing `Sheet:` prefix in the compact draft

**Date:** 2026-10-07 · **Type:** format bug · **Status:** fixed in the encoder and the v0.2 writer; re-measured in [E09](E09-same-session-repeats.md)

## What happened

To save tokens, the first compact draft ([E04](E04-compact-variants.md)) wrote sheet headings as `# Report` instead of `# Sheet: Report`. In the agent run ([E05](E05-agent-mode-v1.md)), Haiku treated `# Report` as a document title, assumed the sheet was called `Sheet1`, and wrote every address as `Sheet1!…`. All four of its address, trace and impact answers for that workbook scored zero.

## Fix

The `Sheet:` prefix was restored in [`encoders.py`](../benchmarks/encoders.py) (`enc_lean`) and is part of v0.2 ([`src/sheetmark/writer.py`](../src/sheetmark/writer.py)). The draft runs were moved to `benchmarks/results/archive_v1/` and the format was re-run in [E09](E09-same-session-repeats.md).

## Lesson

Structural words that cost a token or two can carry meaning for the model. Removing them needs its own test, not just a size comparison.
