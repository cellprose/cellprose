<script setup>
// Accuracy on the real-world set of the 11 Nov 2026 run, one bar per arm, with turns per call and cost per correct
// answer beside it. The reader picks the model; bars grow in when the chart scrolls into view.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { withBase } from 'vitepress';
import { run, MODEL_KEYS, modelName, armName, arm, money } from '../lib/run.js';

const ARMS = ['csv', 'markitdown', 'cellprose_v03', 'agent_xlsx', 'agent_xlsx_viewer'];
const model = ref('sonnet55');
const list = computed(() => ARMS.map((a) => arm('realworld', model.value, a)));
const root = ref(null), shown = ref(false);
let io = null;
onMounted(() => {
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) { shown.value = true; return; }
  io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { shown.value = true; io.disconnect(); } }, { threshold: 0.3 });
  io.observe(root.value);
});
onBeforeUnmount(() => io?.disconnect());
</script>

<template>
  <div class="row" style="margin-bottom:12px">
    <div class="seg" data-tool="Model"><button v-for="m in MODEL_KEYS" :key="m" :aria-pressed="model === m" @click="model = m">{{ modelName(m) }}</button></div>
  </div>
  <div ref="root" class="card chart">
    <div v-for="r in list" :key="r.arm" class="crow" :class="{ sm: r.arm === 'cellprose_v03' }">
      <span class="lab">{{ armName(r.arm) }}<span class="tiny">{{ r.turns.toFixed(1) }} turn{{ r.turns === 1 ? '' : 's' }} · {{ money(r.cost_per_correct) }} per correct</span></span>
      <div class="bars grow" :title="`${armName(r.arm)}: ${r.acc}% correct`">
        <span class="out" :style="{ width: shown ? r.acc + '%' : '0' }"></span>
      </div>
      <span class="delta" :class="r.arm === 'cellprose_v03' ? 'good' : 'base'">{{ r.acc.toFixed(1) }}%<span class="tiny">correct</span></span>
    </div>
    <div class="tiny muted">{{ run.corpora.realworld.workbooks }} real-world workbooks, {{ run.corpora.realworld.questions }} questions, {{ run.repeats }} repeats, run of {{ run.date }} · cost at list price, every token uncached ·
      <a :href="withBase('/benchmarks')">verdicts, intervals and limitations</a></div>
  </div>
</template>
