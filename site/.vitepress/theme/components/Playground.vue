<script setup>
// Pick a benchmark workbook or open your own .xlsx. Both go through the same path: the file is unzipped here, the JS
// writer turns it into Cellprose, and the viewer parses that text. Nothing is uploaded.
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { makeViewer } from '../lib/viewer.js';
import { SAMPLES, loadSample } from '../lib/samples.js';
import { convert, convertPasted, toCsv, core } from '../lib/sheet.js';
import { pastedWorkbook } from '../lib/paste.js';

const host = ref(null);
const cur = ref('11_forecast_overrides');
const sizes = ref(null);
const note = ref('');
const warnings = ref([]);
const over = ref(false);
const three = ref(true);
const pasteText = ref('');
let v = null, last = null;

function show(text, csv, file, isSample) {
  last = [text, csv, file];
  v.load(text, csv, file);
  const wb = core.parse(text);
  sizes.value = { md: text.length, csv: csv.length, fills: wb.sheets.reduce((n, s) => n + s.regions.reduce((m, r) => m + r.formulas.length, 0), 0), sample: isSample };
}
async function pick(k) {
  cur.value = k; warnings.value = [];
  try {
    const s = await loadSample(k);
    show(s.text, s.csv, s.file, true);
    note.value = 'A workbook from the benchmark. The CSV is the exact text the benchmark sent; the .sheet.md was written just now, in this page, by the JS writer.';
  } catch (e) { note.value = e.message; }
}
async function open(f) {
  if (!f) return;
  cur.value = '';
  try {
    const { text, warnings: w, wb } = await convert(await f.arrayBuffer(), f.name);
    warnings.value = w;
    show(text, toCsv(wb), f.name, false);
    note.value = 'Converted in this page by the JS writer, the same code the conformance kit checks. Your file was not uploaded anywhere. The CSV is built from the same cells, values only.';
  } catch (e) {
    note.value = `Couldn't read that file: ${e.message} Try an .xlsx saved from Excel, LibreOffice or Google Sheets.`;
  }
}
function convertPaste(text, html) {
  cur.value = '';
  try {
    const doc = pastedWorkbook(text, html);
    if (!doc) { note.value = 'Nothing to convert. Copy a range of cells in Excel or Google Sheets, then paste.'; return; }
    const { text: md, warnings: w, wb } = convertPasted(doc, 'pasted cells');
    warnings.value = w;
    show(md, toCsv(wb), 'pasted cells', false);
    note.value = 'Pasted cells converted in this page by the JS writer. Nothing was uploaded. Formulas come through when Excel puts them on the clipboard; Google Sheets copies values only.';
  } catch (e) { note.value = `Couldn't convert those cells: ${e.message}`; }
}
function onPaste(e) {
  const t = e.target;
  if (t && t.matches && t.matches('input, select, [contenteditable]')) return;
  const cd = e.clipboardData;
  if (!cd || (cd.files && cd.files.length)) { if (cd && cd.files.length) { e.preventDefault(); open(cd.files[0]); } return; }
  const text = cd.getData('text/plain');
  if (!text) return;
  e.preventDefault();
  pasteText.value = text;
  convertPaste(text, cd.getData('text/html'));
}
const onDrop = (e) => { over.value = false; open(e.dataTransfer.files[0]); };
const est = (n) => Math.round(n / 4).toLocaleString('en-US');
const build = () => { v = makeViewer(host.value, { mode: 'bands', tabs: true, three: three.value }); };
async function layout(t) { three.value = t; await nextTick(); build(); if (last) v.load(...last); }
onMounted(() => { build(); pick(cur.value); window.addEventListener('paste', onPaste); });
onBeforeUnmount(() => window.removeEventListener('paste', onPaste));
</script>

<template>
  <div class="row" style="margin-bottom:14px"><div class="seg" data-tool="Sample"><button v-for="(n, k) in SAMPLES" :key="k" :aria-pressed="cur === k" @click="pick(k)">{{ n }}</button></div></div>
  <div class="inputs">
    <label class="drop big" :class="{ over }" @dragenter.prevent="over = true" @dragover.prevent="over = true" @dragleave.prevent="over = false" @drop.prevent="onDrop">
      <span class="drop-title">Drop an .xlsx here, or click to choose one</span>
      <span class="small muted">Converted in your browser. Nothing is uploaded.</span>
      <input type="file" accept=".xlsx,.xlsm" hidden @change="open($event.target.files[0])">
    </label>
    <div class="paste">
      <label class="small" for="pg-paste"><b>Or paste cells</b> copied from Excel or Google Sheets (Ctrl/Cmd+V anywhere on this page)</label>
      <textarea id="pg-paste" v-model="pasteText" rows="4" spellcheck="false" placeholder="Click here and paste. Tab-separated text works too." @paste.stop="onPaste"></textarea>
      <button class="btn" :disabled="!pasteText.trim()" @click="convertPaste(pasteText)">Convert pasted cells</button>
    </div>
  </div>
  <div v-if="sizes" class="sizes">
    <div v-for="[n, c] in [['CSV', sizes.csv], ['Cellprose', sizes.md]]" :key="n" class="card size" :class="{ sm: n === 'Cellprose' }">
      <span class="small muted">{{ n }}</span><span class="n">{{ c.toLocaleString('en-US') }}</span>
      <span class="small muted">characters · about {{ est(c) }} tokens</span>
      <div class="bar"><i :style="{ width: (c / Math.max(sizes.csv, sizes.md)) * 100 + '%' }"></i></div>
    </div>
    <div class="card size"><span class="small muted">Fill ranges</span><span class="n">{{ sizes.fills }}</span><span class="small muted">lines in formulas blocks</span></div>
  </div>
  <p class="small muted" style="margin:8px 0 18px">Token counts are rough estimates (characters ÷ 4), not a tokenizer. Cellprose is often a little larger than CSV; in the benchmark the saving comes from shorter answers.</p>
  <p v-for="w in warnings" :key="w" class="warnbox" style="margin-bottom:10px">{{ w }}</p>
  <div class="row" style="margin-bottom:10px"><div class="seg" data-tool="Layout"><button :aria-pressed="three" @click="layout(true)">Three linked panes</button><button :aria-pressed="!three" @click="layout(false)">One pane, with CSV</button></div></div>
  <div ref="host"></div>
  <p class="small muted" style="margin-top:10px">{{ note }}</p>
</template>
