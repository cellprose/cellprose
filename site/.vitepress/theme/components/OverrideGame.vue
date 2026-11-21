<script setup>
// Find the typed-in numbers by eye, then see them as gaps in the fill ranges. The answer is not stored here: it is
// worked out from the formulas block the JS writer produces for the forecast workbook.
import { onMounted, ref, computed } from 'vue';
import { loadSample } from '../lib/samples.js';
import { core, cellsOf, overrides } from '../lib/sheet.js';
import { run, armName } from '../lib/run.js';

// Accuracy on the benchmark's "typed-in or formula?" questions, by arm: the mean over the four models of the
// 11 Nov 2026 run on the real-world set (site/data/run.json).
const RW = run.corpora.realworld;
const HC = ['csv', 'markitdown', 'cellprose_v03'].map((e) => {
  const xs = RW.by_task.filter((t) => t.arm === e).map((t) => t.hardcode);
  return { e, name: armName(e), acc: (xs.reduce((a, b) => a + b, 0) / xs.length).toFixed(1) };
});

const ROWS = 5, COLS = 14;
const grid = ref([]);
const truth = ref(new Set());
const picks = ref(new Set());
const done = ref(false);
const reveal = ref('');
const hits = computed(() => [...picks.value].filter((a) => truth.value.has(a)).length);

onMounted(async () => {
  const s = await loadSample('11_forecast_overrides');
  const wb = core.parse(s.text), sh = wb.sheets[0], cells = cellsOf(wb, sh);
  truth.value = overrides(wb, sh, cells);
  const rows = [];
  for (let r = 1; r <= ROWS; r++) {
    const row = [];
    for (let c = 1; c <= COLS; c++) {
      const a = core.addr(c, r), x = cells[a];
      row.push({ a, text: x ? (x.type === 'number' ? Number(x.value).toLocaleString('en-US') : x.text) : '', num: x?.type === 'number', pick: r >= 2 && c >= 3 && c <= 13 && x?.type === 'number' });
    }
    rows.push(row);
  }
  grid.value = rows;
  // The formulas lines for rows 2-5, with each gap called out under the range it interrupts.
  const lines = [];
  const fills = sh.regions[0].formulas.filter((f) => f.range.r1 >= 2 && f.range.r1 <= ROWS && f.range.c2 >= 3 && f.range.c1 <= 13 && f.range.r1 === f.range.r2);
  fills.sort((x, y) => x.range.r1 - y.range.r1 || x.range.c1 - y.range.c1);
  for (const f of fills) {
    lines.push(`${core.rangeStr(f.range)} = ${f.formula}`);
    const next = core.addr(f.range.c2 + 1, f.range.r1);
    if (truth.value.has(next)) lines.push(`      ↳ ${next} is in no range: typed in`);
  }
  reveal.value = lines.join('\n');
});

function toggle(cell) {
  if (!cell.pick || done.value) return;
  const p = new Set(picks.value);
  p.has(cell.a) ? p.delete(cell.a) : p.add(cell.a);
  picks.value = p;
}
const cls = (cell) => [cell.num ? '' : 't', cell.pick ? 'pick' : '',
  done.value && truth.value.has(cell.a) ? 'k-ov' : '',
  !done.value && picks.value.has(cell.a) ? 'picked' : '',
  done.value && picks.value.has(cell.a) && !truth.value.has(cell.a) ? 'wrong' : ''];
function reset() { done.value = false; picks.value = new Set(); }
</script>

<template>
  <div class="card pane"><div class="gridwrap">
    <table class="xl"><tbody>
      <tr><th></th><th v-for="c in 14" :key="c">{{ String.fromCharCode(64 + c) }}</th></tr>
      <tr v-for="(row, i) in grid" :key="i"><th>{{ i + 1 }}</th>
        <td v-for="cell in row" :key="cell.a" :class="cls(cell)" :data-a="cell.a" @click="toggle(cell)">{{ cell.text }}</td></tr>
    </tbody></table>
  </div></div>
  <div class="row" style="margin-top:12px">
    <button class="btn" @click="done = true">Reveal with Cellprose</button>
    <button class="btn ghost" @click="reset">Reset</button>
    <span class="muted small" v-if="!done">{{ picks.size }} cell{{ picks.size === 1 ? '' : 's' }} picked</span>
    <span class="muted small" v-else>You found {{ hits }} of {{ truth.size }}. Cellprose shows all {{ truth.size }} as gaps in its fill ranges.</span>
  </div>
  <div v-if="done" style="margin-top:12px">
    <pre class="term">{{ reveal }}</pre>
    <div class="card hc">
      <div class="small muted">What models did on this kind of question in the benchmark (typed-in or formula?), by format</div>
      <div v-for="r in HC" :key="r.e" class="crow" :class="{ sm: r.e === 'cellprose_v03' }">
        <span class="lab">{{ r.name }}</span>
        <div class="bars"><span class="out" :style="{ width: r.acc + '%' }"></span></div>
        <span class="delta" :class="r.e === 'cellprose_v03' ? 'good' : 'base'">{{ r.acc }}%</span>
      </div>
      <div class="tiny muted">Mean of four models on the {{ RW.workbooks }} real-world workbooks, {{ run.repeats }} repeats each, partial credit. <a href="./benchmarks#tasks">By model and question type</a>.</div>
    </div>
    <div class="finding">
      <div class="card"><b>F2, J2</b>Bookings jump to round numbers. F2 is 117,000 where the formula gives 116,986.</div>
      <div class="card"><b>H4</b>Holds 52, exactly what its formula would give. No values-only format can reveal it.</div>
      <div class="card"><b>K5</b>480,000 where 58 × 9,500 = 551,000. The range <code>B5:J5</code> stops just before it.</div>
    </div>
  </div>
</template>
