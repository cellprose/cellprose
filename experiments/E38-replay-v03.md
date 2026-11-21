# E38: Home page replay, re-recorded on v0.3

**Date:** 21 Nov 2026. **Not a benchmark result.** It is one illustrative call per format for the home page's replay race.

## Question
The replay on the home page was recorded on the v0.2 text. Does the same call, re-recorded on the v0.3 text, still show the kind of miss values-only formats make?

## Setup
- **Command:** `api_run.py --models haiku55 --workbooks 11_forecast_overrides --encs csv,cellprose_v03 --out results/e38_replay`, then `RESULTS_DIR=results/e38_replay python3 score.py`.
- **Calls:** 2 (one per format), one repeat, one run id (`20261121T160101Z-e721be`), Haiku 5.5, development workbook 11. Each call asks all six questions of the workbook; the replay shows the question on C4:M5.
- **Cost:** about $0.003 at list price, uncached. The pre-run estimate was $0.00, worst case $0.03.
- **Code:** commit `3631d4d`, clean tree.

## Results
- **CSV:** answered the C4:M5 question with `Forecast!K5` only (score 0.67). It missed `Forecast!H4`. Whole call: 0.873 over six questions.
- **Cellprose v0.3:** answered `Forecast!H4` and `Forecast!K5` (score 1.0). Whole call: 1.0.
- The picture matches the earlier v0.2 recording.

## Limits
- One call per format, one repeat. This says nothing about rates; the 11 Nov run (E36) does.
- The question was chosen because it shows the miss, as with the earlier recording. Workbook 11 is a development workbook, not held out.
- Single run, not paired with other sessions, so it is not compared with any earlier run.
- The reasoning text is not saved.

## Where it is used
`benchmarks/site_data.py` writes it to `site/data/benchmarks.json` ("replay"); `site/.vitepress/theme/components/ReplayRace.vue` shows it.
