# E34: lean Cellprose tools against the openpyxl agent on GPT-6.1 Sol

**Status:** done (2026-11-07). Development data only; exploratory. No frozen file, protocol text or held-out set was touched.

## Question
E33 found the index-tools arm cheaper than the openpyxl agent on Haiku 5.5 (0.61) but level on GPT-6.1 Sol (0.96).
Sol's openpyxl agent is lean: about 4 turns, batched lookups. Can a leaner Cellprose kit give a clear lead on Sol?

## What was built (arm `agent_cellprose_lean`)
- The index (`tools.index`) is in the first message, so no turn is spent on `outline`.
- `read_range` takes a list of ranges and drops `formats` blocks (`tools.read_ranges`).
- `trace` returns addresses merged into ranges (`tools.trace(compact=True)`, `tools.compress`).
- `whatif(cell, value | factor)`: set one cell, recalculate with LibreOffice, list the cells whose value changes as
  ranges. Both sides go through the same openpyxl save and recalculation, so the round trip cancels out
  (`tools.whatif`).
- No `bash` or `read_file`: Cellprose tools only, with a system prompt that does not offer python
  (`runner/prompts.py::LEAN_SYSTEM`). The user prompt is otherwise the agent prompt.
- **Caveat:** `whatif` uses the same method as the impact ground truth (`realworld.impact_truth`: LibreOffice
  recalculation of openpyxl-saved copies), so impact questions are close to free for this arm. The openpyxl agent
  could run LibreOffice from its shell but did not. Results are given with impact questions excluded too.

## Data
New data-heavy set `dev_e_` (`devlarge.py --data2`): the `--data` rules (Enron corpus, figshare 1221767; v0.3 at most
1.3x CSV; at least 6,000 tokens; held-out authors skipped) with seed 20261110, N = 20, and the dev_ and dev_d_ files
excluded. Rejections recorded by earlier passes over the same pool were reused with `--resume` (they are properties of
the file, not of the draw). 1,197 files screened, 20 kept, 6k to 86k tokens (603k in all), 120 questions.

## Runs and spend ($3.15 this round, capped at $4.50)
- Development checks on dev_ (the set E33 tuned on), Sol, 1 repeat:
  lean without `whatif` in `results/e33_dev` ($0.25: 0.45 against agent_xlsx, accuracy 92.9; impact 77.6);
  lean with `whatif`, first version comparing against an unsaved baseline (run `20261107T151410Z-699918`, $0.19,
  discarded: the round trip showed as changes), then fixed (`20261107T151519Z-fc325b`, $0.21) in `results/e34_check`.
- dev_e_, Sol, agent_xlsx and agent_cellprose_lean, 2 repeats: run `20261107T162647Z-9ba68e` stopped at the $2.30
  vendor cap with 5 calls not made ($2.38); `20261107T163112Z-879c4d` made those 5 ($0.12). 80 calls, 0 failures.
  The one-shot reference was not run: it would have passed the $4.50 cap. E33 showed one-shot costs about twice an
  agent on Sol for files like these.
```
export CELLPROSE_CORPUS=external/devdata2; W=$(ls external/devdata2/questions | sed 's/.json//' | paste -sd,)
python3 api_agent.py --models gpt61sol --workbooks $W --variants agent_xlsx,agent_cellprose_lean --reps 2 --out results/e34_devdata2 --max-usd 7 --vendor-cap-usd 2.3
CELLPROSE_CORPUS=external/devdata2 RESULTS_DIR=results/e34_devdata2 COMPARE_ENC=agent_xlsx python3 score.py
```
(`--max-usd 7` only clears the runner's pre-run estimate, which used stale CLI-era token counts; the vendor cap is the
real stop.)

## Results: dev_e_, GPT-6.1 Sol, 20 workbooks, 2 repeats
| Arm | Accuracy | Mean cost per call | Turns | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- |
| agent_xlsx | 92.0 | $0.0430 | 4.3 | 17,252 | 847 |
| agent_cellprose_lean | 94.2 | $0.0196 | 2.6 | 8,057 | 345 |

Accuracy by type (agent_xlsx, lean): lookup 87.5, 90.0; address 75.0, 75.0; trace 100, 100; impact 89.2, 100;
hardcode 100, 100.

Cost per correct answer, lean against agent_xlsx (95% bootstrap over the 20 workbooks, repeats pooled):
- all questions: **0.44 (0.35-0.57)**
- impact questions not counted as correct for either arm (costs unchanged): **0.45 (0.36-0.58)**

On dev_ (tuned on, 1 repeat) the fixed lean arm was 0.36 (0.23-0.60), accuracy 95.0 against 97.6.

## What it says (exploratory)
- A clear lead on Sol: the lean kit answers for less than half the openpyxl agent's cost per correct answer, with
  the interval well below 1, and is not less accurate (94.2 against 92.0). The lead does not rest on the what-if tool.
- Where it comes from: 2.6 turns instead of 4.3 (the index replaces the exploring turn), half the input per call, and
  less than half the output (no code to write).
- Address questions are the weak spot for both arms (75%); that is a question-wording issue as much as a format one
  (headers like "D" read as column letters).

## Limitations
One model; one set of 20 workbooks, all Enron; 2 repeats; development data. The lean arm has a different system prompt
and no shell, so it is a product configuration (an MCP-only agent), not a one-variable change. `whatif` shares its
method with the impact ground truth. No one-shot reference on this set. Nothing here is a held-out result.

## Next
Run the lean arm against agent_xlsx on Haiku 5.5, Sonnet 5.5 and GPT-6 Luna on dev_e_, then freeze a fresh set and
pre-register the comparison before any public claim.
