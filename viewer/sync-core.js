// Copies the core library next to the extension shell so the extension folder loads unpacked as-is.
// `node sync-core.js` writes it; `node sync-core.js --check` fails when the copy is stale.
const fs = require('node:fs');
const path = require('node:path');
const src = path.join(__dirname, 'core/cellprose-core.js');
const dst = path.join(__dirname, 'extension/cellprose-core.js');
if (process.argv.includes('--check')) {
  if (fs.readFileSync(src, 'utf8') !== fs.readFileSync(dst, 'utf8')) { console.error('extension/cellprose-core.js is stale: run `node sync-core.js`'); process.exit(1); }
} else fs.copyFileSync(src, dst);
