<script setup>
// One recorded benchmark call per format, replayed at a fixed token rate. The counts and answers are the call's own
// (site/data/benchmarks.json, "replay"); the timing is not.
import { onBeforeUnmount, reactive, ref } from 'vue';
import { data, num, label } from '../lib/bench.js';
import { run } from '../lib/run.js';
const hc = (a) => run.corpora.realworld.by_task.find((t) => t.model === 'haiku55' && t.arm === a).hardcode.toFixed(1);

const R = data.replay;
const lanes = R.lanes.map((l) => ({ ...l, name: label(l.encoding), sm: l.encoding !== 'csv' }));
const maxIn = Math.max(...lanes.map((l) => l.tin)), maxOut = Math.max(...lanes.map((l) => l.tout));
const now = reactive(lanes.map(() => ({ tin: 0, tout: 0, done: false })));
const clock = ref('');
const missed = (l) => R.truth.filter((c) => !l.answer.includes(c)).map((c) => c.split('!')[1]);
const [a, b] = lanes;
const saved = a.tout - b.tout;
const finalLine = `Cellprose finished with ${num(saved)} fewer output tokens (${Math.round((b.tout / a.tout - 1) * 100)}% on this call).`;
let raf = 0;

function set(t) {
  lanes.forEach((l, i) => {
    const tin = Math.min(l.tin, (l.tin * t) / 500), tout = t <= 500 ? 0 : Math.min(l.tout, (t - 500) * 1.6);
    Object.assign(now[i], { tin, tout, done: tout >= l.tout });
  });
}
function finish() { set(1e9); clock.value = finalLine; }
finish();
function play() {
  cancelAnimationFrame(raf);
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { finish(); return; }
  const t0 = performance.now();
  const step = (n) => {
    set(n - t0);
    const [x, y] = now;
    clock.value = y.done && !x.done ? 'Cellprose is done. CSV is still reasoning…' : 'Replaying…';
    if (x.done && y.done) { finish(); return; }
    raf = requestAnimationFrame(step);
  };
  raf = requestAnimationFrame(step);
}
onBeforeUnmount(() => cancelAnimationFrame(raf));
</script>

<template>
  <div class="card q"><span class="small muted" style="display:block;font-family:var(--mono)">Workbook 11 · Haiku 5.5 · repeat 2 · one question of {{ a.questions_in_call }} in the call</span>{{ R.question }}</div>
  <div class="row" style="margin-block:12px"><button class="btn" @click="play">▶ Play replay</button><span class="muted small">{{ clock }}</span></div>
  <div class="replay">
    <div v-for="(l, i) in lanes" :key="l.encoding" class="card lane" :class="{ sm: l.sm }">
      <h3>{{ l.name }}</h3>
      <div class="meter"><div class="rowx"><span>Read</span><b>{{ num(Math.round(now[i].tin)) }}</b></div><div class="track"><i :style="{ width: (now[i].tin / maxIn) * 100 + '%' }"></i></div></div>
      <div class="meter"><div class="rowx"><span>Reasoning + answers</span><b>{{ num(Math.round(now[i].tout)) }}</b></div><div class="track out"><i :style="{ width: (now[i].tout / maxOut) * 100 + '%' }"></i></div></div>
      <div class="answer" :class="now[i].done ? (l.score === 1 ? 'ok' : 'bad') : ''">
        <template v-if="now[i].done">{{ JSON.stringify(l.answer) }}
          <span class="vd">{{ l.score === 1 ? 'Correct: both gaps in the fill ranges found.' : `Missed ${missed(l).join(', ')}, which holds the value its formula would give.` }}</span>
        </template>
        <template v-else-if="now[i].tout > 0">Reasoning…</template>
      </div>
    </div>
  </div>
  <p class="muted small" style="margin-top:10px">One recorded call, picked to show the kind of miss values-only formats make; it is not a typical call.
    Token counts are the whole call ({{ a.questions_in_call }} questions); the reasoning text was not saved. It was recorded on 21 Nov 2026, on the v0.3 text (Haiku 5.5, one call per format, not repeated). In the
    11 Nov 2026 run on 30 real-world workbooks, Haiku 5.5 scored {{ hc('csv') }}% on typed-in questions with CSV and {{ hc('cellprose_v03') }}% with Cellprose (<a href="./benchmarks#tasks">all models</a>).</p>
</template>
