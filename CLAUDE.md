# Cellprose

Cellprose is an open plain-text format for spreadsheet workbooks (`.sheet.md`, or `.cellprose.md`; both are read and written, `.sheet.md` is the default). It was called Sheetmark until October 2026. Two goals drive every decision:

1. **Cost efficiency.** A model reaches a correct answer for fewer total tokens (input + output + reasoning) than with CSV, Markdown or TOON.
2. **Accessibility.** Every file is valid GitHub-Flavored Markdown, so workbooks render as tables and diff cleanly on GitHub without Excel.

## Read first

- `docs/DESIGN.md` covers benchmark results, format decisions, architecture and roadmap. It is the source of truth for v0.2.
- `docs/SPEC.md` is the **v0.3** spec; its examples are the golden tests. Benchmark text and results in DESIGN.md are for the v0.2 text, so when the two disagree on the format, SPEC.md wins.
- `docs/PROTOCOL.md` is how the publishable benchmark run is done, scored and reported.
- `benchmarks/README.md` covers the benchmark pipeline and its known issues.
- `experiments/README.md` indexes every experiment run so far.

## Layout

- `src/cellprose/` is the package. `writer.py` is the v0.3 writer (encode); `mcp_server.py` is the MCP server; `cli.py` is the CLI. Install with `pip install -e ".[dev]"` and run `pytest`.
- `conformance/` is the language-neutral conformance kit (JSON workbooks, expected `.sheet.md`, decoded cells, `check.py`). Cases 01–06 mirror `tests/golden/spec/`; change a case only with the spec (see its README).
- `skills/cellprose/` is the agent skill. `scripts/_vendor/` is a copy of the package; refresh it after changing `src/` (see INTEGRATIONS.md).
- `benchmarks/` holds the benchmark. `benchmarks/encoders.py::enc_lean(gfm=True)` produced the benchmarked v0.2 text; `src/cellprose/writer.py` matches it apart from blank lines between blocks and two additions the benchmark text lacks: number formats of loose cells, array formulas, comments, validation and the dropped-features note (SPEC.md §3, §6.5, §8). New runs compare `cellprose_v03` (the shipped v0.3 writer, with the row-number legend) and its agent variant `agent_cellprose_v03`. Earlier ids still resolve (`benchmarks/runner/ids.py`): `sheetmark_v03` is `cellprose_v03_nolegend`, `sheetmark_v031` is `cellprose_v03`; v0.2 ids stay for earlier runs.
- `experiments/` has one file per experiment (E01…), linked to the benchmark code and raw results. Add a new file for every run, and update `docs/DESIGN.md` when a decision changes.
- `site/` is the website (VitePress). Its playground runs `js/src` in the browser, its reference pages are copied from `docs/` at build time, and its benchmark numbers come from `benchmarks/site_data.py` (see `site/README.md`).
- `docs/` holds the specs and docs. `docs/img/` holds the headline chart and the architecture diagram.

## v0.3 format in one breath

Front matter `cellprose: 0.3` (the reader also reads 0.2). A `# Sheet: <name>` heading per sheet, then a `## A1:F9` heading per rectangular region. After each heading comes a compact table without outer pipes (`#|A|B`, then `2|Units|1200`) with row numbers and column letters. Next come a `formulas` fenced block of fill ranges (`B4:E4 = B2*B3`) and a `formats` block. Sheet-level blocks (`merges`, `arrays`, `comments`, `validation`) follow the regions. A `# Names` section closes the file. Formula results are rounded to 6 significant figures; typed values are exact. The serialization is canonical: the same workbook always produces the same bytes.

## Branching discipline (always follow)

- `main` is the stable release branch. It only receives merges from `integration` when cutting a release. Never commit or push to it directly.
- `integration` is the stable development branch. Never commit to it directly either.
- All work happens on a new branch cut from the latest `integration` (`git fetch origin && git checkout -b <type>/<short-name> origin/integration`), e.g. `feat/viewer-lib`, `fix/fmt-rounding`, `exp/e13-baselines`, `docs/spec-v0.2`, `chore/ci`.
- When the work is done, push the branch and open a pull request into `integration`. CI must pass before it is merged.
- After a merge, start the next piece of work from a fresh branch off the updated `integration`. Don't reuse old branches.
- Releases: open a PR from `integration` into `main` once `integration` is green and stable, then tag the release (`v0.3.0`, …).

## Working rules

- **Benchmark integrity comes first.** Never compare runs from different sessions. Always report repeats and spread. Price tokens as uncached. State limitations next to every headline number.
- **Spending:** estimate cost before any benchmark run, and ask before spending more than $5.
- Don't change the workbooks, questions or ground truth without saying so explicitly. Old results become incomparable.
- Keep `docs/` in step with code. A format change updates SPEC.md and gets a golden test.
- Commit in small steps with clear messages.
