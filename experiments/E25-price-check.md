# E25: registry prices against vendor pages (B24)

Date: 2026-10-11. Cost: $0 (web lookup, no model calls).

## Question

Do the list prices in `benchmarks/runner/models.py`, used to re-price `headline_r1r2.json` and every API run, match the vendors' pricing pages?

## Method

Read Anthropic's pricing page (platform.claude.com/docs/en/about-claude/pricing) and OpenAI's (developers.openai.com/api/docs/pricing) and compared each registered model.

## Result

| Model | $/M input | $/M output | Matches registry |
| --- | --- | --- | --- |
| Haiku 4.5 | 1 | 5 | yes |
| Haiku 5.5, prompt up to 100,000 tokens | 0.10 | 0.50 | yes |
| Haiku 5.5, prompt over 100,000 tokens | 0.50 | 2.50 | **missing; added** |
| Sonnet 5.5 | 2 | 10 | yes |
| Opus 5.5 | 4 | 20 | yes |
| Fable 5.1 | 10 | 50 | yes |
| gpt-6-luna (to 272K input) / long | 0.10 / 0.20 | 0.50 / 0.75 | yes / **added** |
| gpt-6.1-sol / long | 2 / 4 | 10 / 15 | yes / **added** |
| gpt-6-astra / long | 10 / 20 | 50 / 75 | yes / **added** |

The base prices were right, including the owner-supplied GPT prices. The registry had no long-prompt tier: Haiku 5.5 is the only Claude model priced by prompt length, and every GPT-6 model has a long-context rate above 272K input tokens. All 14 benchmark workbooks fit under both thresholds, so no existing result changes, and `headline_r1r2.json` is unchanged. Real workbooks do not: the 42-file real corpus does (the largest data sheet encodes to about 790K tokens in the llm-api run), and there a Haiku 5.5 request costs 5 times as much per token.

## Change

`ModelCfg` carries an optional long-prompt threshold and rates; `call_cost`, `estimate` and `analyze.py` pick the rate per request, and agent mode prices each turn on its own prompt length (summing turns first would put a 10-turn run of 20K-token prompts into the long tier). Each raw file records the tier it was priced with. Tests: `tests/test_runner.py`, `tests/test_runner_prep.py`.

## Limits

Third-party sites agreed with the vendor pages on the base prices, but one aggregator listed Astra at $5 / $25 from an older snapshot; the vendor page was used. Prices change: re-check on the day of the final run.
