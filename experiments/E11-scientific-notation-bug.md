# E11: Scientific notation in rounded values

**Date:** 2026-10-08 · **Type:** format bug · **Status:** fixed after the benchmark runs; small effect expected; re-run to confirm

## What happened

While preparing a sample file, the full-year bookings total showed as `1.51599e+06` instead of a plain number. Rounding formula results to 6 significant figures used Python's `%.6g`, which switches to scientific notation at a million or more.

## Fix

Formula results are still rounded to 6 significant figures, but printed in plain notation for magnitudes between 0.0001 and 10^15: `1515987.648` becomes `1515990`. Fixed in [`encoders.py`](../benchmarks/encoders.py) (`fmt_lean`) and in [`src/sheetmark/writer.py`](../src/sheetmark/writer.py) (`fmt_value`), with a test in [`tests/test_writer.py`](../tests/test_writer.py).

## Effect on results

All benchmark runs in [E04](E04-compact-variants.md), [E05](E05-agent-mode-v1.md) and [E09](E09-same-session-repeats.md) used the old formatting, so some totals in the compact format appeared in scientific notation. Lookup accuracy stayed at 100% (values were within the 0.5% tolerance), so the effect is probably small. The next benchmark run will use the fixed writer.
