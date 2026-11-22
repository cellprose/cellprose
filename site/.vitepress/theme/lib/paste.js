// Cells copied from Excel or Google Sheets -> the workbook JSON the writer takes (conformance/README.md). The clipboard
// carries TSV as text/plain and usually an HTML table too. Excel's HTML keeps formulas (x:fmla), so when its grid has the
// same shape as the TSV, formulas are taken from there; the TSV supplies the values either way.

// Tab-separated text with Excel's quoting: a cell holding a tab, newline or quote is wrapped in "" with "" for a quote.
export function parseTsv(text) {
  const rows = [[]];
  let cell = '', i = 0, quoted = false;
  const s = text.replace(/\r\n?/g, '\n');
  for (; i < s.length; i++) {
    const c = s[i];
    if (quoted) {
      if (c === '"' && s[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') quoted = false; else cell += c;
    } else if (c === '"' && cell === '') quoted = true;
    else if (c === '\t') { rows[rows.length - 1].push(cell); cell = ''; } else if (c === '\n') { rows[rows.length - 1].push(cell); cell = ''; rows.push([]); } else cell += c;
  }
  rows[rows.length - 1].push(cell);
  if (rows.length > 1 && rows[rows.length - 1].length === 1 && rows[rows.length - 1][0] === '') rows.pop(); // trailing newline
  return rows;
}

export function colLetters(n) { let s = ''; for (n++; n > 0; n = Math.floor((n - 1) / 26)) s = String.fromCharCode(65 + ((n - 1) % 26)) + s; return s; }

// Text as typed -> a cell. Numbers, percentages, booleans and ISO dates are typed; everything else stays text.
export function typed(raw) {
  const t = raw.trim();
  if (/^(TRUE|FALSE)$/i.test(t)) return { v: t.toUpperCase() === 'TRUE', t: 'bool' };
  const n = t.replace(/^([-+]?)[$€£]/, '$1').replace(/(\d),(?=\d{3}(\D|$))/g, '$1');
  if (/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(n) && n !== '') return { v: Number(n) };
  if (/^[-+]?(\d+\.?\d*|\.\d+)%$/.test(n)) return { v: Number((parseFloat(n) / 100).toPrecision(12)), fmt: '0%' };
  if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return { v: t, t: 'date' };
  return { v: raw };
}

function htmlGrid(html) {
  const table = new DOMParser().parseFromString(html, 'text/html').querySelector('table');
  if (!table) return null;
  const grid = [];
  for (const tr of table.rows) {
    const row = [];
    for (const td of tr.cells) {
      const f = td.getAttribute('x:fmla');
      row.push(f && f[0] === '=' ? f.slice(1) : null);
      for (let k = 1; k < (+td.getAttribute('colspan') || 1); k++) row.push(null);
    }
    grid.push(row);
  }
  return grid;
}

// { text, html? } -> workbook JSON for fromJson, or null if there is nothing to convert.
export function pastedWorkbook(text, html) {
  const rows = parseTsv(text);
  if (!rows.some((r) => r.some((c) => c !== ''))) return null;
  let fm = null;
  try { fm = html ? htmlGrid(html) : null; } catch { /* values only */ }
  if (fm && (fm.length !== rows.length || fm.some((r, i) => r.length !== rows[i].length))) fm = null;
  const cells = {};
  rows.forEach((r, i) => r.forEach((raw, j) => {
    if (raw === '') return;
    const c = typed(raw);
    if (c.t === 'bool') delete c.t;
    const f = fm && fm[i][j];
    if (f) c.f = f;
    cells[colLetters(j) + (i + 1)] = c;
  }));
  return { sheets: [{ name: 'Sheet1', cells }], names: {} };
}
