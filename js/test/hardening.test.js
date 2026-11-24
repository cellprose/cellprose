'use strict';
// Malformed or hostile input must fail fast with an error, never hang or exhaust memory.
const test = require('node:test');
const assert = require('node:assert');
const zlib = require('node:zlib');
const { parseXml } = require('../src/xml');
const { readZip } = require('../src/zip');

test('unterminated comment, CDATA, tag or declaration throws instead of looping', () => {
  for (const src of ['<a><!-- never closed', '<a><![CDATA[ never closed', '<a><b', '<a><?xml never closed', '<a></a']) {
    assert.throws(() => parseXml(src), /malformed XML/, src);
  }
});

test('stray closing tags do not pop the root', () => {
  assert.doesNotThrow(() => parseXml('<a></a></a></a>'));
});

test('out-of-range character references are left as written', () => {
  assert.strictEqual(parseXml('<a>&#x110000;</a>').text, '&#x110000;');
});

function zipOf(name, data) {
  const raw = zlib.deflateRawSync(data);
  const nm = Buffer.from(name);
  const local = Buffer.alloc(30);
  local.writeUInt32LE(0x04034b50, 0); local.writeUInt16LE(8, 8);
  local.writeUInt32LE(raw.length, 18); local.writeUInt32LE(data.length, 22); local.writeUInt16LE(nm.length, 26);
  const central = Buffer.alloc(46);
  central.writeUInt32LE(0x02014b50, 0); central.writeUInt16LE(8, 10);
  central.writeUInt32LE(raw.length, 20); central.writeUInt32LE(data.length, 24); central.writeUInt16LE(nm.length, 28);
  const eocd = Buffer.alloc(22);
  eocd.writeUInt32LE(0x06054b50, 0); eocd.writeUInt16LE(1, 8); eocd.writeUInt16LE(1, 10);
  const head = Buffer.concat([local, nm, raw]);
  eocd.writeUInt32LE(central.length + nm.length, 12); eocd.writeUInt32LE(head.length, 16);
  return Buffer.concat([head, central, nm, eocd]);
}

test('a part that declares more than the size limit is refused', () => {
  const buf = zipOf('a.xml', Buffer.from('<a/>'));
  const central = buf.indexOf(Buffer.from([0x50, 0x4b, 0x01, 0x02]));
  buf.writeUInt32LE(0x7fffffff, central + 24);
  assert.throws(() => readZip(buf), /size limit/);
});

test('a part that inflates past its declared size is refused', () => {
  const buf = zipOf('a.xml', Buffer.alloc(1 << 20, 0x41));
  const central = buf.indexOf(Buffer.from([0x50, 0x4b, 0x01, 0x02]));
  buf.writeUInt32LE(100, central + 24);          // the directory lies: says 100 bytes
  assert.throws(() => readZip(buf).read('a.xml'));
});

test('an honest small part still reads', () => {
  assert.strictEqual(readZip(zipOf('a.xml', Buffer.from('<a/>'))).read('a.xml'), '<a/>');
});

test('a long attribute-less token does not stall the parser', () => {
  const t = Date.now();
  parseXml(`<a ${'b'.repeat(200000)}/>`);
  assert.ok(Date.now() - t < 1000, `took ${Date.now() - t} ms`);
});

test('attributes: quotes, spaces around =, and tokens without a value', () => {
  const n = parseXml(`<x:a  p = "1"  lone q='2' r:id="3" =stray/>`);
  assert.deepStrictEqual(n.attrs, { p: '1', q: '2', id: '3' });
});

test('merges and array formulas that claim the whole sheet are read without enumerating them', () => {
  const { loadXlsx } = require('../src/xlsx');
  const { dumpsWorkbook } = require('../src/writer');
  const ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"';
  const parts = {
    'xl/workbook.xml': `<workbook ${ns}><sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>`,
    'xl/_rels/workbook.xml.rels': '<Relationships xmlns="x"><Relationship Id="rId1" Type="x/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
    'xl/worksheets/sheet1.xml': `<worksheet ${ns}><sheetData><row r="1"><c r="A1"><f t="array" ref="A1:XFD1048576">1</f><v>1</v></c><c r="B1"><v>2</v></c></row></sheetData>` +
      '<mergeCells count="1"><mergeCell ref="A2:XFD1048576"/></mergeCells><hyperlinks><hyperlink ref="C5"/></hyperlinks></worksheet>',
  };
  const t = Date.now();
  const { text } = dumpsWorkbook(loadXlsx({ read: (name) => parts[name] ?? null }));
  assert.ok(Date.now() - t < 5000);
  assert.match(text, /A1:XFD1048576 = 1/);
  assert.match(text, /A2:XFD1048576/);
  assert.match(text, /hyperlink/); // C5 sits inside the merge, so it is counted on the merge's top-left cell
});

test('the published package carries the licence', () => {
  const out = require('node:child_process').execSync('npm pack --dry-run --json', { cwd: require('node:path').join(__dirname, '..'), stdio: ['ignore', 'pipe', 'ignore'] });
  const files = JSON.parse(out)[0].files.map((f) => f.path);
  assert.ok(files.includes('LICENSE'), files.join(', '));
});
