// Browser side of the site: unzip an .xlsx, run the repo's JS writer on it, and parse the result with the viewer's
// parser. The site never encodes or parses Cellprose itself; it only draws what those two produce.
import SM from './cellprose.gen.js';

export const { core } = SM;

// An .xlsx is a ZIP. Inflate every entry up front (DecompressionStream is async; loadXlsx is not), then hand
// loadXlsx an archive object with read(name), which it accepts in place of a path or Buffer.
export async function unzip(bytes) {
  const b = new Uint8Array(bytes);
  const dv = new DataView(b.buffer, b.byteOffset, b.byteLength);
  let eocd = -1;
  for (let i = b.length - 22; i >= Math.max(0, b.length - 22 - 65535); i--) {
    if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error('This is not an .xlsx file (it is not a ZIP archive).');
  const count = dv.getUint16(eocd + 10, true);
  let p = dv.getUint32(eocd + 16, true);
  const dec = new TextDecoder();
  const parts = new Map();
  const jobs = [];
  for (let i = 0; i < count; i++) {
    if (dv.getUint32(p, true) !== 0x02014b50) throw new Error('The ZIP directory of this file is damaged.');
    const method = dv.getUint16(p + 10, true);
    const size = dv.getUint32(p + 20, true);
    const nameLen = dv.getUint16(p + 28, true);
    const skip = nameLen + dv.getUint16(p + 30, true) + dv.getUint16(p + 32, true);
    const off = dv.getUint32(p + 42, true);
    const name = dec.decode(b.subarray(p + 46, p + 46 + nameLen));
    p += 46 + skip;
    if (!/\.(xml|rels)$/.test(name)) continue;
    const start = off + 30 + dv.getUint16(off + 26, true) + dv.getUint16(off + 28, true);
    const raw = b.subarray(start, start + size);
    if (method === 0) parts.set(name, dec.decode(raw));
    else if (method === 8) {
      jobs.push(new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('deflate-raw')))
        .text().then((t) => parts.set(name, t)));
    } else throw new Error(`Unsupported ZIP compression (method ${method}) in ${name}.`);
  }
  await Promise.all(jobs);
  let total = 0;
  for (const t of parts.values()) total += new TextEncoder().encode(t).length;
  return { read: (name) => (parts.has(name) ? parts.get(name) : null), bytes: total, files: parts.size };
}

// .xlsx bytes -> { text, warnings, wb } where wb is the parsed Cellprose text.
export async function convert(bytes, fileName) {
  const archive = await unzip(bytes);
  const model = SM.loadXlsx(archive);
  const { text, warnings } = SM.dumpsWorkbook(model, { source: fileName });
  return { text, warnings, wb: core.parse(text) };
}

// Cells pasted from a spreadsheet -> same result shape as convert().
export function convertPasted(doc, name) {
  const { text, warnings } = SM.dumpsWorkbook(SM.fromJson(doc), { source: name });
  return { text, warnings, wb: core.parse(text) };
}

// Every cell of a parsed sheet, as { [A1]: { cell, formula } }, regions and loose cells together.
export function cellsOf(wb, sheet) {
  const out = {};
  for (const r of sheet.regions) for (const a of Object.keys(r.cells)) out[a] = core.cellInfo(wb, sheet.name, a);
  for (const a of Object.keys(sheet.loose)) out[a] = core.cellInfo(wb, sheet.name, a);
  for (const a of Object.keys(out)) if (!out[a]) delete out[a];
  return out;
}

export function bounds(cells) {
  let c1 = 1, r1 = 1;
  for (const a of Object.keys(cells)) {
    const p = core.parseAddr(a);
    if (cells[a].type === 'empty' && !cells[a].formula) continue;
    c1 = Math.max(c1, p.col); r1 = Math.max(r1, p.row);
  }
  return { c1, r1 };
}

// Typed numbers that sit in a gap between two cells of one fill pattern: the neighbour before, shifted two cells
// along, gives the neighbour after. That is what a gap in a fill range means (docs/SPEC.md, formulas block).
export function overrides(wb, sheet, cells) {
  const res = new Set();
  const f = (c, r) => (c < 1 || r < 1 ? null : core.formulaAt(sheet, core.addr(c, r)));
  for (const [a, x] of Object.entries(cells)) {
    if (x.formula || x.type !== 'number') continue;
    const { col, row } = core.parseAddr(a);
    const L = f(col - 1, row), R = f(col + 1, row), U = f(col, row - 1), D = f(col, row + 1);
    if ((L && R && core.shiftFormula(L, 2, 0) === R) || (U && D && core.shiftFormula(U, 0, 2) === D)) res.add(a);
  }
  return res;
}

