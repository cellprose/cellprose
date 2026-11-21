// Cellprose Viewer: content script. Upgrades the tables GitHub renders from a `.sheet.md` or `.cellprose.md` file.
// The data model lives in cellprose-core.js; this file only touches the DOM.
(function (root) {
  'use strict';
  const C = root.CellproseCore;

  // Wire up one rendered markdown container. `text` is the file's source. Returns a teardown function.
  function enhance(article, text, doc) {
    doc = doc || article.ownerDocument;
    const wb = C.parse(text);
    if (!wb.sheets.length) return () => {};

    // Group article children by sheet: each `# Sheet: …` heading starts a section.
    const sections = [];
    let current = null;
    for (const node of Array.from(article.children)) {
      const h = node.matches('.markdown-heading') ? node.querySelector('h1') : node.matches('h1') ? node : null;
      if (h && /^Sheet:/.test(h.textContent.trim())) {
        const name = wb.sheets[sections.length] && wb.sheets[sections.length].name;
        current = { name: name || h.textContent.replace(/^Sheet:\s*/, '').trim(), nodes: [] };
        sections.push(current);
      } else if (h && /^Names$/.test(h.textContent.trim())) {
        current = null;
      }
      if (current) current.nodes.push(node);
    }

    const cleanups = [];
    const panel = doc.createElement('div');
    panel.className = 'smv-panel';
    panel.hidden = true;
    doc.body.appendChild(panel);
    cleanups.push(() => panel.remove());

    let anchor = null;     // {td, sheet, col, row}
    let rangeEnd = null;
    const tdInfo = new Map();

    function activeSheetName() { return (sections.find(s => !s.nodes[0].classList.contains('smv-hidden')) || sections[0]).name; }

    function clearMarks() {
      article.querySelectorAll('.smv-sel,.smv-in-range,.smv-input').forEach(td => td.classList.remove('smv-sel', 'smv-in-range', 'smv-input'));
    }

    // Index every data cell: address from its row-number cell and the column letter in the header.
    for (const sec of sections) {
      for (const node of sec.nodes) {
        for (const table of node.matches('table') ? [node] : Array.from(node.querySelectorAll('table'))) {
          const cols = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
          for (const tr of table.querySelectorAll('tbody tr')) {
            const tds = Array.from(tr.children);
            const row = parseInt(tds[0].textContent, 10);
            if (!(row > 0)) continue;
            tds.forEach((td, k) => {
              if (k === 0 || !/^[A-Z]+$/.test(cols[k] || '')) return;
              td.classList.add('smv-cell');
              tdInfo.set(td, { sheet: sec.name, col: C.colToNum(cols[k]), row });
              const a = C.addr(C.colToNum(cols[k]), row);
              td.dataset.smvAddr = a;
              const info = C.cellInfo(wb, sec.name, a);
              if (info && info.formula) td.classList.add('smv-formula');
            });
          }
        }
      }
    }

    function tdsOf(sheet, g) {
      const out = [];
      for (const [td, p] of tdInfo) if (p.sheet === sheet && C.inRange(g, p.col, p.row)) out.push(td);
      return out;
    }

    function esc(s) { const d = doc.createElement('div'); d.textContent = s; return d.innerHTML; }

    function select(td, extend) {
      const p = tdInfo.get(td);
      clearMarks();
      if (!extend || !anchor || anchor.sheet !== p.sheet) { anchor = { td, ...p }; rangeEnd = null; }
      else rangeEnd = p;
      const g = rangeEnd
        ? { c1: Math.min(anchor.col, rangeEnd.col), r1: Math.min(anchor.row, rangeEnd.row), c2: Math.max(anchor.col, rangeEnd.col), r2: Math.max(anchor.row, rangeEnd.row) }
        : { c1: anchor.col, r1: anchor.row, c2: anchor.col, r2: anchor.row };
      tdsOf(p.sheet, g).forEach(t => t.classList.add('smv-in-range'));
      anchor.td.classList.add('smv-sel');
      const a = C.addr(anchor.col, anchor.row);
      const info = C.cellInfo(wb, p.sheet, a);
      const rangeText = C.rangeStr(g);
      const multi = rangeText !== a;

      let html = `<div><span class="smv-addr">${esc(p.sheet)}!${esc(multi ? rangeText : a)}</span>`;
      if (info) html += `<span class="smv-muted">${esc(info.type)}</span>`;
      html += `<button type="button" data-smv="copy">Copy ${multi ? 'range' : 'cell'} as grid</button></div>`;
      if (info && !multi) {
        html += `<div class="smv-row">Value <code>${esc(info.text === '' ? '(empty)' : info.text)}</code>`;
        if (info.format) html += ` <span class="smv-muted">format</span> <code>${esc(info.format)}</code>`;
        html += '</div>';
        if (info.formula) {
          html += `<div class="smv-row">Formula <code>${esc(info.formula)}</code></div>`;
          const refs = info.precedents.map(r => `<a class="smv-ref" data-sheet="${esc(r.sheet)}" data-range="${C.rangeStr(r.range)}">${r.sheet === p.sheet ? '' : esc(r.sheet) + '!'}${C.rangeStr(r.range)}</a>`);
          if (refs.length) html += `<div class="smv-row"><span class="smv-muted">Reads</span> ${refs.join('')}</div>`;
        } else if (info.type !== 'empty') {
          html += '<div class="smv-row smv-muted">Typed value, no formula.</div>';
        }
        if (info.formula) for (const r of info.precedents) tdsOf(r.sheet, r.range).forEach(t => t.classList.add('smv-input'));
      }
      panel.innerHTML = html;
      panel.hidden = false;
      panel.dataset.range = rangeText;
      panel.dataset.sheet = p.sheet;
    }

    function showSheet(name) {
      for (const sec of sections) sec.nodes.forEach(n => n.classList.toggle('smv-hidden', sec.name !== name));
      tabs.querySelectorAll('.smv-tab').forEach(b => b.setAttribute('aria-selected', String(b.dataset.sheet === name)));
      clearMarks();
      panel.hidden = true;
    }

    // Sheet tabs.
    const tabs = doc.createElement('div');
    tabs.className = 'smv-tabs';
    tabs.setAttribute('role', 'tablist');
    for (const sec of sections) {
      const b = doc.createElement('button');
      b.type = 'button'; b.className = 'smv-tab'; b.textContent = sec.name; b.dataset.sheet = sec.name;
      b.setAttribute('role', 'tab');
      tabs.appendChild(b);
    }
    sections[0].nodes[0].before(tabs);
    cleanups.push(() => { tabs.remove(); sections.forEach(s => s.nodes.forEach(n => n.classList.remove('smv-hidden'))); });
    showSheet(sections[0].name);

    const onClick = (e) => {
      const tab = e.target.closest && e.target.closest('.smv-tab');
      if (tab && tabs.contains(tab)) { showSheet(tab.dataset.sheet); return; }
      const td = e.target.closest && e.target.closest('td.smv-cell');
      if (td && article.contains(td)) { select(td, e.shiftKey); return; }
    };
    const onPanelClick = (e) => {
      const copy = e.target.closest('[data-smv="copy"]');
      if (copy) {
        const tsv = C.rangeToTSV(wb, panel.dataset.sheet, panel.dataset.range);
        const done = () => { copy.textContent = 'Copied'; };
        if (root.navigator && root.navigator.clipboard) root.navigator.clipboard.writeText(tsv).then(done, () => {});
        panel.dataset.copied = tsv;
        return;
      }
      const ref = e.target.closest('a.smv-ref');
      if (ref) {
        if (ref.dataset.sheet !== activeSheetName()) showSheet(ref.dataset.sheet);
        const g = C.parseRange(ref.dataset.range);
        tdsOf(ref.dataset.sheet, g).forEach(t => t.classList.add('smv-input'));
        const first = tdsOf(ref.dataset.sheet, g)[0];
        if (first && first.scrollIntoView) first.scrollIntoView({ block: 'center' });
      }
    };
    const onKey = (e) => { if (e.key === 'Escape') { clearMarks(); panel.hidden = true; } };
    article.addEventListener('click', onClick);
    tabs.addEventListener('click', onClick);
    panel.addEventListener('click', onPanelClick);
    doc.addEventListener('keydown', onKey);
    cleanups.push(() => { article.removeEventListener('click', onClick); doc.removeEventListener('keydown', onKey); });
    return () => cleanups.forEach(f => f());
  }

  // ------------------------------------------------------------ GitHub bootstrap
  let teardown = null, lastKey = null;

  async function run() {
    const m = /^\/([^/]+)\/([^/]+)\/blob\/(.+\.(?:sheet|cellprose)\.md)$/.exec(location.pathname);
    if (!m) { if (teardown) { teardown(); teardown = null; lastKey = null; } return; }
    const article = document.querySelector('article.markdown-body');
    if (!article || article.dataset.smv) return;
    if (lastKey === location.pathname && teardown) return;
    article.dataset.smv = '1';
    try {
      const res = await fetch(location.pathname.replace('/blob/', '/raw/'), { credentials: 'same-origin' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const text = await res.text();
      if (teardown) teardown();
      teardown = enhance(article, text, document);
      lastKey = location.pathname;
    } catch (err) {
      delete article.dataset.smv;
      console.warn('[cellprose-viewer]', err);
    }
  }

  root.CellproseViewer = { enhance };
  if (root.location && /(^|\.)github\.com$/.test(root.location.hostname)) {
    run();
    document.addEventListener('turbo:render', run);
    document.addEventListener('pjax:end', run);
    new MutationObserver(() => run()).observe(document.body, { childList: true, subtree: true });
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
