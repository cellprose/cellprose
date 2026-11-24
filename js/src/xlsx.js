'use strict';
// .xlsx -> model. Reads the parts the format needs (workbook, sheets, shared strings, styles) straight from the package,
// so names, shared formulas, array formulas and cached results come through as the file stores them.

const path = require('path');
const { readZip } = require('./zip');
const { parseXml, child, kids } = require('./xml');
const { colIndex, shift } = require('./formula');
const { posKey, parseAddress, posRow, posCol } = require('./model');
const BUILTIN = require('./builtin-formats');

const MAX_ENUMERATED = 1000000; // cells of one range listed one by one

// Text with _xHHHH_ escapes (ST_Xstring) decoded.
const unescapeX = (s) => s.replace(/_x([0-9a-fA-F]{4})_/g, (m, h) => String.fromCharCode(parseInt(h, 16)));

// Concatenated text of a <si> or <is> element, leaving out phonetic runs.
function richText(node) {
  let out = '';
  for (const c of node.children) {
    if (c.name === 't') out += c.text;
    else if (c.name === 'r') for (const t of kids(c, 't')) out += t.text;
  }
  return unescapeX(out);
}

// Same test as openpyxl.styles.numbers.is_date_format, so both writers agree on which numbers are dates.
const STRIP = /".*?"|\[(?!hh?\]|mm?\]|ss?\])[^\]]*\]/g;
function isDateFormat(fmt) {
  if (!fmt) return false;
  return /(?<![_\\])[dmhysDMHYS]/.test(fmt.split(';')[0].replace(STRIP, ''));
}

const pad = (n, w = 2) => String(n).padStart(w, '0');

