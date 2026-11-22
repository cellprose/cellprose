// The site's browser code against the repo: run `npm test` (it bundles the writer first).
import test from 'node:test';
import assert from 'node:assert';
import { readFileSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { convert, core, cellsOf, overrides, toCsv } from '../.vitepress/theme/lib/sheet.js';
import { rewriteLinks } from '../scripts/links.mjs';

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const WB = join(REPO, 'benchmarks', 'workbooks');

test('the browser path (DecompressionStream unzip, then the JS writer) gives the CLI\'s exact bytes', async () => {
  const files = readdirSync(WB).filter((f) => f.endsWith('.xlsx'));
  assert.ok(files.length >= 14);
  for (const f of files) {
    const cli = execFileSync('node', [join(REPO, 'js', 'bin', 'cellprose-encode.js'), join(WB, f)]).toString();
    const { text } = await convert(readFileSync(join(WB, f)), f);
    assert.strictEqual(text, cli, f);
  }
});

test('the typed-in cells the site marks in the forecast are the four the benchmark asks about', async () => {
  const { wb } = await convert(readFileSync(join(WB, '11_forecast_overrides.xlsx')), 'f.xlsx');
  const sh = wb.sheets[0];
  assert.deepStrictEqual([...overrides(wb, sh, cellsOf(wb, sh))].sort(), ['F2', 'H4', 'J2', 'K5']);
});

test('CSV built from the parsed text matches the benchmark\'s CSV on the forecast, apart from rounding', async () => {
  const { wb } = await convert(readFileSync(join(WB, '11_forecast_overrides.xlsx')), 'f.xlsx');
  const ours = toCsv(wb).split('\n'), bench = readFileSync(join(REPO, 'benchmarks', 'encoded', '11_forecast_overrides.csv.txt'), 'utf8').split('\n');
  assert.strictEqual(ours[0], bench[0]);
  assert.strictEqual(ours[1], bench[1]);
  assert.strictEqual(ours[4], bench[4]);   // headcount: typed values, exact in both
});

test('a file that is not an .xlsx gets a readable error', async () => {
  await assert.rejects(convert(new TextEncoder().encode('hello'), 'x.xlsx'), /not an \.xlsx/);
});

test('links in docs/ point at site pages, site images or GitHub', () => {
  const md = '[d](DESIGN.md#goals) ![c](img/x.png) [k](../conformance/README.md) [w](https://x.org) [s](#top)';
  assert.strictEqual(rewriteLinks(md, 'docs/SPEC.md'),
    '[d](./design#goals) ![c](/img/x.png) [k](https://github.com/cellprose/cellprose/blob/main/conformance/README.md) [w](https://x.org) [s](#top)');
});

test('the parser the site uses is the viewer\'s', () => {
  assert.strictEqual(typeof core.parse, 'function');
  assert.strictEqual(core.parse('---\ncellprose: 0.3\n---\n').version, '0.3');
});

test('the git-diff demo: each edit is a small real diff of the .sheet.md', async () => {
  const { unzip } = await import('../.vitepress/theme/lib/sheet.js');
  const { diffTexts, unifiedDiff, EDITS } = await import('../.vitepress/theme/lib/gitdiff.js');
  const archive = await unzip(readFileSync(join(WB, '11_forecast_overrides.xlsx')));
  const changedLines = (k) => { const { before, after } = diffTexts(archive, k); return unifiedDiff(before, after).filter((l) => l.kind === 'add' || l.kind === 'del').map((l) => l.text); };
  const fix = changedLines('fix');
  assert.ok(fix.includes('-B5:J5 = B4*$B$9') && fix.includes('+B5:M5 = B4*$B$9'), fix.join('\n'));
  assert.ok(fix.length <= 6);
  const over = changedLines('override');
  assert.ok(over.includes('-L5:M5 = L4*$B$9') && over.includes('+M5 = M4*$B$9'), over.join('\n'));
  assert.strictEqual(changedLines('rename').length, 2);
  assert.deepStrictEqual(Object.keys(EDITS), ['fix', 'override', 'rename']);
  assert.deepStrictEqual(unifiedDiff('a\nb', 'a\nb'), []);
});

test('llms.txt links the spec and skill; llms-full.txt carries them and leaves out maintainer notes', async () => {
  const { llmsIndex, llmsFull } = await import('../scripts/llms.mjs');
  const idx = llmsIndex();
  assert.match(idx, /^# Cellprose\n\n> /);
  assert.match(idx, /docs\/SPEC\.md/);
  assert.match(llmsIndex('https://example.org/x'), /\(https:\/\/example\.org\/x\/reference\/spec\)/);
  const full = llmsFull(REPO);
  assert.ok(full.includes('claude mcp add cellprose'));
  assert.ok(full.includes('# Cellprose v0.3 — Specification'));
  assert.ok(full.includes('name: cellprose') === false, 'skill front matter is stripped');
  assert.ok(!full.includes('refresh the vendored copy'));
  for (const link of idx.matchAll(/\]\((https:[^)]+)\)/g)) assert.ok(!link[1].includes(' '));
});

test('linked GitHub view: every formulas line and pipe-table row has a hook the source pane has too', async () => {
  const { gfm } = await import('../.vitepress/theme/lib/sheet.js');
  const { text } = await convert(readFileSync(join(WB, '11_forecast_overrides.xlsx')), 'f.xlsx');
  const html = gfm(text, true);
  const fills = (text.match(/^[A-Z]+\d+(:[A-Z]+\d+)? = /gm) || []).length;
  assert.strictEqual((html.match(/data-fi="/g) || []).length, fills);
  assert.strictEqual((html.match(/<tr data-sh="Forecast" data-row="/g) || []).length, 9);   // rows 1-5 and 7-10
  assert.ok(!gfm(text).includes('data-row'), 'the plain view carries no hooks');
});

test('pasted cells: TSV with quoting is typed and converted by the JS writer', async () => {
  const { pastedWorkbook, parseTsv } = await import('../.vitepress/theme/lib/paste.js');
  const { convertPasted } = await import('../.vitepress/theme/lib/sheet.js');
  assert.deepStrictEqual(parseTsv('a\t"b\tc"\n"x""y"\t1\n'), [['a', 'b\tc'], ['x"y', '1']]);
  const doc = pastedWorkbook('Item\tUnits\tPrice\nApple\t1,200\t$2.50\nPear\t30\t12%\n', null);
  assert.strictEqual(doc.sheets[0].cells.B2.v, 1200);
  assert.strictEqual(doc.sheets[0].cells.C2.v, 2.5);
  assert.deepStrictEqual(doc.sheets[0].cells.C3, { v: 0.12, fmt: '0%' });
  const { text } = convertPasted(doc, 'pasted cells');
  assert.match(text, /# Sheet: Sheet1/);
  assert.match(text, /Apple/);
  assert.strictEqual(pastedWorkbook('\n\t\n', null), null);
});
