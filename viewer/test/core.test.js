'use strict';
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const C = require('../core/cellprose-core.js');

const golden = fs.readFileSync(path.join(__dirname, '../../tests/golden/design_example.sheet.md'), 'utf8');
const wb = C.parse(golden);

test('parses sheets, regions, names', () => {
  assert.equal(wb.version, '0.3');
  assert.deepEqual(wb.sheets.map(s => s.name), ['P&L']);
  assert.equal(wb.sheets[0].regions[0].label, 'A1:F4');
  assert.equal(wb.names.Growth, 'Assumptions!$B$2');
});

test('cell value and type', () => {
  const i = C.cellInfo(wb, 'P&L', 'D2');
  assert.equal(i.value, 1399.68);
  assert.equal(i.type, 'number');
  assert.equal(C.cellInfo(wb, 'P&L', 'A2').text, 'Units');
  assert.equal(C.cellInfo(wb, 'P&L', 'A1').type, 'empty');
});

test('fill ranges expand with shifted references', () => {
  assert.equal(C.cellInfo(wb, 'P&L', 'D4').formula, '=D2*D3');
  assert.equal(C.cellInfo(wb, 'P&L', 'C2').formula, '=B2*(1+Growth)');
  assert.equal(C.cellInfo(wb, 'P&L', 'F4').formula, '=SUM(B4:E4)');
  assert.equal(C.cellInfo(wb, 'P&L', 'B2').formula, null); // typed value
});

test('absolute references do not shift', () => {
  assert.equal(C.shiftFormula('$A$1+A$1+$A1+A1', 2, 3), '$A$1+C$1+$A4+C4');
  assert.equal(C.shiftFormula('"B2"&B2', 1, 0), '"B2"&C2');
  assert.equal(C.shiftFormula("'My Sheet'!B2+LOG10(2)", 0, 1), "'My Sheet'!B3+LOG10(2)");
});

test('precedents, including defined names', () => {
  const p = C.cellInfo(wb, 'P&L', 'D4').precedents.map(r => r.sheet + '!' + C.rangeStr(r.range));
  assert.deepEqual(p, ['P&L!D2', 'P&L!D3']);
  const q = C.cellInfo(wb, 'P&L', 'D2').precedents.map(r => r.sheet + '!' + C.rangeStr(r.range));
  assert.deepEqual(q, ['P&L!C2', 'Assumptions!B2']);
  assert.deepEqual(C.refsOf("'Q1 Data'!A1:B2+X!C3", 'S').map(r => r.sheet), ['Q1 Data', 'X']);
});

test('formats', () => {
  assert.equal(C.cellInfo(wb, 'P&L', 'C4').format, '$#,##0');
  assert.equal(C.cellInfo(wb, 'P&L', 'C3').format, null);
});

test('copy range as TSV', () => {
  assert.equal(C.rangeToTSV(wb, 'P&L', 'A3:C4'), 'Price\t45\t45\nRevenue\t54000\t58320');
});

test('cell escaping (SPEC 5.2)', () => {
  const d = C.decodeCell;
  assert.deepEqual([d("'00123").type, d("'00123").value], ['text', '00123']);
  assert.equal(d("'TRUE").type, 'text');
  assert.equal(d('a\\|b').value, 'a|b');
  assert.equal(d('x<br>y').value, 'x\ny');
  assert.equal(d('\\<br>').value, '<br>');
  assert.equal(d('" x "').value, ' x ');
  assert.equal(d('"""hi"""').value, '"hi"');
  assert.equal(d('2026-10-07').type, 'date');
  assert.equal(d('#DIV/0!').type, 'error');
  assert.equal(d('?').type, 'unknown');
  assert.equal(d('-3.2e-7').value, -3.2e-7);
});

test('escaped pipes do not split cells; elision rows are skipped; loose cells and quoted sheets', () => {
  const t = [
    '---', 'cellprose: 0.3', '---', '', '# Sheet: "Q#1"', '', '## A1:B3', '',
    '#|A|B', '-|-|-', '1|a\\|b|2', '…|…|…', '3|x|=', '',
    '```formulas', 'B3 = A1&"B2"', '```', '', '```cells', 'D5: hello', 'E5 = SUM(B1:B3)  # 7', '```', '',
  ].join('\n');
  const w = C.parse(t);
  assert.equal(w.sheets[0].name, 'Q#1');
  assert.equal(C.cellInfo(w, 'Q#1', 'A1').value, 'a|b');
  assert.equal(C.cellInfo(w, 'Q#1', 'A3').text, 'x');
  assert.equal(C.cellInfo(w, 'Q#1', 'D5').text, 'hello');
  assert.equal(C.cellInfo(w, 'Q#1', 'E5').formula, '=SUM(B1:B3)');
  assert.equal(C.cellInfo(w, 'Q#1', 'E5').value, 7);
});

test('a v0.2 grid with outer pipes is still read', () => {
  const t = ['---', 'sheetmark: 0.2', '---', '', '# Sheet: S', '', '## A1:B2', '', '|#|A|B|', '|-|-|-|', '|1|x|1|', '|2|y||', ''].join('\n');
  const w = C.parse(t);
  assert.equal(C.cellInfo(w, 'S', 'A1').text, 'x');
  assert.equal(C.cellInfo(w, 'S', 'A2').text, 'y');
  assert.equal(C.cellInfo(w, 'S', 'B2').type, 'empty');
});

test('short rows are padded and an arrays block gives every cell of the array its formula', () => {
  const t = ['---', 'cellprose: 0.3', '---', '', '# Sheet: S', '', '## A1:C2', '', '#|A|B|C', '-|-|-|-', '1|1|2|x', '2|2|4', '',
    '```arrays', 'B1:B2 = A1:A2*2', '```', ''].join('\n');
  const w = C.parse(t);
  assert.equal(C.cellInfo(w, 'S', 'C2').type, 'empty');
  assert.equal(C.cellInfo(w, 'S', 'B1').formula, '=A1:A2*2');
  assert.equal(C.cellInfo(w, 'S', 'B2').formula, '=A1:A2*2');
  assert.equal(C.cellInfo(w, 'S', 'A1').formula, null);
});
