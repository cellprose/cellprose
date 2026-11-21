// The git-diff demo: edit one cell of the forecast's XML, run the JS writer on both versions, and diff the two
// .sheet.md texts. Nothing about the diff is typed in by hand.
import SM from './cellprose.gen.js';

// Each edit patches the forecast's worksheet XML (xl/worksheets/sheet1.xml) or shared strings, and the cached total
// Excel would have saved next to it (N5 is SUM(B5:M5)).
export const EDITS = {
  fix: {
    label: 'Fix the October payroll override',
    story: 'K5 held a typed 480,000. Put the formula back and the total follows.',
    patch: (parts) => ({
      'xl/worksheets/sheet1.xml': parts['xl/worksheets/sheet1.xml']
        .replace('<c r="K5" s="0" t="n"><v>480000</v></c>', '<c r="K5" s="0" t="n"><f aca="false">K4*$B$9</f><v>551000</v></c>')
        .replace('<f aca="false">SUM(B5:M5)</f><v>5743000</v>', '<f aca="false">SUM(B5:M5)</f><v>5814000</v>'),
    }),
  },
  override: {
    label: 'Type over a formula',
    story: 'Someone types 600,000 into L5, which was a formula. The fill range splits around it.',
    patch: (parts) => ({
      'xl/worksheets/sheet1.xml': parts['xl/worksheets/sheet1.xml']
        .replace('<c r="L5" s="0" t="n"><f aca="false">L4*$B$9</f><v>570000</v></c>', '<c r="L5" s="0" t="n"><v>600000</v></c>')
        .replace('<f aca="false">SUM(B5:M5)</f><v>5743000</v>', '<f aca="false">SUM(B5:M5)</f><v>5773000</v>'),
    }),
  },
  rename: {
    label: 'Rename a line',
    story: 'Payroll becomes Salaries. One cell changes, so one line does.',
    patch: (parts) => ({ 'xl/sharedStrings.xml': parts['xl/sharedStrings.xml'].replace('>Payroll<', '>Salaries<') }),
  },
};

const PARTS = ['xl/worksheets/sheet1.xml', 'xl/sharedStrings.xml'];

// archive: what unzip() returns. Returns { before, after } as .sheet.md text.
export function diffTexts(archive, editKey, source = 'forecast.xlsx') {
  const edit = EDITS[editKey];
  const parts = Object.fromEntries(PARTS.map((p) => [p, archive.read(p)]));
  const changed = edit.patch(parts);
  for (const [p, t] of Object.entries(changed)) {
    if (t === parts[p]) throw new Error(`The edit "${editKey}" did not change ${p}; the workbook's XML is not what it expects.`);
  }
  const patched = { read: (n) => (n in changed ? changed[n] : archive.read(n)) };
  const run = (a) => SM.dumpsWorkbook(SM.loadXlsx(a), { source }).text;
  return { before: run(archive), after: run(patched) };
}

// A unified diff by longest common subsequence. Fine for the few dozen lines a sheet.md has here.
export function unifiedDiff(a, b, context = 1) {
  const x = a.split('\n'), y = b.split('\n');
  const n = x.length, m = y.length;
  const t = Array.from({ length: n + 1 }, () => new Int32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) t[i][j] = x[i] === y[j] ? t[i + 1][j + 1] + 1 : Math.max(t[i + 1][j], t[i][j + 1]);
  const ops = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (x[i] === y[j]) { ops.push([' ', x[i], i + 1, j + 1]); i++; j++; }
    else if (t[i + 1][j] >= t[i][j + 1]) { ops.push(['-', x[i], i + 1, j + 1]); i++; }
    else { ops.push(['+', y[j], i + 1, j + 1]); j++; }
  }
  for (; i < n; i++) ops.push(['-', x[i], i + 1, m + 1]);
  for (; j < m; j++) ops.push(['+', y[j], n + 1, j + 1]);
  const keep = new Set();
  ops.forEach((o, k) => { if (o[0] !== ' ') for (let d = -context; d <= context; d++) keep.add(k + d); });
  const out = [];
  for (let k = 0; k < ops.length; k++) {
    if (!keep.has(k)) continue;
    let e = k;
    while (e + 1 < ops.length && keep.has(e + 1)) e++;
    const hunk = ops.slice(k, e + 1);
    const a0 = hunk.find((o) => o[0] !== '+') ?? hunk[0], b0 = hunk.find((o) => o[0] !== '-') ?? hunk[0];
    const na = hunk.filter((o) => o[0] !== '+').length, nb = hunk.filter((o) => o[0] !== '-').length;
    out.push({ kind: 'meta', text: `@@ -${a0[2]},${na} +${b0[3]},${nb} @@` });
    for (const [s, line] of hunk) out.push({ kind: s === '+' ? 'add' : s === '-' ? 'del' : 'ctx', text: s + line });
    k = e;
  }
  return out;
}
