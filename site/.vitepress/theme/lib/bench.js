// Read-only views of site/data/benchmarks.json: the home page's replay (E38, written by benchmarks/site_data.py).
// Every other benchmark number on the site comes from data/run.json (lib/run.js).
import data from '../../../data/benchmarks.json';

export { data };
export const label = (enc) => data.labels[enc] || enc;
export const num = (v) => Number(v).toLocaleString('en-US');
