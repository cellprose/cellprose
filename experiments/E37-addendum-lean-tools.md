# E37: Addendum A, Cellprose with its own tools

**Date:** 11 Nov 2026. **Protocol:** [docs/PROTOCOL_ADDENDUM.md](../docs/PROTOCOL_ADDENDUM.md). **Write-up:** the Addendum A section of [benchmarks/RESULTS.md](../benchmarks/RESULTS.md).

## Question
Does the agent built for Cellprose in E34 (`agent_cellprose_lean`: the index in the first message, then `read_range`, `find`, `trace` and `whatif`, with no shell) answer correctly for less money than the agents reading the `.xlsx` (`agent_xlsx`, `agent_xlsx_viewer`)?

## Setup
- **Freeze:** digest `17a8011250d9888ee994e513f8a829035d79af240d92e241fe110726b8afe62c`, posted before the first call ([gist](https://gist.github.com/Utkarsh-Gaikwad/a6c433049f69434ede8e4d51a08f4e84)).
- **Code:** commit `5a65e14`.
- **Models:** the four from E36.
- **Repeats:** 2.
- **Data:** both held-out corpora.
- **Session:** all three arms ran in one session.
- **Timing:** the addendum was decided after E36's results were seen.
- **Preflight:** `results/preflight_lean/`.

## Results
- **Wins:** 14 of 24 comparisons, with no losses. Cost per correct answer is 0.29–0.79 times the agents', and 23 of the 24 intervals are wholly below 1.
- **Real-world, primary verdict (impact questions left out):** a win for Sonnet and Sol against both agents.
- **Real-world, all questions:** a win for Luna and Sol against both agents.
- **SpreadsheetBench:** a win for all four models against the shell agent, and for Haiku and Sol against the viewer agent.
- **Where it fell short:** every remaining "no difference" comes from accuracy, except Sonnet against the viewer agent on SpreadsheetBench, whose interval reaches 1.03. Accuracy fell short on address questions (Haiku and Luna) and on impact questions (Sonnet).

## Problems found
None in the run: 1,392 calls, no failures, no resumes. Spend was $29.21 at list price, $17.82 billed.

## Next
- **Improve accuracy on address questions** with the lean tools. E34 found the same weakness, and it's a question-wording issue as much as a tool issue. The change must be checked on development data and then on a new held-out set. These workbooks are not used for a new arm again.
