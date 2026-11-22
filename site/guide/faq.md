# FAQ

## Is it lossless?

For what it carries, yes: values, formulas, number formats, merges and defined names convert back to `.xlsx`, and encoding again gives byte-identical text on the benchmark workbooks and an edge-case set. Styling, charts and the other non-goals in the [specification](/reference/spec) are dropped.

## Why not give the model the .xlsx?

An agent reading the raw file spends turns and tokens unpacking XML. In the 11 November run, Cellprose in the prompt in one call cost 0.32 to 0.60 times as much per correct answer as MarkItDown and was within a few points of a shell agent's accuracy, without the agent's 3.5 to 4.6 turns. See the [benchmarks](/benchmarks) for per-model numbers and limits.

## Does it work with models other than Claude?

The published run covers four models, including GPT-6 Luna, on one date. Results differ by model and tokenizer, so read the per-model tables in the [benchmarks](/benchmarks) rather than a pooled figure.

## How big a workbook can it handle?

The benchmark corpora are real-world and SpreadsheetBench workbooks (30 and 28), not only small ones. For long regions, a compact profile (`--max-rows`) keeps the first and last rows and marks what it left out.

## Is there a second implementation?

Yes. A JavaScript writer in `js/`, written from the specification without reading the Python writer, passes the conformance kit byte for byte. It is what converts files in this site's [playground](/playground).
