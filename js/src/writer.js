'use strict';
// Cellprose v0.3 writer. Input is the in-memory workbook described in model.js; output is the canonical .sheet.md text.
// Written from docs/SPEC.md. Where the spec leaves a detail open, the comments say which choice was made and why.

const { colName, fillKey } = require('./formula');
const { posKey, posRow, posCol, parseAddress } = require('./model');

const VERSION = '0.3';
const LEGEND_A = 'Note: the first field of each table row is its row number, not a cell; column A is the second field.';
const LEGEND_OTHER = 'Note: the first field of each table row is its row number, not a cell; the second field is the first column letter in the header.';
const KEEP_TAIL = 3; // rows kept at the end of an elided region (§9)
const NOTE_MISSING = '? = formula with no cached value; open and save in Excel or LibreOffice to compute';
const NOT_CARRIED = ['charts', 'images', 'pivot tables', 'conditional formats', 'hyperlinks'];   // order of the note (§3)
const NOTE_TABLES = 'data-table formulas are not supported; their cached values are written as typed values';

// ---------------------------------------------------------------------------------------------- values (§5.3)

// Sort in code point order, so non-BMP characters sort the same way as in any language that sorts by code point.
function cpCompare(a, b) {
  const x = Array.from(a);
  const y = Array.from(b);
  const n = Math.min(x.length, y.length);
  for (let i = 0; i < n; i++) {
    const d = x[i].codePointAt(0) - y[i].codePointAt(0);
    if (d) return d;
  }
  return x.length - y.length;
}

function intText(n) {
  return Math.abs(n) < 1e21 ? String(n) : BigInt(n).toString();
}

// Shortest round-trip decimal, spelled as Python's repr spells it: fixed notation for 1e-4 <= |x| < 1e16, otherwise
// d.ddde+XX with at least two exponent digits. (JavaScript's own String() is fixed from 1e-6 to 1e21, which covers the
// fixed range.)
function shortest(x) {
  const [mant, exp] = x.toExponential().split('e');
  const e = parseInt(exp, 10);
  if (e >= -4 && e < 16) return String(x);
  return `${mant}e${e < 0 ? '-' : '+'}${String(Math.abs(e)).padStart(2, '0')}`;
}

// A number that is a formula's cached result: 6 significant figures (§5.3). Exponent form below 1e-4, as %.6g spells it.
function resultText(x) {
  const r = Number(x.toPrecision(6));
  if (Math.abs(r) >= 1e-4) return Number.isInteger(r) ? intText(r) : String(r);
  const [mant, exp] = x.toExponential(5).split('e');
  const m = mant.includes('.') ? mant.replace(/0+$/, '').replace(/\.$/, '') : mant;
  const e = parseInt(exp, 10);
  return `${m}e${e < 0 ? '-' : '+'}${String(Math.abs(e)).padStart(2, '0')}`;
}

function numberText(x, computed) {
  if (typeof x === 'bigint') return x.toString();
  // An integer-valued number is written in full, typed or computed: §5.3 says "an integer-valued result is written as
  // an integer", and rounding 1234567 to 1234570 would change a value the workbook holds exactly.
  if (Number.isInteger(x)) return intText(x);
  return computed ? resultText(x) : shortest(x);
}

// Python's str.isspace() set, which decides "leading or trailing whitespace" in §5.3.
const SPACE = '[\\t\\n\\v\\f\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000]';
const PADDED = new RegExp(`^${SPACE}|${SPACE}$`);

// Text that would otherwise read as another type gets a leading apostrophe (§5.3). The tests are on the start of the
// text, not the whole of it: "2026-10-07 plan" and "#REF! was here" are prefixed too. The spec lists the types but not
// how much of the text must match; prefixing is the safe side, because a reader drops one leading apostrophe.
const LOOKS_NUMERIC = /^[-+]?(?:\p{Nd}+\.?\p{Nd}*|\.\p{Nd}+)(?:[eE][-+]?\p{Nd}+)?\n?$/u;
const LOOKS_DATE = /^\p{Nd}{4}-\p{Nd}{2}-\p{Nd}{2}/u;
const LOOKS_TIME = /^\p{Nd}{2}:\p{Nd}{2}:\p{Nd}{2}/u;
const LOOKS_LITERAL = /^(?:TRUE|FALSE|\?)\n?$/;
const LOOKS_ERROR = /^#[A-Z/0!?]+/;

function looksTyped(s) {
  return LOOKS_NUMERIC.test(s) || LOOKS_DATE.test(s) || LOOKS_TIME.test(s) || LOOKS_LITERAL.test(s) || LOOKS_ERROR.test(s);
}

