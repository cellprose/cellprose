// The sheet viewer: a grid on the left, the .sheet.md (or CSV, or the GitHub rendering) on the right. Everything it
// shows comes from parsing the Cellprose text with the viewer's parser; it holds no workbook model of its own.
import { core, cellsOf, bounds, overrides, gfm, esc } from './sheet.js';

const MODES = [['values', 'Values'], ['formulas', 'Formulas'], ['map', 'Formula map'], ['bands', 'Fill-range bands'], ['trace', 'Trace']];
const fmtNum = (x) => (x.type === 'number' ? Number(x.value).toLocaleString('en-US', { maximumFractionDigits: 6 }) : x.text);

function cellsIn(g) {
  const out = [];
  for (let r = g.r1; r <= g.r2; r++) for (let c = g.c1; c <= g.c2; c++) out.push(core.addr(c, r));
  return out;
}

export function makeViewer(host, opts = {}) {
  const three = !!opts.three;
  let wb = null, text = '', csv = '', file = '', sheetIdx = 0, mode = opts.mode || 'bands', right = 'md', drawn = false;
  let cells = {}, fills = [], ov = new Set();
  const gridCard = `<div class="card pane"><div class="pane-bar"><span class="fname"></span><span class="sp vinfo"></span></div><div class="gridwrap"><table class="xl"></table><svg class="arrows"></svg></div><div class="sheettabs"></div><div class="fbar"><span class="addr">A1</span><span class="ftext muted">Hover a cell</span></div><div class="vlegend"></div></div>`;
  const body = (kind) => `<div class="rbody" data-kind="${kind}" style="display:flex;flex-direction:column;flex:1;min-height:0;position:relative"></div>`;
  const modes = `<div class="row" style="margin-bottom:10px"><div class="seg vmodes" data-tool="Show cells as">${MODES.map(([k, n]) => `<button data-v="${k}" aria-pressed="false">${n}</button>`).join('')}</div>${three ? '<span class="small muted">Hover a cell, a source line or a table row: the same place lights up in all three panes.</span>' : ''}</div>`;
  const html = three
    ? `${modes}<div class="viewer three">${gridCard}<div class="card pane"><div class="pane-bar"><span>.sheet.md source</span><span class="sp rinfo"></span></div>${body('md')}</div><div class="card pane"><div class="pane-bar"><span>On GitHub</span><span class="sp rinfo"></span></div>${body('gh')}</div></div>`
    : `${modes}<div class="viewer">${gridCard}<div class="card pane"><div class="pane-bar">${opts.tabs ? `<div class="seg rtabs" data-tool="Right pane"><button data-r="md" aria-pressed="true">.sheet.md</button><button data-r="csv" aria-pressed="false">CSV</button><button data-r="gh" aria-pressed="false">On GitHub</button></div>` : '<span>.sheet.md</span>'}<span class="sp rinfo"></span></div>${body('md')}</div></div>`;
  host.innerHTML = `<div>${html}</div>`;
  const root = host.firstElementChild;   // listeners go here, not on `host`, which a page may rebuild
  const q = (s) => host.querySelector(s);
  const tbl = q('table.xl'), svg = q('svg.arrows'), rt = q('.rtabs');
  const bodies = [...host.querySelectorAll('.rbody')];
  q('.vmodes').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { mode = b.dataset.v; draw(); } });
  if (rt) rt.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { right = b.dataset.r; drawn = false; drawRight(); } });
  q('.sheettabs').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { sheetIdx = +b.dataset.i; draw(); } });
  const sheet = () => wb.sheets[sheetIdx];
  const td = (a) => tbl.querySelector(`td[data-a="${a}"]`);

  function draw() {
    host.querySelectorAll('.vmodes button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.v === mode));
    const sh = sheet();
    cells = cellsOf(wb, sh);
    fills = sh.regions.flatMap((r) => r.formulas);
    const bandOf = {};
    fills.forEach((f, i) => cellsIn(f.range).forEach((a) => (bandOf[a] = i)));
    ov = overrides(wb, sh, cells);
    const b = bounds(cells), maxR = Math.min(b.r1, 300);
    let h = '<tr><th></th>';
    for (let c = 1; c <= b.c1; c++) h += `<th>${core.numToCol(c)}</th>`;
    h += '</tr>';
    for (let r = 1; r <= maxR; r++) {
      h += `<tr><th>${r}</th>`;
      for (let c = 1; c <= b.c1; c++) {
        const a = core.addr(c, r), x = cells[a];
        if (!x || (x.type === 'empty' && !x.formula)) { h += `<td data-a="${a}"></td>`; continue; }
        const cls = [];
        let txt = esc(fmtNum(x));
        if (x.type !== 'number' && !x.formula) cls.push('t');
        else if (!x.formula) cls.push('v');
        if (mode === 'formulas' && x.formula) { cls.push('fx'); txt = esc(x.formula); }
        if (mode === 'map') cls.push(ov.has(a) ? 'k-ov' : x.formula ? 'k-f' : x.type === 'number' ? 'k-in' : 'k-t');
        if (mode === 'bands') { if (bandOf[a] !== undefined) cls.push('bd' + (bandOf[a] % 5)); else if (ov.has(a)) cls.push('k-ov'); }
        h += `<td class="${cls.join(' ')}" data-a="${a}" title="${a}">${txt}</td>`;
      }
      h += '</tr>';
    }
    tbl.innerHTML = h;
    tbl.className = 'xl m-' + mode;
    svg.innerHTML = '';
    q('.fname').textContent = file || 'workbook.xlsx';
    q('.vinfo').textContent = { values: 'what Excel shows', formulas: 'every formula', map: 'cell kinds', bands: `${fills.length} fill ranges · ${ov.size} gap${ov.size === 1 ? '' : 's'}`, trace: 'hover a formula cell' }[mode];
    q('.sheettabs').innerHTML = wb.sheets.map((s, i) => `<button data-i="${i}" aria-pressed="${i === sheetIdx}">${esc(s.name)}</button>`).join('');
    q('.vlegend').innerHTML = mode === 'map'
      ? '<div class="legend"><span><i style="background:var(--lab-bg)"></i>Label</span><span><i style="background:var(--in-bg)"></i>Typed number</span><span><i style="background:var(--f-bg)"></i>Formula</span><span><i style="background:var(--mark)"></i>Typed where a formula belongs</span></div>'
      : mode === 'bands' ? '<div class="legend"><span><i style="background:var(--b1)"></i><i style="background:var(--b2)"></i><i style="background:var(--b3)"></i>One colour per fill range</span><span><i style="background:var(--mark)"></i>Gap: typed in</span></div>' : '';
    drawRight();
  }

  function mdHtml() {
    let cur = null, inF = false, fi = 0;
    return `<pre class="code">${text.replace(/\n$/, '').split('\n').map((l) => {
      const m = /^# Sheet: (.*)$/.exec(l);
      if (m) { cur = m[1].replace(/^"|"$/g, ''); fi = 0; return `<span class="ln"><span class="hd">${esc(l)}</span></span>`; }
      if (l.startsWith('#')) return `<span class="ln"><span class="hd">${esc(l)}</span></span>`;
      if (l.startsWith('```')) { inF = l.trim() === '```formulas'; return `<span class="ln"><span class="kw">${esc(l)}</span></span>`; }
      if (inF && l.includes(' = ')) return `<span class="ln fl" data-sh="${esc(cur)}" data-fi="${fi++}">${esc(l)}</span>`;
      const rm = /^\|?(\d+)\|/.exec(l);
      if (rm && cur) return `<span class="ln" data-sh="${esc(cur)}" data-row="${rm[1]}">${esc(l)}</span>`;
      if (l === '---' || /^(cellprose|source|note):/.test(l) || /^\|?[-|]+\|?$/.test(l) || l.startsWith('|#|') || l.startsWith('#|')) return `<span class="ln"><span class="dm">${esc(l)}</span></span>`;
      return `<span class="ln">${esc(l) || ' '}</span>`;
    }).join('')}</pre>`;
  }

  // The text panes. In three-pane mode they draw once per workbook, so hovering across sheets does not reset scrolling.
  function drawRight() {
    if (drawn && three) return;
    drawn = true;
    if (rt) rt.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.r === right));
    bodies.forEach((rbody) => {
      const kind = three ? rbody.dataset.kind : right;
      const ri = rbody.closest('.pane').querySelector('.rinfo');
      if (kind === 'md') { ri.textContent = text.length.toLocaleString() + ' chars'; rbody.innerHTML = mdHtml(); }
      else if (kind === 'csv') {
        ri.textContent = csv.length.toLocaleString() + ' chars';
        rbody.innerHTML = `<pre class="code">${csv.replace(/\n$/, '').split('\n').map((l) => `<span class="ln">${esc(l) || ' '}</span>`).join('')}</pre>`;
      } else { ri.textContent = 'rendered as GitHub shows it'; rbody.innerHTML = `<div class="gfm">${gfm(text, three)}</div>`; }
    });
  }

  function clearHi() {
    tbl.querySelectorAll('.hot,.prec').forEach((e) => e.classList.remove('hot', 'prec'));
    host.querySelectorAll('.rbody .hl').forEach((e) => e.classList.remove('hl'));
    svg.innerHTML = '';
  }
  function center(a) { const t = td(a); return t ? { x: t.offsetLeft + t.offsetWidth / 2, y: t.offsetTop + t.offsetHeight / 2, td: t } : null; }
  const linesFor = (sel) => bodies.flatMap((b) => [...b.querySelectorAll(`[data-sh="${CSS.escape(sheet().name)}"]${sel}`)]);
  // Mark source/table lines in every pane; with `scroll`, bring them into view inside their own pane (never the page).
  function light(els, scroll) {
    els.forEach((el) => {
      el.classList.add('hl');
      const b = el.closest('.rbody');
      if (!scroll || !b) return;
      const sc = b.querySelector('pre.code, .gfm') || b, r = el.getBoundingClientRect(), v = sc.getBoundingClientRect();
      if (r.top < v.top + 24 || r.bottom > v.bottom - 24) sc.scrollTop += r.top - v.top - sc.clientHeight / 2;
    });
  }

  function focus(a) {
    clearHi();
    const t = td(a);
    if (!t) return;
    t.classList.add('hot');
    const x = cells[a];
    q('.addr').textContent = a;
    q('.ftext').textContent = x
      ? x.formula ? x.formula : x.text + (x.type === 'number' ? (ov.has(a) ? '   · typed in, where a formula belongs' : '   · typed value') : '')
      : 'empty';
    const p = core.parseAddr(a);
    fills.forEach((f, i) => {
      if (!core.inRange(f.range, p.col, p.row)) return;
      cellsIn(f.range).forEach((c) => td(c)?.classList.add('prec'));
      light(linesFor(`[data-fi="${i}"]`), three);
    });
    light(linesFor(`[data-row="${p.row}"]`), three);
    if (mode === 'trace' && x && x.formula) {
      const to = center(a);
      svg.setAttribute('width', tbl.offsetWidth);
      svg.setAttribute('height', tbl.offsetHeight);
      let s = '';
      for (const ref of x.precedents) {
        if (ref.sheet !== sheet().name) continue;
        for (const pa of cellsIn(ref.range)) {
          const c = center(pa);
          if (!c) continue;
          c.td.classList.add('prec');
          s += `<line x1="${c.x}" y1="${c.y}" x2="${to.x}" y2="${to.y}"/><circle cx="${c.x}" cy="${c.y}" r="3.5"/>`;
        }
      }
      svg.innerHTML = s + `<circle cx="${to.x}" cy="${to.y}" r="5"/>`;
    }
  }
  tbl.addEventListener('mouseover', (e) => { const t = e.target.closest('td[data-a]'); if (t) focus(t.dataset.a); });
  tbl.addEventListener('click', (e) => { const t = e.target.closest('td[data-a]'); if (t) focus(t.dataset.a); });
  // Hovering a formulas line or a table row in either text pane lights the same place in the other panes and the grid.
  function hoverLine(ln) {
    if (ln.dataset.sh !== sheet().name) {
      if (!three) return;
      const i = wb.sheets.findIndex((x) => x.name === ln.dataset.sh);
      if (i < 0) return;
      sheetIdx = i; draw();
    }
    clearHi();
    if (ln.dataset.fi !== undefined) {
      const f = fills[+ln.dataset.fi];
      if (!f) return;
      light(linesFor(`[data-fi="${ln.dataset.fi}"]`), three);
      cellsIn(f.range).forEach((c) => td(c)?.classList.add('prec'));
      q('.addr').textContent = core.rangeStr(f.range);
      q('.ftext').textContent = '=' + f.formula + '   · filled across the range';
    } else {
      const r = +ln.dataset.row;
      light(linesFor(`[data-row="${r}"]`), false);
      for (const a of Object.keys(cells)) if (core.parseAddr(a).row === r) td(a)?.classList.add('prec');
      q('.addr').textContent = 'Row ' + r;
      q('.ftext').textContent = 'one line of the pipe table';
    }
  }
  root.addEventListener('mouseover', (e) => { const ln = e.target.closest('.rbody [data-fi], .rbody [data-row]'); if (ln) hoverLine(ln); });

  return {
    load(t, c, name) {
      text = t; csv = c; file = name; wb = core.parse(t); sheetIdx = 0; drawn = false;
      draw();
      if (opts.focus) focus(opts.focus);
    },
    setMode(m) { mode = m; draw(); },
  };
}
