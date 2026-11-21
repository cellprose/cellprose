# E22: fill-range hint (B20)

Date: 2026-10-11. Cost: $0 (token counts and a re-read of the E09 agent results; no model calls).

## Question

Agent mode loses about one point of accuracy when the model reads the Sheetmark file on disk instead of the raw .xlsx, on trace and impact questions (DESIGN.md). One idea in `format-research.md` section 8 was to write the last cell's formula next to each fill range (`B4:E4 = B2*B3  # E4 = E2*E3`) so the shift is visible. Backlog B20 says to fold it into a run only if it would fix the agent-mode trace errors.

## What was built

- `encoders.add_fill_hints` adds the comment to every multi-cell range whose formula shifts, and skips ranges with no relative reference (`B3:E3 = Price`). It works on the finished v0.2 text, so the hint file is the committed v0.2 file plus comments.
- `encoded/<wb>.sheetmark_lean_gfm_hint.txt` for the 14 workbooks.
- Agent variant `agent_sheetmark_hint` in `api_agent.py`. It is opt-in: the default variants are unchanged, and the hint encoding is not in `ENCODINGS`, so no default run sends it.

## Cost in tokens (o200k, 14 workbooks)

v0.2 18,411 tokens, with hints 19,478: **+5.8%**. By workbook it ranges from 0% (`02_employees`, no formulas) to +28% (`12_lookalike_drivers`, small and formula-dense); the large data-heavy files pay 0-8%. The research note's "up to +6.7%" was for the unskipped version. Counted with OpenAI's tokenizer only; the Claude count needs a key.

## Would it fix the trace errors? Not on this evidence

Agent-mode `agent_sheetmark` answers in the E09 runs (haiku and sonnet, 3 repeats):

| Task | v0.2 file | raw .xlsx |
| --- | --- | --- |
| trace | haiku 98.4%, sonnet 96.8% | 100%, 100% |
| impact | haiku 97.0%, sonnet 98.7% | 96.0%, 99.3% |

The trace shortfall is 3 wrong answers out of 126:

- `03_pnl_quarterly` q5, sonnet, both repeats: "Q3 EBITDA" answered with column C instead of D. That is a quarter-to-column mix-up; the hint shows the *last* cell of the range (column E), which would not correct it.
- `07_messy_report` q5, haiku: answered the range `E26:E33` instead of the single summary cell `E34`. Not a fill-range shift.

The impact misses concentrate on three questions (`04_saas_model` q6, `08_loan_schedule` q7, `10_gradebook` q6; 17 of the 24 misses) that need the full dependency set, which a last-cell hint does not give.

So the hint targets an error the data does not show. **Recommendation: do not spend on a run now.** If the user wants it tested anyway, the matched run is `--variants agent_sheetmark,agent_sheetmark_hint` on haiku55, sonnet55 and gpt6luna, 3 reps: 252 calls, expected about $2.9 from the CLI-run averages (the API loop is unmeasured; the worst case is capped at $1 per call by `--max-call-usd`). It would need the user's go-ahead on the spend tier (backlog 0.3).

## A claim to correct

`format-research.md` says the comment is ignored by v0.2 readers. It is not: the reader passes the whole text after `=` to the formula translator, which raises on `# C3 = C1*C2` (`tests/test_fill_hint.py::test_the_v02_reader_rejects_the_hint_comment`). Adopting hints in the format would need a spec rule (a `  # ` comment on a formulas line) and a reader change, plus a golden test, in the same PR. That is another reason to keep it an experiment.

## Reproduce

`python -m pytest tests/test_fill_hint.py`; token counts with tiktoken `o200k_base` over `benchmarks/encoded/*.sheetmark_lean_gfm{,_hint}.txt`; trace and impact misses from `benchmarks/results/scores.csv` (`encoding == agent_sheetmark`).
