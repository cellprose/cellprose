# E08: Usage-limit interruption

**Date:** 2026-10-07, about 21:00 IST · **Type:** run failure · **Status:** handled; no bad data in the results

## What happened

The first attempt at repeated runs hit the account's Claude usage limit partway through. Calls after that point returned an error message ("You've hit your session limit") instead of an answer. The one-shot runner discarded these errors. The agent runner saved them as if they were answers, because it didn't check `is_error`.

## Handling

- All runs were stopped.
- Every result whose text contained the limit message, or whose status wasn't `success`, was deleted: 33 agent files (14 Haiku and 9 Sonnet Sheetmark-file runs, 10 Sonnet raw-xlsx runs).
- [`run_agent.py`](../benchmarks/run_agent.py) now raises on `is_error`, so an error is retried or reported instead of saved.
- The repeats were re-run after the limit reset ([E09](E09-same-session-repeats.md)).

## Lesson

- **Validate every saved result,** not just the ones that look wrong. An error message can look like a model answer.
- **Budget usage before a run.** The project rules now say to estimate cost first and ask before spending more than $5.
