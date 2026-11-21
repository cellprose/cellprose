// Read-only views of site/data/benchmarks.json (written by benchmarks/site_data.py from the result files).
import data from '../../../data/benchmarks.json';

export { data };
export const ORDER = ['csv', 'markdown', 'toon', 'sheetmark_lean_gfm'];
export const SHORT = { csv: 'CSV', markdown: 'Markdown', toon: 'TOON', sheetmark_lean_gfm: 'Cellprose', agent_xlsx: 'Raw .xlsx + tools', agent_sheetmark: 'Cellprose file + tools' };
export const label = (enc) => data.labels[enc] || enc;
export const rows = (set, model, list = data.sets[set].mean) => ORDER.map((e) => list.find((r) => r.model === model && r.encoding === e)).filter(Boolean);
export const row = (set, model, enc) => data.sets[set].mean.find((r) => r.model === model && r.encoding === enc);
export const interval = (set, model, baseline) => data.sets[set].interval.find((i) => i.model === model && i.baseline === baseline);
export const pct = (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%';
export const ratioPct = (r) => pct(Math.round((r - 1) * 100));
export const num = (v) => Number(v).toLocaleString('en-US');
