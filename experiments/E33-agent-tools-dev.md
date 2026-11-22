# E33: Cellprose agent tools and outline mode on large dev workbooks

> **Ids (renamed 9 Nov 2026).** This file was written with the ids `sheetmark_v03` (v0.3 text without the row-number legend) and `sheetmark_v031` (with it). They are now `cellprose_v03_nolegend` and `cellprose_v03`; `agent_` variants likewise. Raw results keep the old ids and score unchanged. "v0.3.1" below means the text with the legend.

**Status:** done (2026-11-07), with a follow-up round (below). Development data only; exploratory. No frozen file, protocol text or held-out set was touched.

## Question
E32 found no difference between the one-shot Cellprose file and an agent reading the .xlsx, and the agent was cheaper on
the largest files (GPT-6.1 Sol: Cellprose cost up to 4.5x the agent's above about 40k characters). Does an agent with
purpose-built Cellprose tools (`outline`, `read_range`, `find`, `trace`) beat the openpyxl agent on large files? Plan and
research: the Claude Doc "Plan: make Cellprose beat Excel-reading agents" (project thread, 2026-11-07).

## What was built
- `src/cellprose/tools.py`: `outline` (an `index` block of sheets and long regions, then the compact profile, regions
  over 6 rows cut to head and tail), `read_range` (one A1 range as Cellprose), `find` (cells containing text, with the
  6 non-empty cells to their right), `trace` (precedents; direct or transitive dependents). Tests: `tests/test_tools.py`.
  Also exposed by the MCP server as `outline_workbook`, `find_cells`, `trace_cell`.
- Arm `agent_xlsx_cellprose`: the agent_xlsx sandbox, file, prompt and limits, plus those four tools
  (`runner/agent.py::CELLPROSE_TOOLS`). `agent_xlsx_viewer` (SpreadsheetBench 2 style viewer) runs as a stronger baseline.
- Dev set `dev_` (`benchmarks/external/devlarge.py`): 10 workbooks drawn by a seeded rule from the project's
  real-workbooks folder, excluding every file selected by rw_, rw2_ or rw3_ (by SHA-256, name and base name), with
  v0.3 text of at least 6,000 o200k tokens. All 10 turned out to be Damodaran models (formula-heavy, many small
  regions), 6k to 58k tokens. Questions: the realworld2 rules unchanged, 6 per workbook, 60 in all.
- `runner/split.py`: names starting `dev_` are development. `split.json` is hashed by `freeze/tier2.json`, so it was
  not edited; this is the only change to the split's meaning, and no held-out set uses the prefix.

## Offline token counts (o200k, no API spend)
| Workbook | v0.3.1 tokens | CSV tokens | v0.3.1 / CSV | outline tokens | outline / v0.3.1 |
| --- | --- | --- | --- | --- | --- |
| dev_apv | 20,384 | 12,769 | 1.60 | 12,194 | 0.60 |
| dev_ddm3st | 6,337 | 2,164 | 2.93 | 6,229 | 0.98 |
| dev_divginzu | 56,698 | 42,704 | 1.33 | 12,481 | 0.22 |
| dev_dividends | 11,169 | 5,606 | 1.99 | 8,169 | 0.73 |
| dev_fcfe3st | 11,081 | 3,068 | 3.61 | 10,909 | 0.98 |
| dev_fcfeginzu | 57,548 | 43,056 | 1.34 | 13,746 | 0.24 |
| dev_fcffginzulambda | 28,709 | 16,929 | 1.70 | 18,870 | 0.66 |
| dev_fcffneg | 8,714 | 4,279 | 2.04 | 8,071 | 0.93 |
| dev_histretsp | 54,545 | 53,350 | 1.02 | 12,804 | 0.23 |
| dev_riskchecker | 6,281 | 5,166 | 1.22 | 2,283 | 0.36 |
| all | 261,466 | 189,091 | 1.38 | 105,756 | 0.40 |

CSV carries no formulas, so v0.3.1 / CSV is high on formula-heavy models. The outline shrinks big data regions (0.22x
to 0.24x) but barely touches models made of many small formula regions (0.93x to 0.98x).

## Run
Haiku 5.5 and GPT-6.1 Sol, 1 repeat, caching off, uncached prices, agent limits 40 turns and $1 per call. Caps: one-shot `--max-usd 2`, agent `--max-usd 3.5`.
```
export CELLPROSE_CORPUS=external/devlarge
W=$(ls external/devlarge/questions | sed 's/.json//' | paste -sd,)
python3 api_run.py   --models haiku55,gpt61sol --workbooks $W --encs sheetmark_v031 --reps 1 --out results/e33_dev --max-usd 2
python3 api_agent.py --models haiku55,gpt61sol --workbooks $W --variants agent_xlsx,agent_xlsx_cellprose,agent_xlsx_viewer --reps 1 --out results/e33_dev --max-usd 3.5
CELLPROSE_CORPUS=external/devlarge RESULTS_DIR=results/e33_dev COMPARE_ENC=sheetmark_v031 python3 score.py
```
Run ids: one-shot `20261107T130946Z-3b4774`, agent `20261107T131056Z-c72b4f`. 80 calls, 0 failures. Spend **$2.69**
(one-shot $0.63, agent $2.06; Anthropic $0.31, OpenAI $2.38).

## Results (1 repeat, 10 workbooks, 60 questions)
| Model | Arm | Accuracy | Mean cost per call | Turns |
| --- | --- | --- | --- | --- |
| Haiku 5.5 | sheetmark_v031 (one-shot) | 88.8 | $0.0046 | |
| Haiku 5.5 | agent_xlsx | 93.9 | $0.0085 | 5.4 |
| Haiku 5.5 | agent_xlsx_viewer | 94.6 | $0.0091 | 4.7 |
| Haiku 5.5 | agent_xlsx_cellprose | 91.8 | $0.0081 | 4.6 |
| GPT-6.1 Sol | sheetmark_v031 (one-shot) | 98.3 | $0.0583 | |
| GPT-6.1 Sol | agent_xlsx | 97.6 | $0.0592 | 4.4 |
| GPT-6.1 Sol | agent_xlsx_viewer | 96.7 | $0.0637 | 4.4 |
| GPT-6.1 Sol | agent_xlsx_cellprose | 96.7 | $0.0574 | 3.3 |

Cost per correct answer, ratio, 95% bootstrap over the 10 workbooks:

| Model | cellprose tools vs agent_xlsx | cellprose tools vs viewer | one-shot v0.3.1 vs agent_xlsx |
| --- | --- | --- | --- |
| Haiku 5.5 | 0.97 (0.75-1.34) | 0.91 (0.58-1.42) | **0.57 (0.33-0.94)** |
| GPT-6.1 Sol | 0.98 (0.73-1.35) | 0.90 (0.70-1.13) | 0.98 (0.57-1.59) |

## What it says (exploratory)
- **The tools do not beat the openpyxl agent yet.** Cost per correct answer is level (0.97, 0.98). Sol needs one turn
  fewer (3.3 against 4.4) and writes half the output tokens (435 against 917), but reads more input (14.0k against
  10.8k tokens per call).
- **The outline is the cost.** It averages about 10k tokens, and with caching off every later turn pays for it again.
  The openpyxl agent's tool outputs are small. On Sol the tool calls were trace 23, read_range 20, outline 10, find 6:
  the targeted tools are used as intended; the map is what is too big.
- **On these models the one-shot file holds up better than on Enron.** Sol: 0.98, no difference; Haiku: 0.57, a win.
  Most of these files are under E32's crossover once formulas are counted as content the agent also has to read.
- Haiku's one-shot accuracy (88.8) trails the agents (92 to 95), mostly address questions (70%). Sol is at 97 to 98 in
  every arm.

## Follow-up round: index-only outline and a data-heavy dev set

Capped at $4.50 for the round. Spend **$2.30**.

**What changed.** `tools.index` returns only the map: per sheet its used range and counts, then each region with its size,
formula count and a 5-value first-row preview, no other values (325 to 1,961 tokens on the dev_ files, against about
10k for `outline`). New arm `agent_xlsx_cellprose_idx` = agent_xlsx_cellprose with `outline` replaced by the index;
`agent_xlsx_cellprose` is kept unchanged so round 1 stays comparable.

**Data-heavy set `dev_d_`** (`devlarge.py --data`): no eligible file in the project folder passed the extra test (v0.3
at most 1.3x CSV tokens), so the draw used the public Enron corpus (figshare 1221767, CC BY 4.0, 15,929 files),
skipping the 30 authors rw2_ or rw3_ selected, one file per author, seed 20261109. Two rules were added during the draw,
before any model call on it: files over 2 MB and files whose screening takes over 120 s are skipped (a first pass
stalled on one file), and a file whose screening raises is rejected (a second pass crashed on an unreadable recalculated
copy; it resumed from the logged rejections of the same seeded order with `--resume`). 901 files screened, 10 kept,
8k to 66k tokens, v0.3 0.99x to 1.23x CSV. Questions: realworld2 rules, 60.

**Runs.** Index arm on dev_: run `20261107T132210Z-d5a9c1` in `results/e33_dev` (20 calls, $0.46). dev_d_: one-shot
`20261107T144125Z-109256`, agent `20261107T144214Z-4c5d55` in `results/e33_devdata` (80 calls, $1.84). 0 failures.
```
export CELLPROSE_CORPUS=external/devdata; W=$(ls external/devdata/questions | sed 's/.json//' | paste -sd,)
python3 api_run.py   --models haiku55,gpt61sol --workbooks $W --encs sheetmark_v031 --reps 1 --out results/e33_devdata --max-usd 1.2
python3 api_agent.py --models haiku55,gpt61sol --workbooks $W --variants agent_xlsx,agent_xlsx_cellprose_idx,agent_xlsx_viewer --reps 1 --out results/e33_devdata --max-usd 2.8
```

| Set | Model | Arm | Accuracy | Mean cost per call | Turns |
| --- | --- | --- | --- | --- | --- |
| dev_ | Haiku 5.5 | agent_xlsx_cellprose_idx | 90.5 | $0.0056 | 4.5 |
| dev_ | GPT-6.1 Sol | agent_xlsx_cellprose_idx | 96.7 | $0.0402 | 3.6 |
| dev_d_ | Haiku 5.5 | sheetmark_v031 (one-shot) | 90.6 | $0.0051 | |
| dev_d_ | Haiku 5.5 | agent_xlsx | 94.4 | $0.0077 | 5.8 |
| dev_d_ | Haiku 5.5 | agent_xlsx_viewer | 89.7 | $0.0081 | 4.5 |
| dev_d_ | Haiku 5.5 | agent_xlsx_cellprose_idx | 95.3 | $0.0047 | 5.2 |
| dev_d_ | GPT-6.1 Sol | sheetmark_v031 (one-shot) | 96.7 | $0.0647 | |
| dev_d_ | GPT-6.1 Sol | agent_xlsx | 100.0 | $0.0312 | 3.8 |
| dev_d_ | GPT-6.1 Sol | agent_xlsx_viewer | 99.4 | $0.0318 | 3.3 |
| dev_d_ | GPT-6.1 Sol | agent_xlsx_cellprose_idx | 98.3 | $0.0296 | 4.0 |

Cost per correct answer, ratio (95% bootstrap over 10 workbooks):

| Set | Model | index tools vs agent_xlsx | index tools vs one-shot v0.3.1 | agent_xlsx vs one-shot v0.3.1 |
| --- | --- | --- | --- | --- |
| dev_ (tuned on) | Haiku 5.5 | **0.68 (0.57-0.91)** | 1.20 (0.73-2.08) | 1.76 (1.06-3.02) |
| dev_ (tuned on) | GPT-6.1 Sol | 0.69 (0.45-1.00) | 0.70 (0.39-1.33) | 1.02 (0.63-1.77) |
| dev_d_ (fresh) | Haiku 5.5 | **0.61 (0.39-0.99)** | 0.88 (0.60-1.31) | 1.44 (0.97-2.14) |
| dev_d_ (fresh) | GPT-6.1 Sol | 0.96 (0.57-1.46) | **0.45 (0.26-0.78)** | **0.47 (0.29-0.81)** |

**What it says (exploratory, 1 repeat):**
- Cutting the map to an index is what made the tools pay. On the fresh data-heavy set, Haiku with the index tools is
  cheaper per correct answer than the openpyxl agent (0.61) and slightly more accurate (95.3 against 94.4). On Sol it
  ties the openpyxl agent (0.96).
- The E32 pattern holds on fresh data-heavy files: on Sol the one-shot file costs about twice what an agent does
  (0.47), so large data-heavy files should be routed to the tools, not sent whole. Haiku is cheap enough per token that
  one-shot is still level there.
- The SpreadsheetBench-style viewer is no better than plain openpyxl on either model.
- The dev_ numbers for the index arm are on the set the change was designed on; dev_d_ is the cleaner test.

## Next (not run)
1. Done in the follow-up round (index-only outline).
2. Drop the `formats` blocks from tool output unless asked; they are a large share on Damodaran models.
3. Done in the follow-up round (dev_d_).
4. A second repeat on dev_d_, and Sonnet 5.5 and GPT-6 Luna, before any held-out run; then size routing in the product
   (one-shot below a threshold, index tools above it) as its own arm.

## Limitations
One repeat; 10 workbooks, all from one author (Damodaran), formula-heavy; 60 questions; prices of 2026-11-07; the
one-shot against agent-loop caveat of PROTOCOL section 1. Nothing here is a held-out result.
