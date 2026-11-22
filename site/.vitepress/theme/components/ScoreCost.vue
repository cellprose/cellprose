<script setup>
// Accuracy against cost per call, from the 11 Nov 2026 run (site/data/run.json, nothing new was run for it).
// One small chart per model, so every point can carry its own label. Cost is shown relative to CSV (CSV = 1x, log scale)
// because the four models' prices differ by more than 20 times. Up is more accurate, left is cheaper. The headline and the
// line under each chart are computed from the same numbers, so they cannot drift from the data.
import { computed, ref } from 'vue';
import { run, MODEL_KEYS, modelName, arm } from '../lib/run.js';

const CORPORA = { realworld: 'Real-world', spreadsheetbench: 'SpreadsheetBench' };
const LEAD = {
  realworld: 'Real-world workbooks have formulas, and CSV falls behind.',
  spreadsheetbench: 'SpreadsheetBench asks about values only, so CSV is already close.',
};
const corpus = ref('realworld');

// The four arms drawn: one-call formats and the shell agent. Every arm is in the table further down the page.
const SHOWN = [
  { a: 'csv', name: 'CSV', fill: '#9aa6a0', above: false, left: true },
  { a: 'markitdown', name: 'MarkItDown', fill: '#c9a227', above: false },
  { a: 'agent_xlsx', name: 'Agent + shell on .xlsx', fill: '#fff', stroke: '#1d4ab0', above: false },
  { a: 'cellprose_v03', name: 'Cellprose in the prompt', fill: '#1d4ab0', above: true, bold: true },
];

const W = 340, H = 270, L = 40, R = 14, T = 14, B = 40;
const X_MIN = 0.4, X_MAX = 3.6;
const yMin = computed(() => (corpus.value === 'realworld' ? 60 : 75));
const x = (r) => L + ((Math.log(r) - Math.log(X_MIN)) / (Math.log(X_MAX) - Math.log(X_MIN))) * (W - L - R);
const Y_MAX = 103;
const y = (a) => T + (1 - (a - yMin.value) / (Y_MAX - yMin.value)) * (H - T - B);
const xTicks = [0.5, 1, 2, 3];
const yTicks = computed(() => { const o = []; for (let v = yMin.value; v <= 100; v += corpus.value === 'realworld' ? 10 : 5) o.push(v); return o; });

const panels = computed(() => MODEL_KEYS.map((m) => {
  const csv = arm(corpus.value, m, 'csv');
  const pts = SHOWN.map((s) => {
    const p = arm(corpus.value, m, s.a);
    return { ...s, acc: p.acc, cost: p.cost, rel: p.cost / csv.cost };
  });
  const cp = pts.find((p) => p.a === 'cellprose_v03');
  const ag = pts.find((p) => p.a === 'agent_xlsx');
  place(pts);
  const note = `Cellprose ${cp.acc.toFixed(1)}% against CSV ${csv.acc.toFixed(1)}%, at ${cp.rel.toFixed(2)}x CSV's cost; the agent scores ${ag.acc.toFixed(1)}%.`;
  return { m, pts, note };
}));

const span = (f) => {
  const v = panels.value.map(f);
  const lo = Math.min(...v), hi = Math.max(...v);
  return [lo, hi];
};
const headline = computed(() => {
  const [cLo, cHi] = span((p) => p.pts.find((q) => q.a === 'cellprose_v03').acc);
  const [vLo, vHi] = span((p) => p.pts.find((q) => q.a === 'csv').acc);
  const [rLo, rHi] = span((p) => p.pts.find((q) => q.a === 'cellprose_v03').rel);
  return `${LEAD[corpus.value]} Cellprose in the prompt scores ${cLo.toFixed(1)}–${cHi.toFixed(1)}% against CSV's ${vLo.toFixed(1)}–${vHi.toFixed(1)}%, for ${rLo.toFixed(2)}–${rHi.toFixed(2)} times CSV's cost.`;
});

const tip = (m, p) => `${modelName(m)}, ${p.name}: ${p.acc.toFixed(1)}% correct, ${p.rel.toFixed(2)}x CSV's cost per call ($${p.cost.toFixed(4)})`;
// Label placement. CSV's label sits to the left of its point and MarkItDown's to the right. The two close points, Cellprose in
// the prompt and the shell agent, are labelled above and below: the higher one above, the lower one below, centred on the point,
// so the two labels never meet and neither covers a dot. Any labels that still overlap are pushed apart, with a leader line.
const LH = 14;
function place(pts) {
  const cp = pts.find((p) => p.a === 'cellprose_v03'), ag = pts.find((p) => p.a === 'agent_xlsx');
  cp.above = cp.acc >= ag.acc; ag.above = !cp.above;
  for (const p of pts) {
    const r = p.bold ? 7 : 5.5, cx = x(p.rel), cy = y(p.acc);
    const width = p.name.length * (p.bold ? 6.6 : 6.1);
    p.cx = cx; p.cy = cy; p.r = r;
    if (p === cp || p === ag) {
      p.anchor = 'middle';
      p.lx = Math.min(Math.max(cx, L + width / 2), W - R - width / 2);
      p.ly = p.above ? cy - r - 5 : cy + r + 12;
      p.x0 = p.lx - width / 2; p.x1 = p.lx + width / 2;
    } else {
      const left = p.left || cx + r + 4 + width > W - R;
      p.anchor = left ? 'end' : 'start';
      p.lx = cx + (left ? -(r + 4) : r + 4);
      p.x0 = left ? p.lx - width : p.lx; p.x1 = left ? p.lx : p.lx + width;
      p.ly = cy + 4;
    }
    p.ly0 = p.ly;
  }
  // A label whose own point is crowded on its left (CSV, usually) moves to the right of the point instead.
  for (const p of pts) {
    if (p === cp || p === ag || p.anchor !== 'end') continue;
    const crowded = pts.some((q) => q !== p && q.cx < p.cx + 4 && q.cx > p.cx - 18 && Math.abs(q.cy - p.cy) < 14);
    if (crowded) { p.anchor = 'start'; p.lx = p.cx + p.r + 4; p.x0 = p.lx; p.x1 = p.lx + p.name.length * 6.1; }
  }
  for (let pass = 0; pass < 30; pass++) {
    const order = [...pts].sort((u, v) => u.ly - v.ly);
    for (let i = 0; i < order.length; i++) for (let j = i + 1; j < order.length; j++) {
      const u = order[i], v = order[j];
      if (u.x1 < v.x0 || v.x1 < u.x0 || v.ly - u.ly >= LH) continue;
      v.ly = u.ly + LH;
    }
    for (const p of pts) p.ly = Math.min(Math.max(p.ly, T + 10), H - B - 4);
  }
  for (const p of pts) p.leader = Math.abs(p.ly - p.ly0) > 6;
}
</script>

