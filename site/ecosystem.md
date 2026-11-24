---
layout: page
title: Ecosystem
---

<div class="sm-page">
<LiveBlock win="Ecosystem">
  <div class="sec-head"><div class="eyebrow">Ecosystem</div><h1 style="font-size:clamp(32px,5vw,48px)">One format, many surfaces.</h1>
    <p class="lede">The Python package does the reading and writing; the other tools wrap it. A second writer in JavaScript, written from the spec alone, passes the same conformance kit.</p></div>
  <div class="eco">
    <div id="cli" class="card"><h3>CLI</h3><p class="muted">Encode, decode, validate and compare sizes, in batch or in CI.</p><pre>cellprose encode book.xlsx
cellprose decode book.sheet.md
cellprose check book.sheet.md
cellprose stats book.xlsx</pre></div>
    <div id="python" class="card"><h3>Python</h3><p class="muted">The core library, for pipelines.</p><pre>import cellprose
text = cellprose.dumps("book.xlsx")</pre></div>
    <div id="mcp" class="card"><h3>MCP server</h3><p class="muted">Agents list sheets, read workbooks as Cellprose, and write cells back to .xlsx.</p><pre>pip install "cellprose[mcp]"
claude mcp add cellprose -- cellprose-mcp</pre></div>
    <div id="llms" class="card"><h3>For agents: llms.txt</h3><p class="muted">An index of the format for agents, and the spec, skill and install steps in one file.</p><pre><a href="./llms.txt">/llms.txt</a>
<a href="./llms-full.txt">/llms-full.txt</a></pre></div>
    <div id="skill" class="card"><h3>Agent skill</h3><p class="muted">A short SKILL.md that teaches an agent the blocks, so it needs no spec lookup.</p><pre>skills/cellprose/SKILL.md</pre></div>
    <div id="git" class="card"><h3>Git</h3><p class="muted">Readable diffs for .xlsx files already in a repo, and a pre-commit hook that writes a .sheet.md twin.</p><pre>cellprose git-setup
cellprose pre-commit</pre></div>
    <div id="js" class="card"><h3>JavaScript writer</h3><p class="muted">An independent writer with no dependencies. It runs this site's playground.</p><pre>node js/bin/cellprose-encode.js book.xlsx</pre></div>
    <div id="viewer" class="card"><h3>GitHub viewer</h3><p class="muted">A browser extension for .sheet.md files on GitHub: sheet tabs, and click a cell to see its real formula and the cells it reads.</p><pre>viewer/extension</pre></div>
    <div id="kit" class="card"><h3>Conformance kit</h3><p class="muted">Language-neutral cases (JSON workbooks, expected .sheet.md, decoded cells) and a checker, for writers and readers in other languages.</p><pre>python conformance/check.py --encoder "your-encoder"</pre></div>
  </div>
</LiveBlock>
</div>
