'use strict';
// The in-memory workbook the writer takes. It is the conformance kit's workbook JSON, with cells in Maps:
//
//   { sheets: [{ name, state, freeze, merges: [..], names: {..}, cells: Map<pos, cell>,
//                comments: Map<pos, text>, validations: [{sqref, type, operator?, formula1, formula2?}],
//                dropped: {charts, images, 'pivot tables', 'conditional formats', hyperlinks} counts }], names: {..} }
//   cell = { v, t, f, fmt, array }
//     v     value: string (text), number, bigint, boolean; a cached result when `f` is set. Absent: none.
//     t     'date' | 'datetime' | 'time' | 'error': v is then an ISO string or the error literal
//     f     formula without the leading '='
//     fmt   number format; absent means General
//     array the anchor of an array formula: its range as a string (`B1:B2`); `true` for a data-table formula, which the
//           format cannot carry
//
// A position is one number, row * 16385 + column, so Maps sort in row-major order.

const { colIndex } = require('./formula');

const STRIDE = 16385;
const posKey = (row, col) => row * STRIDE + col;
const posRow = (k) => Math.floor(k / STRIDE);
const posCol = (k) => k % STRIDE;

function parseAddress(a) {
  const m = /^\$?([A-Za-z]{1,3})\$?(\d+)$/.exec(a);
  if (!m) throw new Error(`bad cell address: ${a}`);
  return posKey(+m[2], colIndex(m[1]));
}

// Conformance-kit workbook JSON (conformance/README.md) -> model.
function fromJson(doc) {
  const sheets = doc.sheets.map((s) => {
    const cells = new Map();
    for (const [addr, c] of Object.entries(s.cells || {})) cells.set(parseAddress(addr), { ...c });
    return {
      name: s.name,
      state: s.state || 'visible',
      freeze: s.freeze || null,
      merges: s.merges || [],
      names: s.names || {},
      cells,
      comments: new Map(Object.entries(s.comments || {}).map(([a, t]) => [parseAddress(a), t])),
      validations: s.validations || [],
      dropped: s.dropped || {},
    };
  });
  return { sheets, names: doc.names || {}, options: doc.options || {} };
}

module.exports = { posKey, posRow, posCol, parseAddress, fromJson, STRIDE };
