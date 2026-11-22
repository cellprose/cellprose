# E31: A/B of row-label layouts for the "one column to the right" address fault

> **Ids (renamed 9 Nov 2026).** This file was written with the ids `sheetmark_v03` (v0.3 text without the row-number legend) and `sheetmark_v031` (with it). They are now `cellprose_v03_nolegend` and `cellprose_v03`; `agent_` variants likewise. Raw results keep the old ids and score unchanged. "v0.3.1" below means the text with the legend.

**Status:** done (2026-11-07). Development experiment, not a protocol run. No frozen file is touched.

> **Public repo note.** The four `rw_dam_*` encoded texts of this experiment (Damodaran workbooks, which carry no licence) are not in the public repository; their questions and raw answers are. The `sheetmark-report/` files cited below were internal notes and are not published.

## Question
E30 gate criterion 3 failed because Haiku 5.5 answers address questions on wide tables one column to the right (see
`sheetmark-report/repilot-handoff.md`). Hypothesis: each row starts with its row number, so the model counts the row number
as column A. Which cheap change to the text fixes it?

## Setup
- Model: Haiku 5.5 (`claude-haiku-5-5`, settings from `runner/models.py`), no prompt caching, tokens priced uncached, 2 repeats.
- Data: the 17 `rw_` workbooks (seen twice already, so this is development only). Questions: the 17 committed address
  questions plus 6 extra address questions per table workbook drawn by rule (rows at 10/30/40/60/70/90% of the table,
  target columns cycled, ground truth read from the .xlsx). 65 questions, 130 answers per variant.
- Variants are pure text transforms of the shipped v0.3 text (`benchmarks/exp_address_ab.py`):
  `hdr_row` (header `row|A|B`), `row_end` (row number last), `addr_label` (`A38|...`), `repeat_hdr` (column header repeated
  every 20 rows in tables wider than 6 columns), and four front-matter notes: `note` ("the first field of each table row is
  its row number, not a cell; column A is the second field"), `note_short`, `note_each` (above every table) and `note_ex`
  (the note plus a worked example).
- Cost: about $3.4 in all (estimate by characters was $0.79 for round 1; the real cost was 2.8x that, the estimate undercounts
  Haiku's reasoning output). Two rounds: six variants, then three more notes. Both under the $5 limit.

## Results (Haiku 5.5, address accuracy over 130 answers)

| Variant | Accuracy | Wrong, right row | Input tokens per call |
| --- | --- | --- | --- |
| v03 (current) | 72.3% | 30 | 46,499 |
| hdr_row | 75.4% | 32 | 46,499 |
| row_end | 76.9% | 30 | 46,513 |
| addr_label | 62.3% | 49 | 47,017 |
| repeat_hdr | 73.1% | 35 | 46,944 |
| **note** | **90.0%** | 13 | 46,527 |
| note_short | 75.4% | 32 | 46,518 |
| note_each | 83.1% | 22 | 47,003 |
| note_ex | 82.3% | 23 | 46,565 |

## Reading
- Moving, renaming or repeating the row labels does not help; `addr_label` hurts. So the problem is not the position of the
  row number alone.
- Saying in words that the first field is the row number and column A is the second field helps most (+18 points for about
  28 tokens), but the other notes land between 75% and 83%. The best number is one wording on one model, with correlated
  answers (several per workbook, two repeats), so the spread is wide and it is not proof.
- Some workbooks stay wrong in every variant (for example `rw_dam_capstru`, `rw_ogl04_doh_payments` and `rw_ogl12_purchase_cards`
  partly), so no variant here removes the fault entirely.
- Limits: development data already seen, one model, one prompt, extra questions drawn by me by rule, answers not independent.

## Reproduce
`python3 benchmarks/exp_address_ab.py gen && python3 benchmarks/exp_address_ab.py run --models haiku55 --reps 2 && python3 benchmarks/exp_address_ab.py report`
Raw answers: `benchmarks/results/e31_address_ab/raw/`.

## Round 3: re-test on fresh questions (2026-11-07, $1.53)
Same 17 workbooks, new address questions (rows at 5/20/35/50/80/95%, different target columns), 134 answers per variant,
Haiku 5.5, 2 repeats (`E31_SET=b python3 benchmarks/exp_address_ab.py ...`, results in `results/e31b_address_retest/`).

| Variant | Accuracy | Wrong, right row |
| --- | --- | --- |
| v03 (current) | 71.6% | 37 |
| note | **88.1%** | 15 |
| note_each | 79.9% | 20 |
| note_ex | 82.1% | 24 |

The front-matter note repeats: 72% to 88-90% on two independent question sets (total A/B spend about $4.9). All three note
wordings beat v0.3 in both sets; the plain `note` is best both times, at about 28 tokens. Still the same 17 files and one model.

## Addendum: VLOOKUP lookup-table case (requested by the maintainer)
`benchmarks/exp_vlookup_ab.py`: the 2-sheet example (`Orders!D2:D4 = VLOOKUP(B2,Rates!$A$2:$C$4,2,FALSE())`, Rates = Region|Rate|Manager),
6 questions (which column does the formula return, VLOOKUP with col 3 and col 2, three addresses), Haiku 5.5, 5 repeats, four variants
(v03, note, note_each, note_ex). **30/30 correct in every variant, $0.005.** The fault does not show on a 4-row, 5-column
workbook: the miscount appears in wide tables (7+ columns) with many rows. So the lookup case does not separate the variants; a
wide lookup table (e.g. a 10-column Rates sheet) would be the fair test and is not built yet.

## Decision (2026-11-07)
The maintainer approved adding the `note` wording to the writer as revision 0.3.1 (SPEC §3.1). The writers (Python and JavaScript) emit it
after the front matter when the file has a table, with a second text when a table does not start at column A (that second text was
not in the A/B; the re-pilot is its first real test). The reader ignores it. `sheetmark_v03` keeps the v0.3.0 bytes; `sheetmark_v031` is new.