<template>
  <div class="row" style="margin-bottom:12px">
    <div class="seg" data-tool="Corpus"><button v-for="(n, k) in CORPORA" :key="k" :aria-pressed="corpus === k" @click="corpus = k">{{ n }}</button></div>
  </div>
  <div class="card sc">
    <p class="sc-head">{{ headline }}</p>
    <p class="sc-how"><b>How to read it:</b> each chart is one model. <b>Up</b> means more answers right. <b>Left</b> means cheaper per call; the dashed line is CSV's cost, and 2x means twice as much. The best place is the top left.</p>
    <div class="sc-grid">
      <figure v-for="p in panels" :key="p.m" class="sc-panel">
        <figcaption class="sc-name">{{ modelName(p.m) }} <span class="sc-better">&#8598; up and left is better</span></figcaption>
        <svg :viewBox="`0 0 ${W} ${H}`" class="sc-svg" role="img"
             :aria-label="`${modelName(p.m)}, ${CORPORA[corpus]} set: ${p.note}`">
          <rect :x="L" :y="T" :width="(x(1) - L)" :height="(y(yMin + (100 - yMin) / 2) - T)" fill="#eaf1fb" opacity=".8" />
          <g stroke="#e3e9e5">
            <line v-for="v in yTicks" :key="'y' + v" :x1="L" :x2="W - R" :y1="y(v)" :y2="y(v)" />
          </g>
          <line :x1="x(1)" :x2="x(1)" :y1="T" :y2="H - B" stroke="#8a968f" stroke-dasharray="4 3" />
          <g font-size="11" fill="#55665d" font-family="var(--mono)">
            <text v-for="v in yTicks" :key="'yt' + v" :x="L - 6" :y="y(v) + 4" text-anchor="end">{{ v }}%</text>
            <text v-for="t in xTicks" :key="'xt' + t" :x="x(t)" :y="H - B + 15" text-anchor="middle">{{ t === 1 ? 'CSV' : t + 'x' }}</text>
            <text :x="(L + W - R) / 2" :y="H - 6" text-anchor="middle">cost per call, relative to CSV (log scale)</text>
          </g>
          <g v-for="q in p.pts" :key="q.a">
            <title>{{ tip(p.m, q) }}</title>
            <circle :cx="x(q.rel)" :cy="y(q.acc)" :r="q.bold ? 7 : 5.5" :fill="q.fill" :stroke="q.stroke || q.fill" stroke-width="2" />
            <line v-if="q.leader" :x1="q.cx" :y1="q.cy" :x2="q.lx" :y2="q.ly - 4" stroke="#8a968f" stroke-width="1" />
            <text :x="q.lx" :y="q.ly" :text-anchor="q.anchor" font-size="11" :font-weight="q.bold ? 700 : 400"
                  :fill="q.bold ? '#1d4ab0' : '#34423b'">{{ q.name }}</text>
          </g>
        </svg>
        <p class="sc-note">{{ p.note }}</p>
      </figure>
    </div>
    <p class="tiny muted">{{ CORPORA[corpus] }} set, {{ run.corpora[corpus].workbooks }} workbooks, {{ run.repeats }} repeats, run of {{ run.date }}, list price, every token uncached. Four of the six arms are drawn; the table under "Every arm, mean per call" below lists all of them. Each model ran at one reasoning setting, so there is no effort curve. Hover a point for its numbers.</p>
  </div>
</template>

<style scoped>
.sc { padding: 14px 16px; display: grid; gap: 12px; }
.sc-head { margin: 0; font-size: 17px; line-height: 1.4; font-weight: 600; }
.sc-how { margin: 0; font-size: 14px; line-height: 1.5; color: #34423b; }
.sc-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 20px; }
@media (max-width: 720px) { .sc-grid { grid-template-columns: minmax(0, 1fr); } }
.sc-panel { margin: 0; display: grid; gap: 4px; }
.sc-name { font-weight: 600; font-size: 14px; display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
.sc-better { font-weight: 400; font-size: 12px; color: #1d4ab0; }
.sc-svg { width: 100%; height: auto; display: block; }
.sc-note { margin: 0; font-size: 13px; line-height: 1.45; color: #34423b; }
.tiny { font: 11px/1.5 var(--mono); }
</style>
