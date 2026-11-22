'use strict';
// The .xlsx reader, on small packages built in the test (stored ZIP entries), so no binary fixtures are needed.
const test = require('node:test');
const assert = require('node:assert');
const { loadXlsx } = require('../src/xlsx');
const { dumpsWorkbook } = require('../src');
const { serialToDate, isDateFormat } = require('../src/xlsx');

const CRC = (() => {
  const t = [];
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t.push(c >>> 0);
  }
  return t;
})();
const crc32 = (b) => {
  let c = 0xffffffff;
  for (const x of b) c = CRC[(c ^ x) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};

function zip(files) {
  const parts = [];
  const central = [];
  let offset = 0;
  for (const [name, text] of Object.entries(files)) {
    const nameB = Buffer.from(name);
    const data = Buffer.from(text);
    const h = Buffer.alloc(30);
    h.writeUInt32LE(0x04034b50, 0);
    h.writeUInt16LE(20, 4);
    h.writeUInt32LE(crc32(data), 14);
    h.writeUInt32LE(data.length, 18);
    h.writeUInt32LE(data.length, 22);
    h.writeUInt16LE(nameB.length, 26);
    parts.push(h, nameB, data);
    const c = Buffer.alloc(46);
    c.writeUInt32LE(0x02014b50, 0);
    c.writeUInt16LE(20, 4);
    c.writeUInt16LE(20, 6);
    c.writeUInt32LE(crc32(data), 16);
    c.writeUInt32LE(data.length, 20);
    c.writeUInt32LE(data.length, 24);
    c.writeUInt16LE(nameB.length, 28);
    c.writeUInt32LE(offset, 42);
    central.push(c, nameB);
    offset += 30 + nameB.length + data.length;
  }
  const cd = Buffer.concat(central);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(central.length / 2, 8);
  end.writeUInt16LE(central.length / 2, 10);
  end.writeUInt32LE(cd.length, 12);
  end.writeUInt32LE(offset, 16);
  return Buffer.concat([...parts, cd, end]);
}

const NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"';
const workbook = (inner, pr = '') => `<?xml version="1.0"?><workbook ${NS} xmlns:r="r">${pr}${inner}</workbook>`;
const rels = (n) =>
  `<Relationships>${Array.from({ length: n }, (_, i) => `<Relationship Id="rId${i + 1}" Target="worksheets/sheet${i + 1}.xml"/>`).join('')}</Relationships>`;
const sheetXml = (rows, extra = '') => `<worksheet ${NS}>${extra}<sheetData>${rows}</sheetData></worksheet>`;

function load(files) {
  return loadXlsx(zip(files));
}

test('values, shared strings, inline strings, booleans, errors and formulas with cached results', () => {
  const wb = load({
    'xl/workbook.xml': workbook('<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets>'),
    'xl/_rels/workbook.xml.rels': rels(1),
    'xl/sharedStrings.xml': `<sst ${NS}><si><t>Revenue</t></si><si><r><t>Rich </t></r><r><t>text</t></r></si></sst>`,
    'xl/worksheets/sheet1.xml': sheetXml(
      '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="inlineStr"><is><t>inline</t></is></c></row>' +
        '<row r="2"><c r="A2"><v>1200</v></c><c r="B2" t="b"><v>1</v></c><c r="C2" t="e"><v>#DIV/0!</v></c></row>' +
        '<row r="3"><c r="A3"><f>A2*2</f><v>2400</v></c><c r="B3" t="str"><f>"a"&amp;"b"</f><v>ab</v></c><c r="C3"><f>A2+1</f></c></row>'
    ),
  });
  const { text } = dumpsWorkbook(wb);
  assert.match(text, /\n1\|Revenue\|Rich text\|inline\n/);
  assert.match(text, /\n2\|1200\|TRUE\|#DIV\/0!\n/);
  assert.match(text, /\n3\|2400\|ab\|\?\n/);
  assert.match(text, /A3 = A2\*2\nB3 = "a"&"b"\nC3 = A2\+1/);
  assert.match(text, /note: '\? = formula/);
});

test('shared formulas are expanded, then written as a fill range', () => {
  const wb = load({
    'xl/workbook.xml': workbook('<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets>'),
    'xl/_rels/workbook.xml.rels': rels(1),
    'xl/worksheets/sheet1.xml': sheetXml(
      '<row r="1"><c r="A1"><v>1</v></c><c r="B1"><f t="shared" ref="B1:B3" si="0">A1*$C$1</f><v>1</v></c></row>' +
        '<row r="2"><c r="A2"><v>2</v></c><c r="B2"><f t="shared" si="0"/><v>2</v></c></row>' +
        '<row r="3"><c r="A3"><v>3</v></c><c r="B3"><f t="shared" si="0"/><v>3</v></c></row>'
    ),
  });
  assert.match(dumpsWorkbook(wb).text, /```formulas\nB1:B3 = A1\*\$C\$1\n```/);
});

test('array formulas: the results are in the grid and the formula is in an arrays block', () => {
  const wb = load({
    'xl/workbook.xml': workbook('<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets>'),
    'xl/_rels/workbook.xml.rels': rels(1),
    'xl/worksheets/sheet1.xml': sheetXml(
      '<row r="1"><c r="A1"><v>1</v></c><c r="B1"><f t="array" ref="B1:B2">A1:A2*2</f><v>2</v></c></row><row r="2"><c r="A2"><v>2</v></c><c r="B2"><v>4</v></c></row>'
    ),
  });
  const { text, warnings } = dumpsWorkbook(wb);
  assert.match(text, /\n1\|1\|2\n2\|2\|4\n/);
  assert.doesNotMatch(text, /```formulas/);
  assert.match(text, /```arrays\nB1:B2 = A1:A2\*2\n```/);
  assert.strictEqual(warnings.length, 0);
});

test('sheet states, frozen panes, merges, global and sheet-scoped names; built-in names are left out', () => {
  const wb = load({
    'xl/workbook.xml': workbook(
      '<sheets><sheet name="One" sheetId="1" r:id="rId1"/><sheet name="Two" sheetId="2" state="veryHidden" r:id="rId2"/></sheets>' +
        '<definedNames><definedName name="Growth">One!$B$2</definedName><definedName name="Local" localSheetId="1">Two!$A$1</definedName>' +
        '<definedName name="_xlnm.Print_Area" localSheetId="0">One!$A$1:$B$2</definedName></definedNames>'
    ),
    'xl/_rels/workbook.xml.rels': rels(2),
    'xl/worksheets/sheet1.xml': sheetXml(
      '<row r="1"><c r="A1" t="inlineStr"><is><t>t</t></is></c></row>',
      '<sheetViews><sheetView><pane xSplit="1" ySplit="1" topLeftCell="B2" state="frozen"/></sheetView></sheetViews>'
    ).replace('</sheetData>', '</sheetData><mergeCells><mergeCell ref="A1:C1"/></mergeCells>'),
    'xl/worksheets/sheet2.xml': sheetXml('<row r="1"><c r="A1"><v>1</v></c></row>'),
  });
  const { text } = dumpsWorkbook(wb);
  assert.match(text, /# Sheet: One\n\n```meta\nfreeze: B2\n```/);
  assert.match(text, /# Sheet: Two\n\n```meta\nhidden: veryHidden\n```/);
  assert.match(text, /```merges\nA1:C1\n```/);
  assert.match(text, /```names\nGrowth = One!\$B\$2\nTwo!Local = Two!\$A\$1\n```/);
  assert.doesNotMatch(text, /Print_Area/);
});

test('numbers with a date format become dates, date-times and times; number formats are carried', () => {
  const styles = `<styleSheet ${NS}><numFmts count="1"><numFmt numFmtId="164" formatCode="yyyy-mm-dd hh:mm:ss"/></numFmts>` +
    '<cellXfs count="4"><xf numFmtId="0"/><xf numFmtId="14"/><xf numFmtId="164"/><xf numFmtId="9"/></cellXfs></styleSheet>';
  const wb = load({
    'xl/workbook.xml': workbook('<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets>'),
    'xl/_rels/workbook.xml.rels': rels(1),
    'xl/styles.xml': styles,
    'xl/worksheets/sheet1.xml': sheetXml(
      '<row r="1"><c r="A1" s="1"><v>46302</v></c><c r="B1" s="2"><v>46302.604224537</v></c><c r="C1" s="2"><v>0.5</v></c><c r="D1" s="3"><v>0.12</v></c></row>'
    ),
  });
  const { text } = dumpsWorkbook(wb);
  assert.match(text, /\n1\|2026-10-07\|2026-10-07T14:30:05\|12:00:00\|0\.12\n/);
  assert.match(text, /A1 = mm-dd-yy\nB1:C1 = yyyy-mm-dd hh:mm:ss\nD1 = 0%/);
});

test('date serials: the 1900 leap-year bug and the 1904 system', () => {
  assert.deepStrictEqual(serialToDate(1, false), { t: 'date', v: '1900-01-01' });
  assert.deepStrictEqual(serialToDate(59, false), { t: 'date', v: '1900-02-28' });
  assert.deepStrictEqual(serialToDate(61, false), { t: 'date', v: '1900-03-01' });
  assert.deepStrictEqual(serialToDate(0, true), { t: 'time', v: '00:00:00' });
  assert.deepStrictEqual(serialToDate(1, true), { t: 'date', v: '1904-01-02' });
});

test('which formats are dates', () => {
  for (const f of ['yyyy-mm-dd', 'mm-dd-yy', 'h:mm:ss', '[h]:mm:ss', 'd-mmm-yy;@']) assert.ok(isDateFormat(f), f);
  for (const f of ['General', '0.00', '#,##0', '0%', '"day"0', '[Red]0.0', '@']) assert.ok(!isDateFormat(f), f);
});

test('a file that is not an .xlsx is refused', () => {
  assert.throws(() => loadXlsx(Buffer.from('hello')), /not a ZIP/);
  assert.throws(() => load({ 'a.txt': 'x' }), /xl\/workbook\.xml is missing/);
});

test('an archive that is already unzipped gives the same workbook as the zip', () => {
  const files = {
    'xl/workbook.xml': workbook('<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets>'),
    'xl/_rels/workbook.xml.rels': rels(1),
    'xl/worksheets/sheet1.xml': sheetXml('<row r="1"><c r="A1"><v>2</v></c><c r="B1"><f>A1*3</f><v>6</v></c></row>'),
  };
  const archive = { read: (name) => (name in files ? files[name] : null) };
  assert.strictEqual(dumpsWorkbook(loadXlsx(archive)).text, dumpsWorkbook(load(files)).text);
});

test('empty text is an empty cell, and an empty <f/> is the text "="', () => {
  const wb = load({
    'xl/workbook.xml': workbook('<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets>'),
    'xl/_rels/workbook.xml.rels': rels(1),
    'xl/worksheets/sheet1.xml': sheetXml(
      '<row r="1"><c r="A1" t="inlineStr"><is><t>a</t></is></c><c r="B1" t="inlineStr"><is><t>b</t></is></c></row>' +
        '<row r="2"><c r="A2" t="e"><f></f><v>#VALUE!</v></c><c r="B2"><v>2</v></c></row>' +
        '<row r="3"><c r="A3" t="inlineStr"><is><t></t></is></c><c r="B3" t="inlineStr"><is><t></t></is></c></row>'
    ),
  });
  const { text } = dumpsWorkbook(wb);
  assert.match(text, /## A1:B2\n/);
  assert.match(text, /\n2\|'=\|2\n/);
  assert.doesNotMatch(text, /\n3\|/);
  assert.doesNotMatch(text, /```formulas/);
});

test('a defined name with no target is left out', () => {
  const wb = load({
    'xl/workbook.xml': workbook('<sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets><definedNames><definedName name="Real">S!$A$1</definedName><definedName name="_xlfn_SINGLE"></definedName></definedNames>'),
    'xl/_rels/workbook.xml.rels': rels(1),
    'xl/worksheets/sheet1.xml': sheetXml('<row r="1"><c r="A1"><v>1</v></c></row>'),
  });
  const { text } = dumpsWorkbook(wb);
  assert.match(text, /Real = S!\$A\$1/);
  assert.doesNotMatch(text, /_xlfn_SINGLE/);
});
