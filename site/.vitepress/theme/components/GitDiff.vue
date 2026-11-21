<script setup>
// Pick an edit to the forecast. The page patches the workbook's XML, runs the JS writer on the old and new versions,
// and shows the real diff of the two .sheet.md files next to what git says about the .xlsx.
import { onMounted, ref, computed } from 'vue';
import { withBase } from 'vitepress';
import { unzip } from '../lib/sheet.js';
import { EDITS, diffTexts, unifiedDiff } from '../lib/gitdiff.js';

const key = ref('fix');
const archive = ref(null);
const error = ref('');
onMounted(async () => {
  try {
    const r = await fetch(withBase('/samples/11_forecast_overrides.xlsx'));
    if (!r.ok) throw new Error(`Could not load the forecast (${r.status}).`);
    archive.value = await unzip(await r.arrayBuffer());
  } catch (e) { error.value = e.message; }
});
const lines = computed(() => {
  if (!archive.value) return [];
  try { const { before, after } = diffTexts(archive.value, key.value); return unifiedDiff(before, after); } catch (e) { error.value = e.message; return []; }
});
const changed = computed(() => lines.value.filter((l) => l.kind === 'add' || l.kind === 'del').length);
</script>

<template>
  <div class="row" style="margin-bottom:12px">
    <div class="seg" data-tool="Edit"><button v-for="(e, k) in EDITS" :key="k" :aria-pressed="key === k" @click="key = k">{{ e.label }}</button></div>
    <span class="small muted">{{ EDITS[key].story }}</span>
  </div>
  <div class="diffs">
    <div class="card pane"><div class="pane-bar">git diff forecast.xlsx</div><pre class="diff"><span class="meta">diff --git a/forecast.xlsx b/forecast.xlsx</span><span>Binary files a/forecast.xlsx and b/forecast.xlsx differ</span></pre></div>
    <div class="card pane"><div class="pane-bar">git diff forecast.sheet.md<span class="sp">{{ changed }} line{{ changed === 1 ? '' : 's' }} changed</span></div>
      <pre class="diff"><span v-for="(l, i) in lines" :key="i" :class="l.kind">{{ l.text }}</span><span v-if="!lines.length" class="meta">Running the writer…</span></pre></div>
  </div>
  <p class="small muted" style="margin-top:10px">Both versions of the .sheet.md were written just now, in this page, by the JS writer from the edited workbook. The edited cell and the cached total next to it are patched in the XML; nothing else changes.</p>
  <p v-if="error" class="warnbox">{{ error }}</p>
</template>
