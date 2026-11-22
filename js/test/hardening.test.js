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
