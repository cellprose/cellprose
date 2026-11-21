<script setup>
// Accuracy against cost per call, from the 11 Nov 2026 run (site/data/run.json, nothing new was run for it).
// One colour per model. The one-call formats of a model (CSV, MarkItDown, Cellprose in the prompt) are joined by a line,
// in that order; the agent arms are single hollow markers. The points are formats and arms, not effort levels: each
// model ran at one reasoning setting. The cost axis is logarithmic because Sonnet's calls cost more than 20 times Luna's.
import { computed, ref } from 'vue';
import { run, MODEL_KEYS, modelName, armName, arm, money } from '../lib/run.js';

const CORPORA = { realworld: 'Real-world', spreadsheetbench: 'SpreadsheetBench' };
const corpus = ref('realworld');
const ONE_CALL = ['csv', 'markitdown', 'cellprose_v03'];
const AGENTS = ['agent_xlsx', 'agent_xlsx_viewer', 'agent_cellprose_v03'];
const COLOR = { haiku55: '#c4441c', sonnet55: '#1d4ab0', gpt6luna: '#7a4bd1', gpt61sol: '#0b6b37' };

const W = 680, H = 400, L = 54, R = 16, T = 14, B = 46;
const pts = computed(() => MODEL_KEYS.flatMap((m) => [...ONE_CALL, ...AGENTS].map((a) => ({ m, a, ...arm(corpus.value, m, a) }))));
const xs = computed(() => pts.value.map((p) => p.cost));
const xMin = computed(() => Math.pow(10, Math.floor(Math.log10(Math.min(...xs.value)) * 2) / 2));
const xMax = computed(() => Math.pow(10, Math.ceil(Math.log10(Math.max(...xs.value)) * 2) / 2));
const yMin = computed(() => Math.floor(Math.min(...pts.value.map((p) => p.acc)) / 5) * 5);
const x = (c) => L + ((Math.log10(c) - Math.log10(xMin.value)) / (Math.log10(xMax.value) - Math.log10(xMin.value))) * (W - L - R);
const y = (a) => T + (1 - (a - yMin.value) / (100 - yMin.value)) * (H - T - B);
const xTicks = computed(() => {
  const out = [];
  for (let e = Math.log10(xMin.value); e <= Math.log10(xMax.value) + 1e-9; e += 0.5) out.push(Math.pow(10, e));
  return out;
});
const yTicks = computed(() => { const o = []; for (let v = yMin.value; v <= 100; v += 5) o.push(v); return o; });
const line = (m) => ONE_CALL.map((a) => pts.value.find((p) => p.m === m && p.a === a)).map((p) => `${x(p.cost)},${y(p.acc)}`).join(' ');
const star = (cx, cy, r) => Array.from({ length: 10 }, (_, i) => {
  const rad = i % 2 ? r * 0.45 : r, ang = (Math.PI / 5) * i - Math.PI / 2;
  return `${(cx + rad * Math.cos(ang)).toFixed(1)},${(cy + rad * Math.sin(ang)).toFixed(1)}`;
}).join(' ');
const tri = (cx, cy, r) => `${cx},${cy - r} ${cx + r},${cy + r * 0.8} ${cx - r},${cy + r * 0.8}`;
const tick = (c) => (c >= 0.01 ? `$${c.toFixed(2)}` : c >= 0.001 ? `$${c.toFixed(3)}` : `$${c.toFixed(4)}`);
const tip = (p) => `${modelName(p.m)}, ${armName(p.a)}: ${p.acc.toFixed(1)}% correct, ${money(p.cost)} per call`;
</script>

