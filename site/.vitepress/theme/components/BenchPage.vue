<script setup>
// The pre-registered benchmark run of 11 Nov 2026 and Addendum A, straight from site/data/run.json
// (benchmarks/site_run.py). Verdicts, every arm, accuracy by question type, the guess control and the limits.
import { computed, ref } from 'vue';
import LiveBlock from './LiveBlock.vue';
import { run, MODEL_KEYS, modelName, armName, arm, verdictsFor, cellproseAcc, baselineAcc, ratios, wins, money, num, range } from '../lib/run.js';

const model = ref('sonnet55');
const corpusKey = ref('realworld');
const view = ref('realworld_primary');
const C = computed(() => run.corpora[corpusKey.value]);
const verdicts = computed(() => verdictsFor(C.value.verdicts, model.value));
const arms = computed(() => run.arms.map((a) => arm(corpusKey.value, model.value, a)).filter(Boolean));
const tasks = computed(() => run.arms.map((a) => C.value.by_task.find((t) => t.model === model.value && t.arm === a)).filter(Boolean));
const hasTasks = computed(() => tasks.value.some((t) => t.trace != null));
const addV = computed(() => verdictsFor(run.addendum.views[view.value].verdicts, model.value));
const TASKS = [['lookup', 'Lookup'], ['address', 'Cell address'], ['trace', 'Formula trace'], ['impact', 'Impact'], ['hardcode', 'Typed-in vs formula']];
const heat = (v) => (v == null ? '' : `background:color-mix(in srgb,var(--ok) ${Math.max(0, v - 50) * 1.8}%,var(--sheet))`);
const vclass = (v) => (v === 'win' ? 'good' : v === 'loss' ? 'bad' : 'base');
const BASE = { markitdown: 'MarkItDown', csv: 'CSV', agent_xlsx: 'Agent + shell', agent_xlsx_viewer: 'Agent + viewer' };

const rw = run.corpora.realworld, sb = run.corpora.spreadsheetbench;
const mid = ratios([rw.verdicts, sb.verdicts], 'markitdown');
const all = [rw.verdicts, sb.verdicts].flat();
const lean = Object.values(run.addendum.views).flatMap((v) => v.verdicts);
</script>