// Text in a `comments` block (§8): the escapes of §5.3 and <br> for line breaks, with no quoting or apostrophe.
function escapeText(s) {
  return s.replace(/\\/g, '\\\\').replace(/\|/g, '\\|').replace(/<br>/g, '\\<br>').replace(/\r\n|\r|\n/g, '<br>');
}

function textCell(s) {
  if (looksTyped(s) || s.startsWith('=') || s.startsWith("'")) s = "'" + s;
  s = s.replace(/\\/g, '\\\\').replace(/\|/g, '\\|').replace(/<br>/g, '\\<br>');
  s = s.replace(/\r\n|\r|\n/g, '<br>');
  if (PADDED.test(s) || s.startsWith('"')) s = '"' + s.replace(/"/g, '""') + '"';
  return s;
}

function dateTimeText(cell) {
  const v = cell.v;
  if (cell.t === 'time') return v.slice(0, 8);
  const [d, t = ''] = v.split('T');
  return cell.t === 'date' || t.slice(0, 8) === '00:00:00' || t === '' ? d : `${d}T${t.slice(0, 8)}`;
}

// One cell's text in a grid or a `cells` block. `computed` is true when the cell holds a formula.
function valueText(cell, computed) {
  const { v, t } = cell;
  if (v === undefined || v === null) return '';
  if (t === 'error') return String(v);
  if (t === 'date' || t === 'datetime' || t === 'time') return dateTimeText(cell);
  if (typeof v === 'boolean') return v ? 'TRUE' : 'FALSE';
  if (typeof v === 'number' || typeof v === 'bigint') return numberText(v, computed);
  return textCell(String(v));
}

// ---------------------------------------------------------------------------------------------- structure (§5.1, §6.1)

function rangeText(r1, c1, r2, c2) {
  const a = colName(c1) + r1;
  return r1 === r2 && c1 === c2 ? a : `${a}:${colName(c2)}${r2}`;
}

// §5.1: 8-connected components, bounding boxes merged while they overlap; one-cell boxes are loose cells.
function detectRegions(keys) {
  const cells = new Set(keys);
  const seen = new Set();
  let boxes = [];
  for (const start of keys) {
    if (seen.has(start)) continue;
    seen.add(start);
    const stack = [start];
    let r1 = posRow(start);
    let r2 = r1;
    let c1 = posCol(start);
    let c2 = c1;
    while (stack.length) {
      const k = stack.pop();
      const r = posRow(k);
      const c = posCol(k);
      if (r < r1) r1 = r;
      if (r > r2) r2 = r;
      if (c < c1) c1 = c;
      if (c > c2) c2 = c;
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (!dr && !dc) continue;
          const nb = posKey(r + dr, c + dc);
          if (cells.has(nb) && !seen.has(nb)) {
            seen.add(nb);
            stack.push(nb);
          }
        }
      }
    }
    boxes.push({ r1, c1, r2, c2 });
  }
  const overlap = (a, b) => !(a.r2 < b.r1 || b.r2 < a.r1 || a.c2 < b.c1 || b.c2 < a.c1);
  for (let merged = true; merged; ) {
    merged = false;
    outer: for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        if (overlap(boxes[i], boxes[j])) {
          const a = boxes[i];
          const b = boxes[j];
          boxes[i] = { r1: Math.min(a.r1, b.r1), c1: Math.min(a.c1, b.c1), r2: Math.max(a.r2, b.r2), c2: Math.max(a.c2, b.c2) };
          boxes.splice(j, 1);
          merged = true;
          break outer;
        }
      }
    }
  }
  boxes.sort((a, b) => a.r1 - b.r1 || a.c1 - b.c1 || a.r2 - b.r2 || a.c2 - b.c2);
  return {
    regions: boxes.filter((b) => b.r1 !== b.r2 || b.c1 !== b.c2),
    loose: boxes.filter((b) => b.r1 === b.r2 && b.c1 === b.c2).map((b) => [b.r1, b.c1]),
  };
}

// §6.1 and §7: greedy row-major grouping of `items` (Map position -> item) into rectangles of equal items.
// A run grows right, then down, and only over cells not yet taken. Returns [{r1, c1, r2, c2, item}].
function fillRanges(items, equal) {
  const left = new Map(items);
  const out = [];
  for (const k of [...items.keys()].sort((a, b) => a - b)) {
    if (!left.has(k)) continue;
    const r = posRow(k);
    const c = posCol(k);
    const anchor = left.get(k);
    let c2 = c;
    while (left.has(posKey(r, c2 + 1)) && equal(anchor, left.get(posKey(r, c2 + 1)))) c2++;
    let r2 = r;
    for (;;) {
      let ok = true;
      for (let x = c; x <= c2 && ok; x++) {
        const nb = left.get(posKey(r2 + 1, x));
        ok = nb !== undefined && equal(anchor, nb);
      }
      if (!ok) break;
      r2++;
    }
    for (let y = r; y <= r2; y++) for (let x = c; x <= c2; x++) left.delete(posKey(y, x));
    out.push({ r1: r, c1: c, r2, c2, item: anchor });
  }
  return out;
}

