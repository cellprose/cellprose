# E10: Cache-neutral cost

**Date:** 2026-10-08 · **Type:** measurement fix · **Status:** adopted for every cost figure

## What happened

The first analysis of the repeats ([E09](E09-same-session-repeats.md)) showed Sheetmark v0.2 at **−94%** cost on Haiku, which was obviously wrong. Repeat runs send identical prompts, and the API's prompt cache bills a repeated prompt at about 10% of the normal input price. Whichever format happened to run second in a cache window looked nearly free.

## Fix

[`analyze.py`](../benchmarks/analyze.py) `usage()` now prices every token as uncached: all input tokens (fresh, cache-read and cache-write) at the input price, plus output at the output price.

| Model | Input price, $/M tokens | Output price, $/M tokens |
| --- | --- | --- |
| Haiku 4.5 (`claude-haiku-4-5-20251001`) | 1 | 5 |
| Haiku 5.5 (`claude-haiku-5-5`) | 0.10 | 0.50 |
| Sonnet 5.5 (`claude-sonnet-5-5`) | 2 | 10 |

That makes cost proportional to the work done, whatever the cache state. Billed cost from the CLI is still kept in each raw file (`cost`) but isn't used for comparisons.

## Lesson

Use a cost metric that doesn't depend on run order. For the publishable benchmark, turn prompt caching off entirely.
