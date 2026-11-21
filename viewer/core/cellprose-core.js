// Cellprose viewer core: parse a v0.2 `.sheet.md` text and answer cell questions.
// No DOM, no network. Works as a classic script (global `CellproseCore`) and as a CommonJS module,
// so the browser extension, the tests and a future review app can all load it unchanged.
(function (root) {
  'use strict';

  // ---------------------------------------------------------------- addresses
  function colToNum(s) {
    let n = 0;
    for (const ch of s) n = n * 26 + (ch.charCodeAt(0) - 64);
    return n;
  }
  function numToCol(n) {
    let s = '';
    while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); }
    return s;
  }
  function parseAddr(a) {
    const m = /^\$?([A-Za-z]{1,3})\$?(\d+)$/.exec(a);
    return m ? { col: colToNum(m[1].toUpperCase()), row: +m[2] } : null;
  }
  function addr(col, row) { return numToCol(col) + row; }
  // "B2:E4" or "B2" -> {c1, r1, c2, r2}
  function parseRange(s) {
    const [a, b] = s.split(':');
    const p = parseAddr(a), q = b ? parseAddr(b) : p;
    if (!p || !q) return null;
    return { c1: Math.min(p.col, q.col), r1: Math.min(p.row, q.row), c2: Math.max(p.col, q.col), r2: Math.max(p.row, q.row) };
  }
  function rangeStr(g) {
    const a = addr(g.c1, g.r1), b = addr(g.c2, g.r2);
    return a === b ? a : a + ':' + b;
  }
  function inRange(g, col, row) { return col >= g.c1 && col <= g.c2 && row >= g.r1 && row <= g.r2; }

  // ---------------------------------------------------------------- cell text
  const ERRORS = new Set(['#REF!', '#DIV/0!', '#N/A', '#NAME?', '#NULL!', '#NUM!', '#VALUE!']);

  // Split a table row on unescaped pipes. `line` has its outer pipes removed.
  function splitRow(line) {
    const out = [];
    let cur = '', i = 0;
    while (i < line.length) {
      const ch = line[i];
      if (ch === '\\' && i + 1 < line.length) { cur += ch + line[i + 1]; i += 2; continue; }
      if (ch === '|') { out.push(cur); cur = ''; i++; continue; }
      cur += ch; i++;
    }
    out.push(cur);
    return out;
  }

  // Decode one cell's text (SPEC 5.2). Returns {type, value, text}; `text` is what to show.
  function decodeCell(raw) {
    if (raw === '') return { type: 'empty', value: null, text: '' };
    if (raw === '?') return { type: 'unknown', value: null, text: '?' };
    let s = raw, quoted = false;
    if (s.length >= 2 && s[0] === '"' && s[s.length - 1] === '"') { quoted = true; s = s.slice(1, -1).replace(/""/g, '"'); }
    const unescaped = s.replace(/\\(.)|<br>/g, (m, c) => (c === undefined ? '\n' : c));
    // `\<br>` unescapes to a literal "<br>": the backslash-escaped `<` followed by "br>".
    if (quoted) return { type: 'text', value: unescaped, text: unescaped };
    if (unescaped[0] === "'") { const t = unescaped.slice(1); return { type: 'text', value: t, text: t }; }
    if (/^-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(unescaped)) return { type: 'number', value: Number(unescaped), text: unescaped };
    if (unescaped === 'TRUE' || unescaped === 'FALSE') return { type: 'boolean', value: unescaped === 'TRUE', text: unescaped };
    if (ERRORS.has(unescaped)) return { type: 'error', value: unescaped, text: unescaped };
    if (/^\d{4}-\d\d-\d\d(T\d\d:\d\d:\d\d)?$/.test(unescaped) || /^\d\d:\d\d:\d\d$/.test(unescaped)) {
      return { type: 'date', value: unescaped, text: unescaped };
    }
    return { type: 'text', value: unescaped, text: unescaped };
  }

  // ---------------------------------------------------------------- formulas
  // Shift relative references in `formula` by (dc, dr); `$` parts stay put. Text in quotes is untouched.
  function shiftFormula(formula, dc, dr) {
    if (!dc && !dr) return formula;
    return formula.split(/("(?:[^"]|"")*")/).map((part, i) => {
      if (i % 2 === 1) return part;
      return part.replace(/(^|[^A-Za-z0-9_.])(\$?)([A-Za-z]{1,3})(\$?)(\d+)(?![A-Za-z0-9_(])/g,
        (m, pre, d1, col, d2, row) => {
          const c = d1 ? colToNum(col.toUpperCase()) : colToNum(col.toUpperCase()) + dc;
          const r = d2 ? +row : +row + dr;
          if (c < 1 || r < 1) return pre + '#REF!';
          return pre + d1 + (d1 ? col : numToCol(c)) + d2 + (d2 ? row : r);
        });
    }).join('');
  }

  // References a formula reads: [{sheet, range: {c1,r1,c2,r2}}]. Defined names are expanded once.
  function refsOf(formula, sheet, names) {
    const out = [];
    const body = formula.replace(/"(?:[^"]|"")*"/g, '""');
    const re = /(?:(?:'((?:[^']|'')+)'|([A-Za-z_][A-Za-z0-9_.]*))!)?(\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?)(?![A-Za-z0-9_(])/g;
    let m;
    while ((m = re.exec(body))) {
      if (m.index > 0 && /[A-Za-z0-9_.]/.test(body[m.index - 1]) && !m[1] && !m[2]) continue;
      const g = parseRange(m[3].replace(/\$/g, ''));
      if (g) out.push({ sheet: m[1] ? m[1].replace(/''/g, "'") : (m[2] || sheet), range: g });
    }
    if (names) {
      for (const id of body.match(/[A-Za-z_][A-Za-z0-9_.]*(?![A-Za-z0-9_.(!])/g) || []) {
        const target = names[id] || names[sheet + '!' + id];
        if (target && !/^\$?[A-Za-z]{1,3}\$?\d+$/.test(id)) out.push(...refsOf(target, sheet, null));
      }
    }
    return out;
  }

  // ---------------------------------------------------------------- parser
  function parseBlockLines(lines) {
    return lines.map(l => l.replace(/\s+#.*$/, '').trim()).filter(Boolean);
  }

  function parse(text) {
    const lines = text.replace(/\r\n?/g, '\n').split('\n');
    const wb = { version: null, sheets: [], names: {} };
    let i = 0;
    if (lines[0] === '---') {
      for (i = 1; i < lines.length && lines[i] !== '---'; i++) {
        const m = /^(?:cellprose|sheetmark):\s*(\S+)/.exec(lines[i]);
        if (m) wb.version = m[1];
      }
      i++;
    }
    let sheet = null, region = null, inNames = false;
    for (; i < lines.length; i++) {
      const line = lines[i];
      let m;
      if (/^```/.test(line)) {
        const kind = line.slice(3).trim();
        const body = [];
        for (i++; i < lines.length && !/^```/.test(lines[i]); i++) body.push(lines[i]);
        const items = parseBlockLines(body);
        if (kind === 'names') {
          for (const it of items) { const k = it.indexOf(' = '); if (k > 0) wb.names[it.slice(0, k)] = it.slice(k + 3); }
        } else if (sheet && kind === 'formulas' && region) {
          for (const it of items) {
            const k = it.indexOf(' = ');
            const g = k > 0 && parseRange(it.slice(0, k));
            if (g) region.formulas.push({ range: g, formula: it.slice(k + 3) });
          }
        } else if (sheet && kind === 'formats' && region) {
          for (const it of items) {
            const k = it.indexOf(' = ');
            const g = k > 0 && parseRange(it.slice(0, k));
            if (g) region.formats.push({ range: g, format: it.slice(k + 3) });
          }
        } else if (sheet && kind === 'cells') {
          for (const raw of body) {
            if ((m = /^([A-Z]+\d+) = (.*?)(?:\s+#\s*(.*))?$/.exec(raw))) {
              const p = parseAddr(m[1]);
              sheet.loose[m[1]] = { col: p.col, row: p.row, formula: m[2], cell: decodeCell(m[3] || '') };
            } else if ((m = /^([A-Z]+\d+):\s?(.*)$/.exec(raw))) {
              const p = parseAddr(m[1]);
              sheet.loose[m[1]] = { col: p.col, row: p.row, formula: null, cell: decodeCell(m[2]) };
            }
          }
        } else if (sheet && kind === 'arrays') {
          for (const it of items) {
            const k = it.indexOf(' = ');
            const g = k > 0 && parseRange(it.slice(0, k));
            if (g) sheet.arrays.push({ range: g, formula: it.slice(k + 3) });
          }
        } else if (sheet && kind === 'merges') {
          for (const it of items) { const g = parseRange(it); if (g) sheet.merges.push(g); }
        }
        continue;
      }
      if ((m = /^# Sheet:\s*(.*)$/.exec(line))) {
        let name = m[1].trim();
        if (name.length > 1 && name[0] === '"' && name.endsWith('"')) name = name.slice(1, -1);
        sheet = { name, regions: [], loose: {}, merges: [], arrays: [] };
        wb.sheets.push(sheet); region = null; inNames = false;
      } else if (/^# Names\s*$/.test(line)) {
        inNames = true; sheet = null; region = null;
      } else if (sheet && (m = /^##\s+([A-Z]+\d+(?::[A-Z]+\d+)?)\s*$/.exec(line))) {
        const g = parseRange(m[1]);
        region = { range: g, label: m[1], cells: {}, formulas: [], formats: [], tableIndex: sheet.regions.length };
        sheet.regions.push(region);
      } else if (region && (/^\|/.test(line) || /^#\|/.test(line)) && !inNames) {
        // v0.3 rows have no outer pipes and the table ends at a blank line; v0.2 rows have both.
        const bare = line[0] === '#';
        const strip = (l) => (bare ? l : l.replace(/^\||\|$/g, ''));
        const isRow = (l) => (bare ? l.trim() !== '' : /^\|/.test(l));
        const cols = [];
        const head = splitRow(strip(line));
        if (head[0] !== '#') continue;
        for (const h of head.slice(1)) cols.push(colToNum(h.trim()));
        i++; // separator row
        for (i++; i < lines.length && isRow(lines[i]); i++) {
          const parts = splitRow(strip(lines[i]));
          const row = parseInt(parts[0], 10);
          if (!(row > 0)) continue; // elision marker row (`…|…`)
          cols.forEach((c, k) => { region.cells[addr(c, row)] = decodeCell(parts[k + 1] === undefined ? '' : parts[k + 1]); });
        }
        i--;
      }
    }
    return wb;
  }

  // ---------------------------------------------------------------- queries
  function findSheet(wb, name) { return wb.sheets.find(s => s.name === name) || null; }

  function regionAt(sheet, col, row) {
    return sheet.regions.find(r => inRange(r.range, col, row)) || null;
  }

  // The formula text in a cell (without `=`), expanded from its fill range; null for typed values.
  function formulaAt(sheet, a) {
    const p = parseAddr(a);
    if (!p) return null;
    if (sheet.loose[a]) return sheet.loose[a].formula;
    for (const f of sheet.arrays) if (inRange(f.range, p.col, p.row)) return f.formula;   // every cell of an array shows its formula
    const region = regionAt(sheet, p.col, p.row);
    if (!region) return null;
    for (const f of region.formulas) {
      if (inRange(f.range, p.col, p.row)) return shiftFormula(f.formula, p.col - f.range.c1, p.row - f.range.r1);
    }
    return null;
  }

  function formatAt(sheet, a) {
    const p = parseAddr(a);
    const region = p && regionAt(sheet, p.col, p.row);
    if (!region) return null;
    for (const f of region.formats) if (inRange(f.range, p.col, p.row)) return f.format;
    return null;
  }

  // Everything the viewer shows for one cell.
  function cellInfo(wb, sheetName, a) {
    const sheet = findSheet(wb, sheetName);
    if (!sheet) return null;
    const p = parseAddr(a);
    if (!p) return null;
    const region = regionAt(sheet, p.col, p.row);
    const key = addr(p.col, p.row);
    const cell = sheet.loose[key] ? sheet.loose[key].cell : region ? region.cells[key] : null;
    if (!cell) return null;
    const formula = formulaAt(sheet, key);
    return {
      sheet: sheetName, address: key, type: cell.type, value: cell.value, text: cell.text,
      formula: formula === null ? null : '=' + formula,
      format: formatAt(sheet, key),
      precedents: formula === null ? [] : refsOf(formula, sheetName, wb.names),
    };
  }

  // Copy a range as a tab-separated grid (pastes into Excel, Sheets and Numbers as cells).
  function rangeToTSV(wb, sheetName, rangeText) {
    const sheet = findSheet(wb, sheetName), g = parseRange(rangeText);
    if (!sheet || !g) return '';
    const rows = [];
    for (let r = g.r1; r <= g.r2; r++) {
      const row = [];
      for (let c = g.c1; c <= g.c2; c++) {
        const info = cellInfo(wb, sheetName, addr(c, r));
        row.push(info ? info.text.replace(/[\t\r\n]+/g, ' ') : '');
      }
      rows.push(row.join('\t'));
    }
    return rows.join('\n');
  }

  const api = {
    parse, cellInfo, formulaAt, formatAt, refsOf, shiftFormula, rangeToTSV, decodeCell,
    findSheet, regionAt, parseAddr, parseRange, rangeStr, addr, inRange, numToCol, colToNum,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.CellproseCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