// An Excel serial number as {t, v}, following the 1900 / 1904 date systems. Values in [0, 1) are times of day.
function serialToDate(x, epoch1904) {
  const totalSeconds = Math.round(x * 86400);
  if (x >= 0 && x < 1) {
    const s = totalSeconds % 86400;
    return { t: 'time', v: `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}` };
  }
  let days = Math.floor(totalSeconds / 86400);
  const s = totalSeconds - days * 86400;
  // Excel counts 1900-02-29, a day that never existed, so serials 1..59 are one day behind the 1899-12-30 epoch.
  if (!epoch1904 && x > 0 && x < 60) days += 1;
  const base = epoch1904 ? Date.UTC(1904, 0, 1) : Date.UTC(1899, 11, 30);
  const d = new Date(base + days * 86400000);
  const date = `${pad(d.getUTCFullYear(), 4)}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
  if (s === 0) return { t: 'date', v: date };
  return { t: 'datetime', v: `${date}T${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}` };
}

function parseNumber(text) {
  if (/^-?\d+$/.test(text) && text.length > 15) return BigInt(text);
  return parseFloat(text);
}

function relsTarget(base, target) {
  return target.startsWith('/') ? target.slice(1) : path.posix.normalize(path.posix.join(path.posix.dirname(base), target));
}

// `file` is a path, a Buffer, or an archive that is already unzipped: any object with read(name) returning the
// part's text or null. The last is how a browser uses this reader: it inflates the parts itself (DecompressionStream)
// and hands them over, since zlib and fs exist only in Node.
function loadXlsx(file) {
  const zip = file && typeof file.read === 'function' ? file : readZip(file);
  const part = (name) => {
    const text = zip.read(name);
    return text === null ? null : parseXml(text);
  };
  const workbook = part('xl/workbook.xml');
  if (!workbook) throw new Error('not an .xlsx workbook (xl/workbook.xml is missing)');
  const rels = new Map();
  for (const r of kids(part('xl/_rels/workbook.xml.rels'), 'Relationship')) rels.set(r.attrs.Id, relsTarget('xl/workbook.xml', r.attrs.Target));
  const epoch1904 = /^(1|true)$/.test((child(workbook, 'workbookPr') || { attrs: {} }).attrs.date1904 || '');

  const shared = [];
  const sst = part('xl/sharedStrings.xml');
  if (sst) for (const si of kids(sst, 'si')) shared.push(richText(si));

  // Style index -> number format string.
  const custom = new Map();
  const xfFormats = [];
  const styles = part('xl/styles.xml');
  if (styles) {
    for (const nf of kids(child(styles, 'numFmts'), 'numFmt')) custom.set(nf.attrs.numFmtId, nf.attrs.formatCode);
    for (const xf of kids(child(styles, 'cellXfs'), 'xf')) {
      const id = xf.attrs.numFmtId || '0';
      xfFormats.push(custom.has(id) ? custom.get(id) : BUILTIN[id] || 'General');
    }
  }

  const sheetEls = kids(child(workbook, 'sheets'), 'sheet');
  const sheets = [];
  const sheetIndex = [];
  for (const el of sheetEls) {
    const target = rels.get(el.attrs.id);
    const xml = target && part(target);
    if (!xml || xml.name !== 'worksheet') {
      sheetIndex.push(null); // chartsheets and the like are not sheets of cells
      continue;
    }
    const sheet = {
      name: el.attrs.name, state: el.attrs.state || 'visible', freeze: null, merges: [], names: {}, cells: new Map(),
      comments: new Map(), validations: [], dropped: {},
    };
    readSheet(xml, sheet, { shared, xfFormats, epoch1904 });
    readExtras(xml, sheet, target, part);
    sheetIndex.push(sheet);
    sheets.push(sheet);
  }

  // Defined names (§8). Built-in names (_xlnm.Print_Area and friends) are not the user's names and are left out.
  const names = {};
  for (const dn of kids(child(workbook, 'definedNames'), 'definedName')) {
    if (dn.attrs.name.startsWith('_xlnm.') || !dn.text) continue; // (a name with no target names nothing)
    if (dn.attrs.localSheetId !== undefined) {
      const sheet = sheetIndex[+dn.attrs.localSheetId];
      if (sheet) sheet.names[dn.attrs.name] = dn.text;
    } else names[dn.attrs.name] = dn.text;
  }
  return { sheets, names, options: {} };
}

function readSheet(xml, sheet, ctx) {
  const view = child(child(xml, 'sheetViews'), 'sheetView');
  const pane = child(view, 'pane');
  if (pane && /^frozen/.test(pane.attrs.state || '')) {
    sheet.freeze = pane.attrs.topLeftCell || `${colNameOf(+(pane.attrs.xSplit || 0) + 1)}${+(pane.attrs.ySplit || 0) + 1}`;
  }
  for (const m of kids(child(xml, 'mergeCells'), 'mergeCell')) sheet.merges.push(m.attrs.ref);

  const shared = new Map(); // si -> {master position, formula}
  let row = 0;
  for (const rowEl of kids(child(xml, 'sheetData'), 'row')) {
    row = rowEl.attrs.r ? +rowEl.attrs.r : row + 1;
    let col = 0;
    for (const c of kids(rowEl, 'c')) {
      let pos;
      if (c.attrs.r) {
        pos = parseAddress(c.attrs.r);
        col = posCol(pos);
      } else pos = posKey(row, ++col);
      const cell = readCell(c, pos, shared, ctx);
      if (cell) sheet.cells.set(pos, cell);
    }
  }
}

// Everything on a sheet that is not a cell: comments and data validation (carried, SPEC §8) and the features that are
// only counted for the front matter note (§3, §12). The counts follow what openpyxl reads, so the two writers agree.
function readExtras(xml, sheet, target, part) {
  for (const dv of kids(child(xml, 'dataValidations'), 'dataValidation')) {
    const f1 = child(dv, 'formula1');
    if (!dv.attrs.type || dv.attrs.type === 'none' || dv.attrs.type === 'any' || !f1) continue;
    const f2 = child(dv, 'formula2');
    sheet.validations.push({ sqref: dv.attrs.sqref || '', type: dv.attrs.type, operator: dv.attrs.operator, formula1: f1.text,
      formula2: f2 ? f2.text : undefined });
  }
  sheet.dropped['conditional formats'] = kids(xml, 'conditionalFormatting').reduce((n, cf) => n + kids(cf, 'cfRule').length, 0);
  // openpyxl puts a hyperlink on every cell of its range except merged cells that are not the top-left of their merge;
  // a single-cell link on one of those goes to the merge's top-left cell. The count is of cells holding a link.
  const mergedAway = new Map(); // position of a covered merged cell -> top-left cell of its merge
  const bigMerges = []; // merges too large to list cell by cell (a file can claim A1:XFD1048576): tested as rectangles
  for (const m of sheet.merges) {
    const [a, b = a] = m.split(':').map(parseAddress);
    if ((posRow(b) - posRow(a) + 1) * (posCol(b) - posCol(a) + 1) > MAX_ENUMERATED) {
      bigMerges.push([a, b]);
      continue;
    }
    for (let r = posRow(a); r <= posRow(b); r++) for (let c = posCol(a); c <= posCol(b); c++) if (posKey(r, c) !== a) mergedAway.set(posKey(r, c), a);
  }
  const mergeTop = (k) => {
    if (mergedAway.has(k)) return mergedAway.get(k);
    for (const [a, b] of bigMerges) {
      if (k !== a && posRow(k) >= posRow(a) && posRow(k) <= posRow(b) && posCol(k) >= posCol(a) && posCol(k) <= posCol(b)) return a;
    }
    return undefined;
  };
  const cells = new Set();
  let area = 0;
  for (const h of kids(child(xml, 'hyperlinks'), 'hyperlink')) {
    const ref = h.attrs.ref || '';
    const [a, b = a] = ref.split(':').map(parseAddress);
    if (a === undefined) continue;
    if (!ref.includes(':')) cells.add(mergeTop(a) !== undefined ? mergeTop(a) : a);
    else if ((posRow(b) - posRow(a) + 1) * (posCol(b) - posCol(a) + 1) > 100000) area += (posRow(b) - posRow(a) + 1) * (posCol(b) - posCol(a) + 1);
    else for (let r = posRow(a); r <= posRow(b); r++) for (let c = posCol(a); c <= posCol(b); c++) if (mergeTop(posKey(r, c)) === undefined) cells.add(posKey(r, c));
  }
  sheet.dropped.hyperlinks = cells.size + area;

  // (string slicing, not path.basename: the browser build of this file shims only part of `path`)
  const slash = target.lastIndexOf('/');
  const relsPath = `${target.slice(0, slash)}/_rels/${target.slice(slash + 1)}.rels`;
  const rels = part(relsPath);
  let charts = 0;
  let images = 0;
  let pivots = 0;
  for (const r of kids(rels, 'Relationship')) {
    const type = r.attrs.Type || '';
    const to = relsTarget(target, r.attrs.Target);
    if (type.endsWith('/comments')) {
      const list = child(part(to), 'commentList');
      for (const c of kids(list, 'comment')) {
        const text = child(c, 'text');
        let out = '';
        if (text) for (const t of text.children) out += t.name === 't' ? t.text : t.name === 'r' ? kids(t, 't').map((x) => x.text).join('') : '';
        if (c.attrs.ref && out.trim()) sheet.comments.set(parseAddress(c.attrs.ref), out);   // (not unescaped: openpyxl does not)
      }
    } else if (type.endsWith('/pivotTable')) pivots++;
    else if (type.endsWith('/drawing')) {
      const walk = (n) => {
        for (const k of n.children) {
          if (k.name === 'graphicFrame' && descendant(k, 'chart')) charts++;
          else if (k.name === 'pic') images++;
          else walk(k);
        }
      };
      const d = part(to);
      if (d) walk(d);
    }
  }
  sheet.dropped.charts = charts;
  sheet.dropped.images = images;
  sheet.dropped['pivot tables'] = pivots;
}

function descendant(node, name) {
  for (const k of node.children) if (k.name === name || descendant(k, name)) return true;
  return false;
}

const colNameOf = (n) => require('./formula').colName(n);

function readCell(c, pos, shared, ctx) {
  const type = c.attrs.t || 'n';
  const fEl = child(c, 'f');
  const vEl = child(c, 'v');
  const fmt = ctx.xfFormats[+(c.attrs.s || 0)] || 'General';
  const cell = {};
  let emptyFormula = false;
  if (fmt !== 'General') cell.fmt = fmt;

  if (fEl) {
    const ft = fEl.attrs.t;
    if (ft === 'shared') {
      if (fEl.text) shared.set(fEl.attrs.si, { pos, f: fEl.text });
      const master = shared.get(fEl.attrs.si);
      if (master) cell.f = fEl.text || shift(master.f, posRow(pos) - posRow(master.pos), posCol(pos) - posCol(master.pos));
    } else cell.f = fEl.text;
    if (!cell.f && !ft) { // an empty <f/> has nothing to recompute: it is the text "="
      delete cell.f;
      emptyFormula = true;
    }
    if (ft === 'array') cell.array = fEl.attrs.ref || true;       // the anchor holds the array's range (a string)
    else if (ft === 'dataTable') cell.array = true;               // true: a data table, which the format cannot carry
  }

  let v;
  if (type === 'inlineStr') {
    const is = child(c, 'is');
    if (is) v = richText(is);
  } else if (vEl !== undefined) {
    const text = vEl.text;
    if (type === 's') v = ctx.shared[+text];
    else if (type === 'str') v = unescapeX(text);
    else if (type === 'b') v = text === '1';
    else if (type === 'e') {
      cell.t = 'error';
      v = text;
    } else if (type === 'd') {
      const [d, t = ''] = text.split('T');
      cell.t = t && t.slice(0, 8) !== '00:00:00' ? 'datetime' : 'date';
      v = cell.t === 'date' ? d : `${d}T${t.slice(0, 8)}`;
    } else if (text !== '') {
      v = parseNumber(text);
      if (typeof v === 'number' && v >= 0 && v < 2958466 && isDateFormat(fmt)) { // (9999-12-31 is the last date)
        const d = serialToDate(v, ctx.epoch1904);
        cell.t = d.t;
        v = d.v;
      }
    }
  }
  if (emptyFormula) {
    v = '=';
    delete cell.t;
  }
  if (v !== undefined) cell.v = v;
  return cell.v !== undefined || cell.f !== undefined ? cell : null;
}

module.exports = { loadXlsx, serialToDate, isDateFormat };
