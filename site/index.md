---
layout: page
title: Cellprose
titleTemplate: Spreadsheets models read right, in one call
---

<div class="sm-page wide">

<LiveBlock id="welcome" win="Cellprose — Welcome">
<div class="hero">
  <div class="eyebrow">Open format · .sheet.md</div>
  <h1>Spreadsheets that models <em>read right</em>, in one call.</h1>
  <p class="lede">Cellprose writes an Excel workbook as plain Markdown: values in a pipe table, formulas as fill ranges, one file per workbook. Models see the formulas, not just the values, so they answer trace and typed-in questions that CSV and MarkItDown get wrong. It renders as tables on GitHub.</p>
  <HomeStats />
  <div class="row"><a class="btn" href="./playground">Try the playground</a><a class="btn ghost" href="./guide/">Read the format</a></div>
</div>
</LiveBlock>

<LiveBlock id="viewer" win="Forecast.xls — Cellprose Viewer">
  <div class="sec-head"><div class="eyebrow">See it</div><h2>Every formula, in ten lines.</h2>
    <p class="lede">A 12-month forecast from the benchmark, converted in this page by the JS writer. Switch views, and hover a cell or a formula line. Coloured bands are fill ranges; the striped cells are typed-in numbers sitting where formulas belong.</p></div>
  <SheetViewer sample="11_forecast_overrides" name="forecast.xlsx" focus="H4" />
</LiveBlock>

<LiveBlock id="how" win="How it works">
  <div class="sec-head"><div class="eyebrow">How it works</div><h2>From a zip of XML to text a model can read.</h2></div>
  <HowItWorks />
</LiveBlock>

<LiveBlock id="game" win="Override Finder">
  <div class="sec-head"><div class="eyebrow">Try this</div><h2>Find the typed-in numbers.</h2>
    <p class="lede">Someone overwrote formula cells with typed numbers. This is what the values look like. Click the cells you suspect, then reveal what Cellprose shows.</p></div>
  <OverrideGame />
</LiveBlock>

<LiveBlock id="replay" win="Replay">
  <div class="sec-head"><div class="eyebrow">Replay</div><h2>Same question, two formats.</h2>
    <p class="lede">A recorded benchmark call, replayed at a fixed token rate. Haiku 5.5 read the forecast once as CSV and once as Cellprose.</p></div>
  <ReplayRace />
</LiveBlock>

<LiveBlock id="benchmark" win="Benchmark Results.xls">
  <div class="sec-head"><div class="eyebrow">Benchmark</div><h2>Close to agent accuracy, in one call.</h2>
    <p class="lede">Accuracy on 30 real-world workbooks, by how the model got the workbook. Cellprose in the prompt answers in one call; the shell agents take several turns and are somewhat more accurate on some models.</p></div>
  <RunChart />
</LiveBlock>

<LiveBlock id="git" win="Git Diff">
  <div class="sec-head"><div class="eyebrow">Works with Git</div><h2>Review a spreadsheet change like code.</h2>
    <p class="lede">Pick an edit to the forecast. Git can only say a binary file differs; the .sheet.md shows which lines changed.</p></div>
  <GitDiff />
</LiveBlock>

<LiveBlock id="install" win="Command Prompt">
  <div class="sec-head"><div class="eyebrow">Get started</div><h2>Use it where you work.</h2></div>
  <InstallTabs />
</LiveBlock>

<LiveBlock id="news" win="Launch news">
  <div class="sec-head"><div class="eyebrow">Launch news</div><h2>Hear when it ships.</h2></div>
  <NewsSignup source="home" />
</LiveBlock>

</div>
