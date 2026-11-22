# Cellprose website

The project site: home, a playground, docs and benchmark results, in the "Live Sheet" look (the page itself is drawn
as a spreadsheet). Built with [VitePress](https://vitepress.dev).

```bash
cd site
npm ci
npm run dev        # http://localhost:5173
npm run build      # static site in .vitepress/dist
npm test           # browser code against the JS writer and the docs
```

## Where things come from

Nothing on the site is a second copy of the format or of the results.

| What | Source |
|---|---|
| Playground and home-page conversions | `js/src` (the JS writer), bundled for the browser by `scripts/prepare.mjs`. An `.xlsx` is unzipped in the page with `DecompressionStream` and handed to `loadXlsx` as an archive object. |
| Parsing `.sheet.md` for the viewer | `viewer/core/cellprose-core.js`, bundled with the writer |
| Spec, design notes, benchmark protocol | `docs/SPEC.md`, `docs/DESIGN.md`, `docs/PROTOCOL.md`, copied into `reference/` at build time with links rewritten (`scripts/links.mjs`) |
| Benchmark numbers | `data/run.json` (the pre-registered run of 11 Nov 2026 and Addendum A), written by `benchmarks/site_run.py` from the committed result files; `tests/test_site_run.py` checks it against `benchmarks/RESULTS.md`. The replay on the home page reads one call per format, recorded on 21 Nov 2026 on the v0.3 text (`results/e38_replay/`, E38), in `data/benchmarks.json` (`benchmarks/site_data.py`). |
| `/llms.txt`, `/llms-full.txt` | Written by `scripts/llms.mjs` from `docs/SPEC.md`, `INTEGRATIONS.md` and the skill. Set `SITE_URL` at build time to make the index's site links absolute; unset, it links to the repo. |
| Sample workbooks | `benchmarks/workbooks/*.xlsx` and the benchmark's CSV of each, copied into `public/samples/` |

`reference/`, `public/samples/`, `public/img/`, `public/llms*.txt` and `.vitepress/theme/lib/cellprose.gen.js` are generated and gitignored.
The guide pages (`guide/`) and the home, playground, benchmarks and ecosystem pages are written by hand.

After a new benchmark run, regenerate the numbers with `cd benchmarks && python site_run.py` (the run and its
addendum) and `python site_data.py` (the replay).

## Layout

| Path | What |
|---|---|
| `.vitepress/config.mts` | Nav, sidebar, search, fonts |
| `.vitepress/theme/` | The Live Sheet theme: `Layout.vue` (formula bar, column letters, row numbers, status bar), `live.js` (draws the column letters, row numbers and section ranges), `style.css`, `components/`, `lib/` |
| `index.md`, `playground.md`, `benchmarks.md`, `ecosystem.md` | Pages built from components |
| `guide/` | Hand-written docs |
| `scripts/` | `prepare.mjs` (bundle, samples, reference pages) and its helpers |

`SITE_BASE` sets the base path for hosting under a sub-path (for example `SITE_BASE=/cellprose/ npm run build` for GitHub Pages).
The code is under Apache-2.0 (`LICENSE`) and the spec under CC-BY-4.0 (`LICENSE-SPEC`); the footer links both. Hosting and domain are not decided yet.

## Domain and hosting

The canonical domain is `https://cellprose.com` (override with `SITE_URL` for previews). The build sets canonical, Open Graph and Twitter meta tags and a sitemap from it. Deploy on Cloudflare Pages: build command `npm run build`, root directory `site`, output directory `.vitepress/dist`. Add `cellprose.com` as a custom domain in the Pages project; Cloudflare creates the DNS record when the zone is in the same account.
