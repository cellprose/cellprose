'use strict';
// Minimal ZIP reader (stored and deflated entries, no ZIP64, no encryption): enough for .xlsx.
const fs = require('fs');
const zlib = require('zlib');

const MAX_PART = 256 * 1024 * 1024; // bytes one part may inflate to
const MAX_TOTAL = 512 * 1024 * 1024; // bytes all parts together may declare

function readZip(file) {
  const buf = Buffer.isBuffer(file) ? file : fs.readFileSync(file);
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 22 - 65535); i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) {
      eocd = i;
      break;
    }
  }
  if (eocd < 0) throw new Error('not a ZIP file (no end-of-central-directory record)');
  const count = buf.readUInt16LE(eocd + 10);
  let p = buf.readUInt32LE(eocd + 16);
  const entries = new Map();
  let total = 0;
  for (let i = 0; i < count; i++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) throw new Error('corrupt ZIP central directory');
    const method = buf.readUInt16LE(p + 10);
    const size = buf.readUInt32LE(p + 20);
    const usize = buf.readUInt32LE(p + 24);
    const nameLen = buf.readUInt16LE(p + 28);
    const extraLen = buf.readUInt16LE(p + 30);
    const commentLen = buf.readUInt16LE(p + 32);
    const offset = buf.readUInt32LE(p + 42);
    const name = buf.toString('utf8', p + 46, p + 46 + nameLen);
    total += usize;
    if (usize > MAX_PART || total > MAX_TOTAL) throw new Error('ZIP expands beyond the size limit; refusing to read it');
    entries.set(name, { method, size, usize, offset });
    p += 46 + nameLen + extraLen + commentLen;
  }
  return {
    has: (name) => entries.has(name),
    read(name) {
      const e = entries.get(name);
      if (!e) return null;
      const start = e.offset + 30 + buf.readUInt16LE(e.offset + 26) + buf.readUInt16LE(e.offset + 28);
      const raw = buf.subarray(start, start + e.size);
      if (e.method === 0) return raw.toString('utf8');
      if (e.method === 8) return zlib.inflateRawSync(raw, { maxOutputLength: Math.max(e.usize, 1) }).toString('utf8');
      throw new Error(`unsupported ZIP compression method ${e.method} for ${name}`);
    },
  };
}

module.exports = { readZip };
