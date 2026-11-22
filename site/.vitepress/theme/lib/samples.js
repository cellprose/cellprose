// The benchmark workbooks the site shows, converted in the browser by the JS writer when a page first needs them.
import { withBase } from 'vitepress';
import { convert, unzip } from './sheet.js';

export const SAMPLES = {
  '11_forecast_overrides': 'Forecast',
  '03_pnl_quarterly': 'P&L',
  '08_loan_schedule': 'Loan schedule',
  '05_multisheet_model': 'Multi-sheet model',
};
const cache = {};

async function bytes(path) {
  const r = await fetch(withBase(path));
  if (!r.ok) throw new Error(`Could not load ${path} (${r.status}).`);
  return r.arrayBuffer();
}

// { text, csv, file, xmlBytes }: the .sheet.md, the benchmark's CSV of the same workbook, and how many bytes of XML
// the .xlsx holds once unzipped.
export function loadSample(name) {
  if (!cache[name]) {
    cache[name] = (async () => {
      const [xlsx, csvBuf] = await Promise.all([bytes(`/samples/${name}.xlsx`), bytes(`/samples/${name}.csv.txt`)]);
      const { text } = await convert(xlsx, `${name}.xlsx`);
      const archive = await unzip(xlsx);
      return { text, csv: new TextDecoder().decode(csvBuf), file: `${name}.xlsx`, xmlBytes: archive.bytes };
    })();
  }
  return cache[name];
}