// ---------------------------------------------------------------------------------------------- the writer

function hasContent(cell) {
  // Empty text is an empty cell (SPEC §6): it is not part of any region. A formula that returned "" still is.
  return cell !== undefined && ((cell.v !== undefined && cell.v !== null && (cell.v !== '' || cell.f !== undefined)) || cell.f !== undefined);
}

function dumpsWorkbook(wb, options = {}) {
  const maxRows = options.maxRows || null;
  const warnings = [];
  const tables = [];
  const dropped = {};
  let missing = false;
  const tableStarts = new Set();
  let elidedAny = false;
  const body = [];

  for (const sheet of wb.sheets) {
    const name = /[#\n\r]/.test(sheet.name) ? `"${sheet.name}"` : sheet.name;
    body.push(`# Sheet: ${name}`, '');
    const meta = [];
    if (sheet.state && sheet.state !== 'visible') meta.push(`hidden: ${sheet.state === 'hidden' ? 'true' : sheet.state}`);
    if (sheet.freeze) meta.push(`freeze: ${sheet.freeze}`);
    if (meta.length) body.push('```meta', ...meta, '```', '');

    const cells = new Map();
    for (const [k, cell] of sheet.cells) if (hasContent(cell)) cells.set(k, cell);
    const { regions, loose } = detectRegions([...cells.keys()].sort((a, b) => a - b));

    // Array formulas (§6.5): the anchor holds `array` = its range. Every cell inside a range shows a formula result.
    const inArray = new Set();
    const arrayLines = [];
    for (const [k, cell] of [...cells].sort((x, y) => x[0] - y[0])) {   // row-major order of the anchor
      if (typeof cell.array !== 'string') continue;
      const [a, b = a] = cell.array.split(':').map(parseAddress);
      for (let r = posRow(a); r <= posRow(b); r++) for (let c = posCol(a); c <= posCol(b); c++) inArray.add(posKey(r, c));
      arrayLines.push(`${cell.array} = ${cell.f}`);
    }

    for (const { r1, c1, r2, c2 } of regions) {
      let rows = [];
      for (let r = r1; r <= r2; r++) rows.push(r);
      let hidden = [];
      if (maxRows && rows.length > maxRows) {
        const head = Math.max(maxRows - KEEP_TAIL, 1);
        hidden = rows.slice(head, rows.length - KEEP_TAIL);
        rows = [...rows.slice(0, head), ...rows.slice(rows.length - KEEP_TAIL)];
      }
      const cols = [];
      for (let c = c1; c <= c2; c++) cols.push(colName(c));
      tableStarts.add(c1);
      body.push(`## ${rangeText(r1, c1, r2, c2)}`, '', `#|${cols.join('|')}`, Array(cols.length + 1).fill('-').join('|'));
      for (const r of rows) {
        const out = [];
        for (let c = c1; c <= c2; c++) {
          const cell = cells.get(posKey(r, c));
          if (!cell) out.push('');
          else if (cell.array === true) {
            // §12: no syntax for data-table formulas; the cached value is written as a typed value.
            tables.push(`${sheet.name}!${colName(c)}${r}`);
            if (hasValue(cell)) out.push(valueText(cell, false));
            else {
              out.push('?');
              missing = true;
            }
          } else if (typeof cell.array === 'string' && !hasValue(cell)) {
            out.push('?');
            missing = true;
          } else if (inArray.has(posKey(r, c))) out.push(valueText(cell, true));
          else if (cell.f !== undefined && !hasValue(cell)) {
            out.push('?');
            missing = true;
          } else out.push(valueText(cell, cell.f !== undefined));
        }
        while (out.length && out[out.length - 1] === '') out.pop(); // trailing empty cells are left out (§5.2)
        body.push(out.length ? `${r}|${out.join('|')}` : `${r}|`);
        if (hidden.length && r === hidden[0] - 1) body.push(['…', ...cols.map(() => '…')].join('|'));
      }
      body.push('');
      if (hidden.length) {
        elidedAny = true;
        body.push('```elided', `rows: ${hidden[0]}-${hidden[hidden.length - 1]}  # ${hidden.length} rows not shown`, '```', '');
      }

      // The formulas and formats blocks cover every row of the region, shown or not (§9).
      const formulas = new Map();
      const formats = new Map();
      for (let r = r1; r <= r2; r++) {
        for (let c = c1; c <= c2; c++) {
          const cell = cells.get(posKey(r, c));
          if (!cell) continue;
          if (cell.f !== undefined && !cell.array) formulas.set(posKey(r, c), { f: cell.f, key: fillKey(cell.f, r, c) });
          if (cell.fmt && cell.fmt !== 'General') formats.set(posKey(r, c), cell.fmt);
        }
      }
      if (formulas.size) {
        const lines = fillRanges(formulas, (a, b) => a.key === b.key).map((x) => `${rangeText(x.r1, x.c1, x.r2, x.c2)} = ${x.item.f}`);
        body.push('```formulas', ...lines, '```', '');
      }
      if (formats.size) body.push(...formatsBlock(formats));
    }

    if (loose.length) {
      body.push('```cells');
      const formats = new Map();
      for (const [r, c] of loose) {
        const cell = cells.get(posKey(r, c));
        const addr = colName(c) + r;
        if (cell.array === true) {
          tables.push(`${sheet.name}!${addr}`);
          body.push(`${addr}: ${hasValue(cell) ? valueText(cell, false) : '?'}`);
        } else if (typeof cell.array === 'string') {
          body.push(`${addr}: ${hasValue(cell) ? valueText(cell, true) : '?'}`);
          if (!hasValue(cell)) missing = true;
        } else if (cell.f !== undefined) {
          body.push(`${addr} = ${cell.f}  # ${hasValue(cell) ? (cell.v === '' ? '""' : valueText(cell, true)) : '?'}`);
        } else body.push(`${addr}: ${valueText(cell, false)}`);
        if (cell.fmt && cell.fmt !== 'General') formats.set(posKey(r, c), cell.fmt);
      }
      body.push('```', '');
      if (formats.size) body.push(...formatsBlock(formats));
    }

    const merges = [...(sheet.merges || [])].sort(cpCompare);
    if (merges.length) body.push('```merges', ...merges, '```', '');
    if (arrayLines.length) body.push('```arrays', ...arrayLines, '```', '');
    const comments = [...(sheet.comments || [])].sort((a, b) => a[0] - b[0])
      .filter(([, text]) => text.trim()).map(([k, text]) => `${colName(posCol(k))}${posRow(k)}: ${escapeText(text)}`);
    if (comments.length) body.push('```comments', ...comments, '```', '');
    const validations = (sheet.validations || []).flatMap((v) => v.sqref.split(/\s+/).filter(Boolean).map((rng) =>
      `${rng} = ${v.type}${v.operator ? ` ${v.operator}` : ''}: ${v.formula1}${v.formula2 !== undefined ? ` ; ${v.formula2}` : ''}`))
      .sort(cpCompare);
    if (validations.length) body.push('```validation', ...validations, '```', '');
    for (const [k, n] of Object.entries(sheet.dropped || {})) dropped[k] = (dropped[k] || 0) + n;
  }

  const names = Object.entries(wb.names || {}).sort((a, b) => cpCompare(a[0], b[0])).map(([n, t]) => `${n} = ${t}`);
  const local = [];
  for (const sheet of wb.sheets) for (const [n, t] of Object.entries(sheet.names || {})) local.push([sheet.name, n, t]);
  local.sort((a, b) => cpCompare(a[0], b[0]) || cpCompare(a[1], b[1]));
  if (names.length || local.length) {
    body.push('# Names', '', '```names', ...names, ...local.map(([s, n, t]) => `${s}!${n} = ${t}`), '```', '');
  }

  if (tables.length) warnings.push(`data-table formulas are not supported; wrote their cached values as typed values: ${tables.join(', ')}`);
  const head = ['---', `cellprose: ${VERSION}`];
  if (elidedAny) head.push('profile: compact');
  if (options.source) head.push(`source: ${options.source}`);
  const notes = [];
  if (missing) notes.push(NOTE_MISSING);
  if (tables.length) notes.push(NOTE_TABLES);
  const carried = NOT_CARRIED.filter((k) => dropped[k]).map((k) => `${dropped[k]} ${dropped[k] === 1 ? k.slice(0, -1) : k}`);
  if (carried.length) notes.push(`not carried: ${carried.join(', ')}`);
  if (notes.length) head.push(`note: '${notes.join('; ')}'`);
  head.push('---', '');
  if (options.legend !== false && tableStarts.size) head.push(tableStarts.size === 1 && tableStarts.has(1) ? LEGEND_A : LEGEND_OTHER, '');
  return { text: [...head, ...body].join('\n').replace(/\s+$/, '') + '\n', warnings };
}

function hasValue(cell) {
  return cell.v !== undefined && cell.v !== null;
}

function formatsBlock(formats) {
  const lines = fillRanges(formats, (a, b) => a === b).map((x) => `${rangeText(x.r1, x.c1, x.r2, x.c2)} = ${x.item}`);
  return ['```formats', ...lines, '```', ''];
}

module.exports = { dumpsWorkbook, valueText, textCell, numberText, detectRegions, fillRanges };