// The values of a parsed workbook as CSV, one block per sheet, the way the benchmark wrote CSV.
export function toCsv(wb) {
  return wb.sheets.map((s) => {
    const cells = cellsOf(wb, s), b = bounds(cells), lines = ['## ' + s.name];
    for (let r = 1; r <= b.r1; r++) {
      const row = [];
      for (let c = 1; c <= b.c1; c++) {
        let t = cells[core.addr(c, r)]?.text ?? '';
        if (/[",\n]/.test(t)) t = '"' + t.replace(/"/g, '""') + '"';
        row.push(t);
      }
      lines.push(row.join(','));
    }
    return lines.join('\n');
  }).join('\n\n') + '\n';
}

export const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// A small GitHub-flavoured renderer for Cellprose files: front matter, headings, fenced blocks and pipe tables.
// With `linked`, grid rows and formulas lines carry data-sh / data-row / data-fi, the same hooks the source pane has,
// so the viewer can highlight one place in all its panes.
export function gfm(t, linked = false) {
  const L = t.split('\n');
  let h = '', i = 0, cur = null, fi = 0;
  const q = (v) => esc(v).replace(/"/g, '&quot;');
  if (L[0] === '---') {
    let j = 1; const kv = [];
    while (j < L.length && L[j] !== '---') { const k = L[j].indexOf(':'); kv.push([L[j].slice(0, k), L[j].slice(k + 1)]); j++; }
    h += `<table class="fm">${kv.map(([k, v]) => `<tr><td><b>${esc(k)}</b></td><td>${esc(v)}</td></tr>`).join('')}</table>`;
    i = j + 1;
  }
  // v0.3 rows have no outer pipes (`2|North|120`); v0.2 rows have both (`|2|North|120|`)
  const split = (r) => (r.startsWith('|') ? r.slice(1, -1) : r).split(/(?<!\\)\|/);
  const rowNo = (r) => /^\|?(\d+)\|/.exec(r);
  for (; i < L.length; i++) {
    const l = L[i];
    if (l.startsWith('## ')) h += `<h2>${esc(l.slice(3))}</h2>`;
    else if (l.startsWith('# ')) {
      const m = /^# Sheet: (.*)$/.exec(l);
      if (m) { cur = m[1].replace(/^"|"$/g, ''); fi = 0; }
      h += `<h1>${esc(l.slice(2))}</h1>`;
    } else if (l.startsWith('```')) {
      let j = i + 1; const b = [];
      while (j < L.length && !L[j].startsWith('```')) { b.push(L[j]); j++; }
      if (linked && l.trim() === '```formulas' && cur !== null) {
        h += `<pre class="fmls">${b.map((x) => (x.includes(' = ') ? `<span class="ln fl" data-sh="${q(cur)}" data-fi="${fi++}">${esc(x)}</span>` : `<span class="ln">${esc(x)}</span>`)).join('')}</pre>`;
      } else h += `<pre>${esc(b.join('\n'))}</pre>`;
      i = j;
    } else if (l.startsWith('|') || l.startsWith('#|')) {
      const rows = []; let j = i;
      while (j < L.length && (l.startsWith('|') ? L[j].startsWith('|') : L[j].trim() !== '')) { rows.push(L[j]); j++; }
      h += `<table><tr>${split(rows[0]).map((c) => `<th>${esc(c)}</th>`).join('')}</tr>${rows.slice(2)
        .map((r) => `<tr${linked && cur !== null && rowNo(r) ? ` data-sh="${q(cur)}" data-row="${rowNo(r)[1]}"` : ''}>${split(r).map((c) => `<td>${esc(c.replace(/\\\|/g, '|')).replace(/&lt;br&gt;/g, '<br>')}</td>`).join('')}</tr>`).join('')}</table>`;
      i = j - 1;
    } else if (l.trim()) h += `<p>${esc(l)}</p>`;
  }
  return h;
}