<template>
  <div class="row" style="margin-bottom:12px">
    <div class="seg" data-tool="Corpus"><button v-for="(n, k) in CORPORA" :key="k" :aria-pressed="corpus === k" @click="corpus = k">{{ n }}</button></div>
  </div>
  <div class="card sc">
    <div class="sc-legend" aria-hidden="true">
      <span v-for="m in MODEL_KEYS" :key="m"><i :style="{ background: COLOR[m] }"></i>{{ modelName(m) }}</span>
      <span class="sep"></span>
      <span><svg width="14" height="14"><circle cx="7" cy="7" r="4.5" fill="#55665d" /></svg>CSV</span>
      <span><svg width="14" height="14"><rect x="3" y="3" width="8" height="8" fill="#55665d" /></svg>MarkItDown</span>
      <span><svg width="14" height="14"><polygon :points="star(7, 7.5, 7)" fill="#55665d" /></svg>Cellprose in the prompt</span>
      <span><svg width="14" height="14"><polygon :points="tri(7, 7, 5.5)" fill="none" stroke="#55665d" stroke-width="1.6" /></svg>Agent (shell, viewer or Cellprose tools)</span>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" class="sc-svg" role="img"
         :aria-label="`Accuracy against cost per call for four models in each arm, ${CORPORA[corpus]} set. The same numbers are in the table below.`">
      <g stroke="#e3e9e5">
        <line v-for="v in yTicks" :key="'y' + v" :x1="L" :x2="W - R" :y1="y(v)" :y2="y(v)" />
        <line v-for="c in xTicks" :key="'x' + c" :x1="x(c)" :x2="x(c)" :y1="T" :y2="H - B" />
      </g>
      <g font-size="11" fill="#55665d" font-family="var(--mono)">
        <text v-for="v in yTicks" :key="'yt' + v" :x="L - 8" :y="y(v) + 4" text-anchor="end">{{ v }}%</text>
        <text v-for="c in xTicks.filter((_, i) => i % 2 === 0)" :key="'xt' + c" :x="x(c)" :y="H - B + 18" text-anchor="middle">{{ tick(c) }}</text>
        <text :x="(L + W - R) / 2" :y="H - 6" text-anchor="middle">cost per call, list price, uncached (log scale)</text>
        <text :x="14" :y="(T + H - B) / 2" text-anchor="middle" :transform="`rotate(-90 14 ${(T + H - B) / 2})`">accuracy</text>
      </g>
      <polyline v-for="m in MODEL_KEYS" :key="'l' + m" :points="line(m)" fill="none" :stroke="COLOR[m]" stroke-width="1.6" stroke-opacity=".7" />
      <g v-for="p in pts" :key="p.m + p.a" :fill="AGENTS.includes(p.a) ? '#fff' : COLOR[p.m]" :stroke="COLOR[p.m]" stroke-width="1.8">
        <title>{{ tip(p) }}</title>
        <circle v-if="p.a === 'csv'" :cx="x(p.cost)" :cy="y(p.acc)" r="4.5" />
        <rect v-else-if="p.a === 'markitdown'" :x="x(p.cost) - 4" :y="y(p.acc) - 4" width="8" height="8" />
        <polygon v-else-if="p.a === 'cellprose_v03'" :points="star(x(p.cost), y(p.acc), 8)" />
        <polygon v-else :points="tri(x(p.cost), y(p.acc), 5.5)" />
      </g>
    </svg>
    <p class="tiny muted">{{ CORPORA[corpus] }} set, {{ run.corpora[corpus].workbooks }} workbooks, {{ run.repeats }} repeats, run of {{ run.date }}. Up and to the left is better. The points are formats and arms, not effort levels: each model ran at one reasoning setting, so there is no effort curve. The line joins a model's one-call formats (CSV, MarkItDown, Cellprose in the prompt). Hover a point for its numbers; the table under "Every arm, mean per call" below lists every value for the model you pick there.</p>
  </div>
</template>

<style scoped>
.sc { padding: 14px 16px; display: grid; gap: 10px; }
.sc-svg { width: 100%; height: auto; display: block; }
.sc-legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13px; align-items: center; }
.sc-legend span { display: inline-flex; gap: 6px; align-items: center; }
.sc-legend i { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.sc-legend .sep { width: 1px; height: 14px; background: var(--grid); }
.tiny { font: 11px/1.5 var(--mono); }
</style>
