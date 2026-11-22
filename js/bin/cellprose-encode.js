#!/usr/bin/env node
'use strict';
// cellprose-encode FILE [--max-rows N] [--source NAME] [-o OUT]
// FILE is an .xlsx workbook or a conformance-kit workbook (.json). Prints the .sheet.md text on stdout (UTF-8, LF);
// warnings go to stderr.

const fs = require('fs');
const path = require('path');
const { dumpsWorkbook, fromJson, loadXlsx } = require('../src');

function usage(code) {
  process.stderr.write('usage: cellprose-encode FILE.xlsx|FILE.json [--max-rows N] [--source NAME] [-o OUT]\n');
  process.exit(code);
}

function main(argv) {
  const opts = {};
  let file = null;
  let out = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--max-rows') opts.maxRows = parseInt(argv[++i], 10);
    else if (a === '--source') opts.source = argv[++i];
    else if (a === '-o' || a === '--output') out = argv[++i];
    else if (a === '-h' || a === '--help') usage(0);
    else if (a.startsWith('-') && a !== '-') usage(2);
    else if (file === null) file = a;
    else usage(2);
  }
  if (file === null) usage(2);
  let wb;
  if (file.toLowerCase().endsWith('.json')) {
    wb = fromJson(JSON.parse(fs.readFileSync(file, 'utf8')));
    if (opts.maxRows === undefined && wb.options.max_rows) opts.maxRows = wb.options.max_rows;
    if (opts.source === undefined && wb.options.source) opts.source = wb.options.source;
  } else {
    wb = loadXlsx(file);
    if (opts.source === undefined) opts.source = path.basename(file); // as the Python CLI does
  }
  const { text, warnings } = dumpsWorkbook(wb, opts);
  for (const w of warnings) process.stderr.write(`warning: ${w}\n`);
  if (out && out !== '-') fs.writeFileSync(out, text, 'utf8');
  else fs.writeSync(1, text);
}

try {
  main(process.argv.slice(2));
} catch (e) {
  process.stderr.write(`${path.basename(process.argv[1])}: ${e.message}\n`);
  process.exit(1);
}
