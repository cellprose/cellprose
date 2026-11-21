<script setup>
import { onMounted, ref } from 'vue';
import { loadSample } from '../lib/samples.js';
import { num } from '../lib/bench.js';
import { run, range, baselineAcc } from '../lib/run.js';

const s = ref(null);
const turns = range(run.corpora.realworld.arms.filter((a) => a.arm === 'agent_xlsx').map((a) => a.turns));
onMounted(async () => { try { s.value = await loadSample('11_forecast_overrides'); } catch { /* the numbers stay as dashes */ } });
</script>

<template>
  <div class="steps">
    <div class="card step"><span class="num">1 · THE .XLSX</span>
      <span class="big" data-f='=SUM(BYTES(UNZIP("forecast.xlsx")))'>{{ s ? num(s.xmlBytes) : '—' }}</span>
      <p class="muted">bytes of XML in the forecast workbook once unzipped. Formulas, cached values and styling attributes on every cell.</p></div>
    <div class="card step"><span class="num">2 · CELLPROSE</span>
      <span class="big" data-f='=LEN(CELLPROSE("forecast.xlsx"))'>{{ s ? num(s.text.length) : '—' }}</span>
      <p class="muted">characters of Markdown, written in this page by the JS writer. One pipe table per region, then a <code>formulas</code> block of fill ranges.</p></div>
    <div class="card step"><span class="num">3 · THE MODEL</span>
      <span class="big" data-f='=TURNS("Cellprose")'>1 turn</span>
      <p class="muted">to answer, with the formulas in view. An agent that opens the .xlsx with a shell takes {{ turns }} turns to reach the same accuracy ({{ baselineAcc('realworld', 'agent_xlsx') }}% on the real-world benchmark set).</p></div>
  </div>
</template>
