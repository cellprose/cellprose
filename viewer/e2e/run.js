// Manual browser check (needs `playwright-core` and a Chromium; not part of CI):
//   NODE_PATH=<dir with playwright-core> node e2e/run.js [path-to-chromium]
const { chromium } = require('playwright-core');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert');
(async () => {
  const exe = process.argv[2] || process.env.CHROMIUM || '/opt/pw-browsers/chromium';
  const browser = await chromium.launch({ executablePath: exe, args: ['--no-sandbox'] });
  const page = await browser.newPage({ permissions: [] });
  page.on('pageerror', e => { console.error(e); process.exitCode = 1; });
  await page.goto('file://' + path.join(__dirname, 'fixture.html'));
  await page.addStyleTag({ path: path.join(__dirname, '../extension/content.css') });
  await page.addScriptTag({ path: path.join(__dirname, '../extension/cellprose-core.js') });
  await page.addScriptTag({ path: path.join(__dirname, '../extension/content.js') });
  const text = fs.readFileSync(path.join(__dirname, 'fixture.sheet.md'), 'utf8');
  await page.evaluate(t => window.CellproseViewer.enhance(document.querySelector('article'), t), text);

  assert.equal(await page.locator('.smv-tab').count(), 2);
  assert.equal(await page.locator('table:visible').count(), 1);
  await page.click('td[data-smv-addr="D4"]');
  let panel = await page.locator('.smv-panel').innerText();
  assert.match(panel, /P&L!D4/); assert.match(panel, /=D2\*D3/); assert.match(panel, /\$#,##0/);
  assert.deepEqual(await page.locator('td.smv-input').evaluateAll(n => n.map(x => x.dataset.smvAddr)), ['D2', 'D3']);
  // Cross-sheet precedents: click D2, follow the link to Assumptions.
  await page.click('td[data-smv-addr="D2"]');
  await page.click('a.smv-ref[data-sheet="Assumptions"]');
  assert.equal(await page.locator('.smv-tab[aria-selected=true]').innerText(), 'Assumptions');
  assert.deepEqual(await page.locator('td.smv-input').evaluateAll(n => n.map(x => x.dataset.smvAddr)), ['B2']);
  // Range copy on the first sheet.
  await page.click('.smv-tab:first-child');
  await page.click('td[data-smv-addr="A3"]');
  await page.click('td[data-smv-addr="C4"]', { modifiers: ['Shift'] });
  await page.click('[data-smv="copy"]');
  assert.equal(await page.locator('.smv-panel').getAttribute('data-copied'), 'Price\t45\t45\nRevenue\t54000\t58320');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.smv-panel:visible').count(), 0);
  await page.screenshot({ path: process.env.SHOT || '/tmp/smv.png' });
  await browser.close();
  console.log('e2e ok');
})().catch(e => { console.error(e); process.exit(1); });
