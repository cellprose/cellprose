# Cellprose Viewer

A browser extension that upgrades `.sheet.md` files on GitHub. GitHub already renders the tables; the viewer adds:

- **Sheet tabs.** One tab per `# Sheet:` section instead of one long page.
- **Click a cell** to see its address, value, type, number format and real formula (fill ranges are expanded, so `D4` shows `=D2*D3`, not the anchor's `B2*B3`).
- **Highlight a formula's inputs.** Cells a formula reads are outlined, including through defined names. A reference to another sheet is a link that switches tabs.
- **Copy a range as a grid.** Click a cell, shift-click another, press "Copy range as grid", and paste into Excel, Sheets or Numbers.
- `Esc` clears the selection. Cells that hold a formula carry a blue edge.

Nothing leaves the browser: the extension reads the file you are already viewing (same origin, your GitHub session) and makes no other requests.

## Layout

| Path | What |
| --- | --- |
| `core/cellprose-core.js` | The library: parse v0.2 and v0.3 text, `cellInfo`, `formulaAt`, `refsOf`, `rangeToTSV`. No DOM, no network. Loads as a classic script or `require()`. |
| `extension/` | The Manifest V3 shell: `manifest.json`, `content.js` (DOM and GitHub glue), `content.css`. `extension/cellprose-core.js` is a copy of the core. |
| `test/core.test.js` | Unit tests for the core, run on the golden file in `tests/golden/`. |
| `e2e/` | A fixture page and a Playwright script for clicking through the real DOM. Manual, not in CI. |

The core is deliberately separate so the same code can power another surface later (a review app, a docs site).

## Develop

```
cd viewer
npm test            # core tests, plus a check that extension/cellprose-core.js is in sync
node sync-core.js   # refresh the copy after editing core/
```

Load it in Chrome: `chrome://extensions` → Developer mode → Load unpacked → pick `viewer/extension`. Open any `*.sheet.md` file on github.com.

## Limits (v0.1 of the viewer)

- Reads the file from `/raw/`, so it shows the committed text, not a diff view. Rendered diffs are the git diff driver's job.
- Formula results are the cached values in the file (6 significant figures); the viewer does not recalculate.
- Needs GitHub's rendered Markdown view (`/blob/`). Files over GitHub's render limit show no tables to upgrade.
- Chrome and Edge (MV3). Firefox and a Chrome Web Store listing are not done.
