// Gets the site's generated inputs ready before VitePress runs. Everything written here is gitignored.
//  1. Bundles the repo's JS writer (js/src) and the viewer's parser (viewer/core) into one browser ES module, so the
//     playground converts .xlsx with the same code the conformance kit checks, not a copy.
//  2. Copies the sample workbooks (and the benchmark's CSV of each) into public/samples.
//  3. Copies the spec, design notes and protocol from docs/ into reference/, with links rewritten for the site.
//  4. Writes llms.txt and llms-full.txt (scripts/llms.mjs).
import { build } from 'esbuild';
import { cpSync, mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { GITHUB, REFERENCE, rewriteLinks } from './links.mjs';
import { fileURLToPath } from 'node:url';
import { llmsFull, llmsIndex } from './llms.mjs';

const SITE = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO = resolve(SITE, '..');
export const SAMPLES = ['11_forecast_overrides', '03_pnl_quarterly', '08_loan_schedule', '05_multisheet_model'];

// 1. the writer and the parser, for the browser
const shims = join(SITE, 'scripts', 'shims');
await build({
  entryPoints: [join(SITE, 'scripts', 'browser-entry.cjs')],
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: 'es2020',
  outfile: join(SITE, '.vitepress', 'theme', 'lib', 'cellprose.gen.js'),
  alias: { fs: join(shims, 'none.cjs'), zlib: join(shims, 'none.cjs'), path: join(shims, 'path.cjs') },
  legalComments: 'none',
  logLevel: 'warning',
});

// 2. samples
const out = join(SITE, 'public', 'samples');
mkdirSync(out, { recursive: true });
for (const s of SAMPLES) {
  cpSync(join(REPO, 'benchmarks', 'workbooks', `${s}.xlsx`), join(out, `${s}.xlsx`));
  cpSync(join(REPO, 'benchmarks', 'encoded', `${s}.csv.txt`), join(out, `${s}.csv.txt`));
}
cpSync(join(REPO, 'docs', 'img'), join(SITE, 'public', 'img'), { recursive: true });

// 3. reference pages
const ref = join(SITE, 'reference');
mkdirSync(ref, { recursive: true });
for (const [file, page] of Object.entries(REFERENCE)) {
  const src = join(REPO, 'docs', file);
  if (!existsSync(src)) throw new Error(`docs/${file} is missing`);
  const body = rewriteLinks(readFileSync(src, 'utf8'), `docs/${file}`);
  const note = `<p class="srcnote">Generated from <a href="${GITHUB}docs/${file}"><code>docs/${file}</code></a>. Edit it there.</p>\n\n`;
  // the note goes under the page's title
  const withNote = /^# .*\n/m.test(body) ? body.replace(/^# .*\n/m, (h) => `${h}\n${note}`) : note + body;
  writeFileSync(join(ref, `${page}.md`), `---\neditLink: false\n---\n\n${withNote}`);
}
// 4. what agents read: /llms.txt and /llms-full.txt
writeFileSync(join(SITE, 'public', 'llms.txt'), llmsIndex(process.env.SITE_URL));
writeFileSync(join(SITE, 'public', 'llms-full.txt'), llmsFull(REPO, process.env.SITE_URL));
console.log('prepared: writer bundle, samples, reference pages');
