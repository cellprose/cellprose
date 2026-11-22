'use strict';
// Formula text handling for the writer: split a formula into literal text and cell references, so two formulas can be
// compared "as filled" (same formula shifted) and a formula can be shifted (shared formulas in .xlsx files).
// Only references are touched. Text in "quotes", 'sheet names', [brackets], function names and defined names is literal.

const MAXCOL = 16384; // XFD
const MAXROW = 1048576;

function colIndex(letters) {
  let n = 0;
  for (const ch of letters.toUpperCase()) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n;
}

function colName(n) {
  let s = '';
  while (n > 0) {
    const m = (n - 1) % 26;
    s = String.fromCharCode(65 + m) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

const IDENT_CHAR = /[\p{L}\p{N}_.\\]/u;
const CELL = /(\$?)([A-Za-z]{1,3})(\$?)(\d+)/y;
const COLS = /(\$?)([A-Za-z]{1,3}):(\$?)([A-Za-z]{1,3})/y;
const ROWS = /(\$?)(\d+):(\$?)(\d+)/y;
const NUMBER = /(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/y;
const IDENT = /[\p{L}_\\][\p{L}\p{N}_.\\]*/uy;

// A reference must not run into a longer word, a function call or a sheet qualifier.
function endsClean(src, end) {
  const next = src[end];
  return next === undefined || !(IDENT_CHAR.test(next) || next === '(' || next === '!');
}

function match(re, src, i) {
  re.lastIndex = i;
  return re.exec(src);
}

// Returns an array whose items are strings (literal text) or references:
//   {k: 'cell', ca, c, ra, r}   {k: 'col', a, c} (one end of A:B)   {k: 'row', a, r} (one end of 1:2)
function scan(src) {
  const parts = [];
  let lit = '';
  const push = (p) => {
    if (lit) parts.push(lit);
    lit = '';
    parts.push(p);
  };
  let i = 0;
  const n = src.length;
  while (i < n) {
    const ch = src[i];
    if (ch === '"' || ch === "'") {
      let j = i + 1;
      while (j < n) {
        if (src[j] === ch) {
          if (src[j + 1] === ch) j += 2;
          else break;
        } else j++;
      }
      lit += src.slice(i, j + 1);
      i = j + 1;
      continue;
    }
    if (ch === '[') {
      let depth = 0;
      let j = i;
      for (; j < n; j++) {
        if (src[j] === '[') depth++;
        else if (src[j] === ']' && --depth === 0) break;
      }
      lit += src.slice(i, j + 1);
      i = j + 1;
      continue;
    }
    if (ch === '$' || /[A-Za-z]/.test(ch) || /[0-9]/.test(ch)) {
      let m = match(CELL, src, i);
      if (m && +m[4] >= 1 && +m[4] <= MAXROW && colIndex(m[2]) <= MAXCOL && endsClean(src, i + m[0].length)) {
        push({ k: 'cell', ca: m[1] === '$', c: colIndex(m[2]), ra: m[3] === '$', r: +m[4] });
        i += m[0].length;
        continue;
      }
      m = match(COLS, src, i);
      if (m && colIndex(m[2]) <= MAXCOL && colIndex(m[4]) <= MAXCOL && endsClean(src, i + m[0].length)) {
        push({ k: 'col', a: m[1] === '$', c: colIndex(m[2]) });
        lit += ':';
        push({ k: 'col', a: m[3] === '$', c: colIndex(m[4]) });
        i += m[0].length;
        continue;
      }
      m = match(ROWS, src, i);
      if (m && +m[2] >= 1 && +m[4] >= 1 && +m[2] <= MAXROW && +m[4] <= MAXROW && endsClean(src, i + m[0].length)) {
        push({ k: 'row', a: m[1] === '$', r: +m[2] });
        lit += ':';
        push({ k: 'row', a: m[3] === '$', r: +m[4] });
        i += m[0].length;
        continue;
      }
      if (/[0-9]/.test(ch)) {
        m = match(NUMBER, src, i);
        lit += m[0];
        i += m[0].length;
        continue;
      }
      m = match(IDENT, src, i);
      if (m) {
        lit += m[0];
        i += m[0].length;
        continue;
      }
    }
    if (ch === '.' && /[0-9]/.test(src[i + 1] || '')) {
      const m = match(NUMBER, src, i);
      lit += m[0];
      i += m[0].length;
      continue;
    }
    lit += ch;
    i++;
  }
  if (lit) parts.push(lit);
  return parts;
}

function refText(p, dr, dc) {
  if (p.k === 'cell') {
    const c = p.ca ? p.c : p.c + dc;
    const r = p.ra ? p.r : p.r + dr;
    if (c < 1 || c > MAXCOL || r < 1 || r > MAXROW) return '#REF!';
    return (p.ca ? '$' : '') + colName(c) + (p.ra ? '$' : '') + r;
  }
  if (p.k === 'col') {
    const c = p.a ? p.c : p.c + dc;
    if (c < 1 || c > MAXCOL) return '#REF!';
    return (p.a ? '$' : '') + colName(c);
  }
  const r = p.a ? p.r : p.r + dr;
  if (r < 1 || r > MAXROW) return '#REF!';
  return (p.a ? '$' : '') + r;
}

// The formula moved by (dr, dc) cells, as Excel's fill handle would move it.
function shift(src, dr, dc) {
  return scan(src).map((p) => (typeof p === 'string' ? p : refText(p, dr, dc))).join('');
}

// A form of the formula that is the same for every cell of a fill: relative references become offsets from (row, col),
// absolute ones stay absolute. Two formulas have equal keys exactly when one is the other shifted.
function fillKey(src, row, col) {
  return scan(src)
    .map((p) => {
      if (typeof p === 'string') return p;
      if (p.k === 'cell') return `\u0001${p.ca ? '$' + p.c : '~' + (p.c - col)},${p.ra ? '$' + p.r : '~' + (p.r - row)}`;
      if (p.k === 'col') return `\u0002${p.a ? '$' + p.c : '~' + (p.c - col)}`;
      return `\u0003${p.a ? '$' + p.r : '~' + (p.r - row)}`;
    })
    .join('');
}

module.exports = { colIndex, colName, scan, shift, fillKey, MAXCOL, MAXROW };
