# E17: All eleven encodings on three cheap models

**Date:** 2026-10-09 · **Type:** benchmark (encoding comparison) · **Status:** done. 462 of 462 calls succeeded.

## Question

Which encoding gives the lowest cost per correct answer, and is there a Sheetmark variant that removes the input overhead seen in [E16](E16-grid-csv-vs-sheetmark.md)?

## Setup

| Item | Value |
| --- | --- |
| Models | `haiku55`, `sonnet55`, `gpt6luna` (settings as in E16) |
| Workbooks | all 14 |
| Encodings | all 10 in `encoders.ENCODINGS` plus `none` (questions without the workbook) |
| Repeats | 1, one invocation |
| Cost | $1.87 expected; actual $1.91 (Anthropic $1.82, OpenAI $0.09) |

## Results

Totals over 14 workbooks. Brackets: change against CSV for the same model. Cost per correct = cost / accuracy, relative to CSV.

| Model | Encoding | Accuracy % | Input tokens | Output tokens | Cost | Cost per correct vs CSV |
| --- | --- | --- | --- | --- | --- | --- |
| haiku55 | csv | 98.4 | 23,681 (+0%) | 19,412 | $0.0121 (+0%) | +0% |
| haiku55 | sheetmark_lean | 97.6 | 27,917 (+18%) | 14,753 | $0.0102 (-16%) | -15% |
| haiku55 | sheetmark_lean_gfm | 99.1 | 29,463 (+24%) | 15,839 | $0.0109 (-10%) | -11% |
| haiku55 | sheetmark | 99.0 | 36,491 (+54%) | 14,063 | $0.0107 (-12%) | -12% |
| haiku55 | sheetmark_labels | 99.7 | 36,289 (+53%) | 14,407 | $0.0108 (-10%) | -12% |
| haiku55 | sheetmark_inline | 98.7 | 51,544 (+118%) | 11,882 | $0.0111 (-8%) | -8% |
| haiku55 | grid_values | 97.5 | 33,844 (+43%) | 16,673 | $0.0117 (-3%) | -2% |
| haiku55 | markdown | 90.9 | 30,578 (+29%) | 19,922 | $0.0130 (+8%) | +17% |
| haiku55 | toon | 92.2 | 24,725 (+4%) | 21,693 | $0.0133 (+10%) | +18% |
| haiku55 | markdown_kv | 84.6 | 47,619 (+101%) | 20,705 | $0.0151 (+25%) | +46% |
| haiku55 | none | 1.0 | 6,213 (-74%) | 4,285 | $0.0028 (-77%) | +2078% |
| sonnet55 | csv | 98.9 | 23,681 (+0%) | 10,967 | $0.1570 (+0%) | +0% |
| sonnet55 | sheetmark_lean | 99.8 | 27,917 (+18%) | 8,904 | $0.1449 (-8%) | -9% |
| sonnet55 | sheetmark_lean_gfm | 99.8 | 29,463 (+24%) | 9,012 | $0.1490 (-5%) | -6% |
| sonnet55 | sheetmark | 99.8 | 36,491 (+54%) | 7,732 | $0.1503 (-4%) | -5% |
| sonnet55 | sheetmark_labels | 98.9 | 36,289 (+53%) | 9,142 | $0.1640 (+4%) | +4% |
| sonnet55 | sheetmark_inline | 100.0 | 51,544 (+118%) | 8,685 | $0.1899 (+21%) | +20% |
| sonnet55 | grid_values | 98.9 | 33,844 (+43%) | 9,207 | $0.1598 (+2%) | +2% |
| sonnet55 | markdown | 98.9 | 30,578 (+29%) | 11,060 | $0.1718 (+9%) | +9% |
| sonnet55 | toon | 96.3 | 24,725 (+4%) | 11,946 | $0.1689 (+8%) | +10% |
| sonnet55 | markdown_kv | 93.9 | 47,619 (+101%) | 12,751 | $0.2227 (+42%) | +49% |
| sonnet55 | none | 4.8 | 6,213 (-74%) | 1,245 | $0.0249 (-84%) | +228% |
| gpt6luna | csv | 97.8 | 17,911 (+0%) | 13,577 | $0.0086 (+0%) | +0% |
| gpt6luna | sheetmark_lean | 98.9 | 21,147 (+18%) | 11,034 | $0.0076 (-11%) | -12% |
| gpt6luna | sheetmark_lean_gfm | 98.9 | 22,525 (+26%) | 11,226 | $0.0079 (-8%) | -9% |
| gpt6luna | sheetmark | 97.8 | 25,975 (+45%) | 9,335 | $0.0073 (-15%) | -15% |
| gpt6luna | sheetmark_labels | 99.3 | 25,833 (+44%) | 8,309 | $0.0067 (-21%) | -23% |
| gpt6luna | sheetmark_inline | 97.3 | 36,935 (+106%) | 9,652 | $0.0085 (-1%) | -0% |
| gpt6luna | grid_values | 95.2 | 24,066 (+34%) | 10,291 | $0.0076 (-12%) | -10% |
| gpt6luna | markdown | 97.2 | 21,717 (+21%) | 12,981 | $0.0087 (+1%) | +2% |
| gpt6luna | toon | 88.4 | 18,842 (+5%) | 13,374 | $0.0086 (-0%) | +11% |
| gpt6luna | markdown_kv | 81.6 | 34,659 (+94%) | 22,026 | $0.0145 (+69%) | +102% |
| gpt6luna | none | 2.2 | 4,128 (-77%) | 6,762 | $0.0038 (-56%) | +1911% |

## Reading

- **`none` scores 1-5%**, so answers cannot be guessed from the questions alone. The test inputs carry the information.
- **`sheetmark_lean` (the non-GFM layout) carries the least overhead of the Sheetmark variants:** +18% input against CSV, versus +24% for `sheetmark_lean_gfm`. It has the lowest cost per correct answer for `haiku55` (-15%) and `sonnet55` (-9%), and is close behind for `gpt6luna` (-12%). The GitHub-renderable table layout costs about 6 points of input.
- **Every Sheetmark variant matches or beats CSV on cost per correct answer for `haiku55` and `gpt6luna`;** for `sonnet55` three do (`sheetmark_lean`, `sheetmark_lean_gfm`, `sheetmark`) and two do not (`sheetmark_labels` +4%, `sheetmark_inline` +20%).
- **TOON** is nearly as small as CSV on input (+4-5%) but less accurate (88-96%) and more expensive per correct answer (+10-18%). **Markdown-KV** is the worst on every model.

## Limits

One repeat, three cheaper models, 14 workbooks built for this project, separate invocation (not comparable with E16 even for the shared encodings). GPT prices unverified.

## Reproduce

```bash
cd benchmarks
python3 api_run.py --models haiku55,sonnet55,gpt6luna --out results/e17-encodings --vendor-cap-usd 10
RESULTS_DIR=results/e17-encodings python3 score.py
RESULTS_DIR=results/e17-encodings python3 analyze.py
```
