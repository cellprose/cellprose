<script setup>
// The hero's numbers, from the 11 Nov 2026 run (site/data/run.json), each with its comparison and sample next to it.
import { withBase } from 'vitepress';
import { run, cellproseAcc, baselineAcc, ratios, wins, range } from '../lib/run.js';

const rw = run.corpora.realworld, sb = run.corpora.spreadsheetbench;
const turns = range(rw.arms.filter((a) => a.arm === 'agent_xlsx').map((a) => a.turns));
const mid = ratios([rw.verdicts, sb.verdicts], 'markitdown');
</script>

<template>
  <div class="stats">
    <div class="stat">
      <b data-f='=ACCURACY("Cellprose", "real-world")'>{{ cellproseAcc('realworld') }}%</b>
      <span>right on formula-heavy questions in one call, against {{ baselineAcc('realworld', 'csv') }}% for CSV and {{ baselineAcc('realworld', 'markitdown') }}% for MarkItDown ({{ rw.workbooks }} real-world workbooks, four models)</span>
    </div>
    <div class="stat">
      <b data-f='=TURNS("Cellprose")'>1 turn</b>
      <span>where an agent with a shell needs {{ turns }} turns ({{ baselineAcc('realworld', 'agent_xlsx') }}% accuracy; Cellprose is within about 0.5 to 3.8 points of it per model, GPT-6 Luna 93.8% against 97.6%): no sandbox needed</span>
    </div>
    <div class="stat">
      <b data-f='=CostPerCorrect("Cellprose")/CostPerCorrect("MarkItDown")'>{{ range(mid.map((v) => v.ratio), 2) }}×</b>
      <span>MarkItDown's cost per correct answer, a win in {{ wins(mid) }} of {{ mid.length }} model-and-corpus pairs</span>
    </div>
  </div>
  <p class="small muted">
    Pre-registered run of {{ run.date }}: {{ rw.workbooks + sb.workbooks }} held-out workbooks, {{ run.repeats }} repeats, every token priced as uncached.
    Against agents that open the <code>.xlsx</code> themselves, cost is mostly no difference.
    <a :href="withBase('/benchmarks')">Full results and limitations</a>.
  </p>
</template>
