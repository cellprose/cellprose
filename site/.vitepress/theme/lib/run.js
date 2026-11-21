// Read-only views of site/data/run.json: the 11 Nov 2026 benchmark run and Addendum A, written by
// benchmarks/site_run.py from the committed result files (tests/test_site_run.py checks it against RESULTS.md).
import run from '../../../data/run.json';

export { run };
export const MODEL_KEYS = run.model_order;
export const modelName = (m) => run.models[m] || m;
export const armName = (a) => run.labels[a] || a;
export const arm = (c, m, a) => run.corpora[c].arms.find((r) => r.model === m && r.arm === a);
export const verdictsFor = (list, m) => list.filter((v) => v.model === m);
export const range = (xs, digits = 1) => {
  const lo = Math.min(...xs), hi = Math.max(...xs);
  return lo === hi ? lo.toFixed(digits) : `${lo.toFixed(digits)}–${hi.toFixed(digits)}`;
};
// Workbook-averaged accuracy across models, as the verdict tables report it: Cellprose's own (`acc`) or a baseline's.
export const cellproseAcc = (c) => range(run.corpora[c].verdicts.filter((v) => v.baseline === 'csv').map((v) => v.acc));
export const baselineAcc = (c, b) => range(run.corpora[c].verdicts.filter((v) => v.baseline === b).map((v) => v.acc_baseline));
export const ratios = (lists, b) => lists.flat().filter((v) => v.baseline === b);
export const wins = (list) => list.filter((v) => v.verdict === 'win').length;
export const money = (v) => (v == null ? 'n/a' : `$${v.toFixed(4)}`);
export const num = (v) => Number(v).toLocaleString('en-US');
