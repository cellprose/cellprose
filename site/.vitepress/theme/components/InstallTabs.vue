<script setup>
// One-click install snippets. The lines mirror INTEGRATIONS.md; `copy` is what the button puts on the clipboard.
import { ref } from 'vue';

const MCP_JSON = `{
  "mcpServers": {
    "cellprose": {
      "command": "cellprose-mcp",
      "env": { "CELLPROSE_ROOT": "/Users/you/work" }
    }
  }
}`;
const TABS = [
  ['CLI', [['# convert, then compare sizes', 1], ['cellprose encode model.xlsx'], ['cellprose stats model.xlsx']]],
  ['Python', [['# from PyPI', 1], ['pip install cellprose'], ['python -c "import cellprose; print(cellprose.dumps(\'model.xlsx\'))"']]],
  ['MCP: Claude Code', [['# optional CELLPROSE_ROOT keeps the server inside one folder', 1], ['pip install "cellprose[mcp]"'], ['claude mcp add cellprose -e CELLPROSE_ROOT="$HOME/work" -- cellprose-mcp']]],
  ['MCP: Desktop, Cursor', [['# add to the client\'s MCP JSON config', 1], ...MCP_JSON.split('\n').map((l) => [l])]],
  ['Agent skill', [['# Claude Code: for every project (use .claude/skills/ for one)', 1], ['cp -r skills/cellprose ~/.claude/skills/'], ['# needs only openpyxl; it triggers on spreadsheet tasks', 1]]],
  ['JavaScript', [['# the second, independent writer; no dependencies', 1], ['node js/bin/cellprose-encode.js model.xlsx > model.sheet.md']]],
];
const cur = ref(0), copied = ref(false);
const text = (i) => TABS[i][1].filter((l) => !l[1]).map((l) => l[0]).join('\n');
async function copy() {
  try { await navigator.clipboard.writeText(text(cur.value)); copied.value = true; setTimeout(() => (copied.value = false), 1500); } catch { /* clipboard blocked: the text is selectable */ }
}
</script>

<template>
  <div class="tabs" role="tablist" data-tool="Where">
    <button v-for="(t, i) in TABS" :key="t[0]" role="tab" :aria-selected="cur === i" @click="cur = i; copied = false">{{ t[0] }}</button>
  </div>
  <div class="termwrap" style="margin-top:12px">
    <pre class="term"><template v-for="(l, j) in TABS[cur][1]" :key="j"><span :class="{ cm: l[1] }">{{ l[0] }}</span>{{ '\n' }}</template></pre>
    <button class="btn ghost copy" @click="copy">{{ copied ? 'Copied' : 'Copy' }}</button>
  </div>
  <p class="small muted" style="margin-top:10px">Working with an agent? <a href="./llms.txt">/llms.txt</a> indexes the format for it, and <a href="./llms-full.txt">/llms-full.txt</a> is the spec, the skill and these steps in one file.</p>
</template>
