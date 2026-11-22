'use strict';
// Runs the conformance kit's writer cases in-process (no Python needed). The same cases run through the kit's own
// checker, as a separate program, in CI: python conformance/check.py --encoder "node js/bin/cellprose-encode.js".
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { dumpsWorkbook, fromJson } = require('../src');

const CASES = path.join(__dirname, '..', '..', 'conformance', 'cases');

for (const id of fs.readdirSync(CASES).sort()) {
  const meta = JSON.parse(fs.readFileSync(path.join(CASES, id, 'case.json'), 'utf8'));
  if (!meta.write) continue;
  test(`kit ${id}`, () => {
    const wb = fromJson(JSON.parse(fs.readFileSync(path.join(CASES, id, meta.write.input), 'utf8')));
    const { text, warnings } = dumpsWorkbook(wb, { maxRows: wb.options.max_rows });
    assert.strictEqual(text, fs.readFileSync(path.join(CASES, id, meta.write.expected), 'utf8'));
    assert.strictEqual(warnings.length > 0, !!meta.write.warns);
  });
}