<template>
  <LiveBlock id="results" win="Benchmark Results.xls">
    <div class="sec-head"><div class="eyebrow">Benchmarks · run of {{ run.date }}</div>
      <h1 style="font-size:clamp(32px,5vw,48px)">More right answers, in one call.</h1>
      <p class="lede">A pre-registered run on {{ rw.workbooks + sb.workbooks }} held-out workbooks and four models. The protocol, code and data were frozen and their digest posted before the first call.</p></div>
    <div class="stats">
      <div class="stat"><b>{{ cellproseAcc('realworld') }}%</b>
        <span>accuracy with Cellprose in one call on the {{ rw.workbooks }} real-world workbooks, against {{ baselineAcc('realworld', 'csv') }}% for CSV and {{ baselineAcc('realworld', 'markitdown') }}% for MarkItDown</span></div>
      <div class="stat"><b>{{ range(rw.arms.filter((a) => a.arm === 'agent_xlsx').map((a) => a.turns)) }}</b>
        <span>turns an agent with a shell needs on the same workbooks ({{ baselineAcc('realworld', 'agent_xlsx') }}% accuracy). Cellprose in the prompt answers in one call, within about 0.5 to 3.8 points of it per model (GPT-6 Luna 93.8% against 97.6%)</span></div>
      <div class="stat"><b>{{ range(mid.map((v) => v.ratio), 2) }}×</b>
        <span>MarkItDown's cost per correct answer; a win in {{ wins(mid) }} of {{ mid.length }} model-and-corpus pairs</span></div>
    </div>
    <p class="muted small">{{ all.length }} pre-registered comparisons: {{ wins(all) }} wins, {{ all.filter((v) => v.verdict === 'loss').length }} losses, the rest no difference. Against agents that open the <code>.xlsx</code> with a shell, cost is mostly no difference. Every number has its limits <a href="#limits">below</a>.</p>
  </LiveBlock>

  <LiveBlock id="scorecost" win="Score vs cost.xls">
    <div class="sec-head"><div class="eyebrow">Accuracy and cost</div><h2>Every model, every way of giving it the workbook.</h2>
      <p class="lede">Accuracy against cost per call for the four models, from the same run. Cellprose in the prompt sits higher than CSV and MarkItDown for most models, and for some it costs less.</p></div>
    <ScoreCost />
  </LiveBlock>

  <LiveBlock id="verdicts" win="Verdicts">
    <div class="sec-head"><div class="eyebrow">Verdicts</div><h2>Cost per correct answer, against each alternative.</h2>
      <p class="lede">Ratio of Cellprose's cost per correct answer to the baseline's, with its 95% paired-bootstrap interval over workbooks. A win needs the whole interval below 1 and no more than one point of accuracy lost; a loss needs it wholly above 1.</p></div>
    <div class="row" style="margin-bottom:12px">
      <div class="seg" data-tool="Model"><button v-for="m in MODEL_KEYS" :key="m" :aria-pressed="model === m" @click="model = m">{{ modelName(m) }}</button></div>
      <div class="seg" data-tool="Workbooks"><button v-for="(c, k) in run.corpora" :key="k" :aria-pressed="corpusKey === k" @click="corpusKey = k">{{ c.label }} ({{ c.workbooks }})</button></div>
    </div>
    <p class="muted small">{{ C.label }}: {{ C.workbooks }} workbooks, {{ C.questions }} questions, {{ C.about }}. {{ run.repeats }} repeats.</p>
    <div class="tw"><table class="ref"><tbody>
      <tr><th>Against</th><th>Accuracy (Cellprose / baseline)</th><th>Cost ratio</th><th>95% interval</th><th>Verdict</th></tr>
      <tr v-for="v in verdicts" :key="v.baseline">
        <td>{{ BASE[v.baseline] }}</td>
        <td class="num">{{ v.acc.toFixed(1) }}% / {{ v.acc_baseline.toFixed(1) }}%</td>
        <td class="num">{{ v.ratio.toFixed(2) }}</td>
        <td class="num">{{ v.lo.toFixed(2) }} to {{ v.hi.toFixed(2) }}</td>
        <td><span class="verdict" :class="vclass(v.verdict)">{{ v.verdict }}</span></td>
      </tr>
    </tbody></table></div>

    <h3 style="margin:22px 0 10px">Every arm, mean per call</h3>
    <div class="tw"><table class="ref"><tbody>
      <tr><th>Arm</th><th>Accuracy</th><th>Tokens per call</th><th>Cost per call</th><th>Cost per correct</th><th>Turns</th></tr>
      <tr v-for="a in arms" :key="a.arm">
        <td>{{ armName(a.arm) }}</td>
        <td class="num">{{ a.acc.toFixed(1) }}%</td>
        <td class="num">{{ num(a.tokens) }}</td>
        <td class="num">{{ money(a.cost) }}</td>
        <td class="num">{{ money(a.cost_per_correct) }}</td>
        <td class="num">{{ a.turns.toFixed(1) }}</td>
      </tr>
      <tr><td>{{ armName('none') }}</td><td class="num">{{ C.none[model].toFixed(1) }}%</td><td colspan="4" class="muted small">the control: what a model gets right with no workbook at all</td></tr>
    </tbody></table></div>
    <p class="muted small">Question-averaged accuracy here; the verdicts above average by workbook, so the two can differ by a tenth of a point. Prices are list prices with every token uncached.</p>
  </LiveBlock>

  <LiveBlock id="tasks" win="Accuracy by question type">
    <div class="sec-head"><div class="eyebrow">Accuracy by question type</div><h2>Where formulas decide the answer.</h2>
      <p class="lede">CSV and MarkItDown carry values only. The gap opens on the questions that need a formula: what a cell is computed from, what a change would move, and which numbers were typed in where a formula belongs.</p></div>
    <div v-if="hasTasks" class="tw card"><table class="ref heat"><tbody>
      <tr><th>{{ modelName(model) }}, {{ C.label }}</th><th v-for="t in TASKS" :key="t[0]">{{ t[1] }}</th></tr>
      <tr v-for="r in tasks" :key="r.arm"><td>{{ armName(r.arm) }}</td>
        <td v-for="t in TASKS" :key="t[0]" class="h" :style="heat(r[t[0]])">{{ r[t[0]] == null ? '—' : r[t[0]].toFixed(1) + '%' }}</td></tr>
    </tbody></table></div>
    <p v-else class="muted">SpreadsheetBench questions are all value lookups, so there is no breakdown. Switch to the real-world set above.</p>
  </LiveBlock>

  <LiveBlock id="addendum" win="Addendum A">
    <div class="sec-head"><div class="eyebrow">Addendum A</div><h2>Cellprose with its own tools.</h2>
      <p class="lede">An agent given the workbook's index and Cellprose's read, find, trace and what-if tools, with no shell, against the same two shell agents. Frozen and posted separately; {{ run.addendum.repeats }} repeats. <b>The decision to run it was made after the main results were seen</b>, so read it as a second result, not part of the first.</p></div>
    <div class="row" style="margin-bottom:12px">
      <div class="seg" data-tool="Model"><button v-for="m in MODEL_KEYS" :key="m" :aria-pressed="model === m" @click="model = m">{{ modelName(m) }}</button></div>
      <div class="seg" data-tool="View"><button v-for="(v, k) in run.addendum.views" :key="k" :aria-pressed="view === k" @click="view = k">{{ v.label }}</button></div>
    </div>
    <div class="tw"><table class="ref"><tbody>
      <tr><th>Against</th><th>Accuracy (own tools / baseline)</th><th>Cost ratio</th><th>95% interval</th><th>Verdict</th></tr>
      <tr v-for="v in addV" :key="v.baseline">
        <td>{{ BASE[v.baseline] }}</td>
        <td class="num">{{ v.acc.toFixed(1) }}% / {{ v.acc_baseline.toFixed(1) }}%</td>
        <td class="num">{{ v.ratio.toFixed(2) }}</td>
        <td class="num">{{ v.lo.toFixed(2) }} to {{ v.hi.toFixed(2) }}</td>
        <td><span class="verdict" :class="vclass(v.verdict)">{{ v.verdict }}</span></td>
      </tr>
    </tbody></table></div>
    <p class="muted small">Across three overlapping views (the real-world comparisons appear in two of them, so these are not {{ lean.length }} independent tests): {{ wins(lean) }} wins of {{ lean.length }}, no losses, cost ratios {{ range(lean.map((v) => v.ratio), 2) }}. The remaining "no difference" verdicts come from accuracy, mostly address questions on Haiku 5.5 and GPT-6 Luna. Impact questions are left out of the primary view because the what-if tool shares its method with the ground truth for them.</p>
  </LiveBlock>

  <LiveBlock id="limits" win="README.TXT">
    <div class="sec-head"><div class="eyebrow">Method and limitations</div><h2>Read before quoting a number.</h2></div>
    <ul class="limits">
      <li>{{ rw.workbooks }} real-world workbooks ({{ rw.questions }} questions) and {{ sb.workbooks }} SpreadsheetBench workbooks ({{ sb.questions }} questions), reported separately and never pooled. With this few workbooks the intervals are wide, Haiku's widest.</li>
      <li>The questions are generated by rule from the workbooks, not written by their authors. SpreadsheetBench tasks are restated as value questions, where CSV already scores well and Cellprose has less to add.</li>
      <li>Four models on one date: {{ MODEL_KEYS.map(modelName).join(', ') }}. Nothing is claimed for a model that was not run.</li>
      <li>Every token is priced as uncached input or output at list price. The billed amount, with caching, was lower; see the full results.</li>
      <li>Cellprose sends more tokens than CSV (1.31× on Claude, 1.60× on GPT). It wins on cost per correct answer only where it is right more often.</li>
      <li>A one-shot call and an agent loop spend tokens differently. A win over an agent is on cost per correct answer, which is what a user pays, and says nothing about which reads a workbook better at equal cost.</li>
      <li>The benchmark workbooks average about 20,000–25,000 tokens. Very large models do not fit one call; for those the index-then-tools route is the one to use, and it has not been measured on large files.</li>
      <li>Full tables, failures, resumes and spend: <a href="https://github.com/cellprose/cellprose/blob/main/benchmarks/RESULTS.md">RESULTS.md</a>. How runs are done and scored: <a href="./reference/protocol">the benchmark protocol</a>. Every number on this page is generated from the result files by <code>benchmarks/site_run.py</code>, and a test checks it against RESULTS.md.</li>
    </ul>
  </LiveBlock>
</template>
