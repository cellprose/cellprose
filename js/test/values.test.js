'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { numberText, textCell } = require('../src/writer');
const { scan, shift, fillKey } = require('../src/formula');

test('typed numbers are exact; integer-valued ones are integers', () => {
  assert.strictEqual(numberText(5, false), '5');
  assert.strictEqual(numberText(0.1 + 0.2, false), '0.30000000000000004');
  assert.strictEqual(numberText(-3.2e-7, false), '-3.2e-07');
  assert.strictEqual(numberText(1e16, false), '10000000000000000');
  assert.strictEqual(numberText(1.5e-10, false), '1.5e-10');
  assert.strictEqual(numberText(0.0001, false), '0.0001');
  assert.strictEqual(numberText(-0, false), '0');
});

test('formula results keep 6 significant figures', () => {
  assert.strictEqual(numberText(1515987.648, true), '1515990');
  assert.strictEqual(numberText(0.2466666667, true), '0.246667');
  assert.strictEqual(numberText(0.0123456789, true), '0.0123457');
  assert.strictEqual(numberText(0.000123456789, true), '0.000123457');
  assert.strictEqual(numberText(1.234567e-5, true), '1.23457e-05');
  assert.strictEqual(numberText(1e-5, true), '1e-05');
  assert.strictEqual(numberText(9.9999995e-5, true), '0.0001');
  assert.strictEqual(numberText(-2.5, true), '-2.5');
  assert.strictEqual(numberText(1234567, true), '1234567'); // integer-valued results are not rounded
});

test('text that reads as another type is prefixed; the rest is escaped', () => {
  assert.strictEqual(textCell('00123'), "'00123");
  assert.strictEqual(textCell('TRUE'), "'TRUE");
  assert.strictEqual(textCell('true'), 'true');
  assert.strictEqual(textCell('=x'), "'=x");
  assert.strictEqual(textCell("'q"), "''q");
  assert.strictEqual(textCell('a|b\\c'), 'a\\|b\\\\c');
  assert.strictEqual(textCell('<br>'), '\\<br>');
  assert.strictEqual(textCell('a\r\nb\rc\nd'), 'a<br>b<br>c<br>d');
  assert.strictEqual(textCell(' x'), '" x"');
  assert.strictEqual(textCell('"x'), '"""x"');
  assert.strictEqual(textCell("'  x"), "''  x");
});

test('formula references: scanning and shifting', () => {
  assert.strictEqual(shift('B2*(1+Growth)', 0, 1), 'C2*(1+Growth)');
  assert.strictEqual(shift('$A2*B$1', 1, 1), '$A3*C$1');
  assert.strictEqual(shift("'Other Sheet'!$A$1+F2", 2, 0), "'Other Sheet'!$A$1+F4");
  assert.strictEqual(shift('SUM(A:A)+SUM($B:C)+SUM(1:2)', 0, 1), 'SUM(B:B)+SUM($B:D)+SUM(1:2)');
  assert.strictEqual(shift('LOG10(A1)+"A1"+Sheet1!B2', 1, 0), 'LOG10(A2)+"A1"+Sheet1!B3');
  assert.strictEqual(shift('1.5E3*A1', 0, 1), '1.5E3*B1');
  assert.strictEqual(shift('A1', 0, -1), '#REF!');
  assert.deepStrictEqual(scan('TAX*2'), ['TAX*2']);
});

test('two formulas are one fill when one is the other shifted', () => {
  assert.strictEqual(fillKey('B2*C$1+$A2', 2, 2), fillKey('C3*D$1+$A3', 3, 3));
  assert.notStrictEqual(fillKey('B2*2', 2, 2), fillKey('B2*2', 2, 3));
  assert.strictEqual(fillKey('$B2', 2, 2), fillKey('$B3', 3, 3)); // a locked column still follows the row
  assert.strictEqual(fillKey('$B2', 2, 2), fillKey('$B2', 2, 3)); // ...and right: the column is locked
  assert.notStrictEqual(fillKey('$B2', 2, 2), fillKey('$B2', 3, 2));
});
