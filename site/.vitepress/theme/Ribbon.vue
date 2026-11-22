<script setup>
// The site's nav, drawn as an Excel ribbon. Three kinds of command, each drawn differently:
//   big framed button  = opens (a page, or the file picker)
//   small "↓" button   = jumps to a section of the open page
//   green toggle       = switches what the page shows (in the yellow "Page tools" tab, like Excel's Table Tools)
// Toggles are mirrors of the page's own controls (any element with data-tool), so the ribbon never holds state of its own.
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useData, useRoute, useRouter, withBase } from 'vitepress';

const route = useRoute();
const router = useRouter();
const { page: pageData } = useData();
const REPO = 'https://github.com/cellprose/cellprose';

const PAGES = [
  { key: 'home', label: 'Home', link: '/', icon: 'home' },
  { key: 'playground', label: 'Playground', link: '/playground', icon: 'play' },
  { key: 'docs', label: 'Docs', link: '/guide/', icon: 'book' },
  { key: 'benchmarks', label: 'Benchmarks', link: '/benchmarks', icon: 'chart' },
  { key: 'ecosystem', label: 'Ecosystem', link: '/ecosystem', icon: 'plug' },
];
const DOCS = [
  ['Why Cellprose', '/guide/', 'book'], ['Format in ten minutes', '/guide/format', 'fx'], ['FAQ', '/guide/faq', 'help'],
  ['Specification', '/reference/spec', 'sheet'], ['Design decisions', '/reference/design', 'target'], ['Benchmark protocol', '/reference/protocol', 'kit'],
];
// Sections of the pages built from components; doc pages list their own headings instead.
const SECTIONS = {
  home: [['Welcome', 'welcome'], ['See it', 'viewer'], ['How it works', 'how'], ['Try this', 'game'], ['Replay', 'replay'], ['Benchmark', 'benchmark'], ['Works with Git', 'git'], ['Get started', 'install']],
  playground: [['Your workbook', 'workbook']],
  benchmarks: [['Results', 'results'], ['Accuracy by task', 'tasks'], ['Agent mode', 'agent'], ['Limitations', 'limits']],
  ecosystem: [['CLI', 'cli'], ['Python', 'python'], ['MCP server', 'mcp'], ['Agent skill', 'skill'], ['Git', 'git'], ['JavaScript writer', 'js'], ['GitHub viewer', 'viewer'], ['Conformance kit', 'kit']],
};
const GO = { home: ['playground', 'docs', 'benchmarks'], playground: ['docs', 'benchmarks'], docs: ['playground', 'benchmarks'], benchmarks: ['playground', 'docs'], ecosystem: ['playground', 'docs'] };
const SAMPLES = [['Forecast', '11_forecast_overrides.xlsx'], ['P&L', '03_pnl_quarterly.xlsx'], ['Loan schedule', '08_loan_schedule.xlsx'], ['Multi-sheet model', '05_multisheet_model.xlsx']];

const I = {
  home: '<path d="M5 15 16 6l11 9" fill="none" stroke="#55665d" stroke-width="1.6"/><path d="M8 13v13h16V13" fill="#fff" stroke="#55665d"/><rect x="13" y="18" width="6" height="8" fill="#107c41"/>',
  play: '<path d="M9 6h14l4 4v16H9z" fill="#fff" stroke="#55665d"/><path d="M14 13v8l7-4z" fill="#107c41"/>',
  open: '<path d="M4 9h9l2 2h13v15H4z" fill="#ffe9a6" stroke="#b08a1c"/><path d="M4 14h24" stroke="#b08a1c"/>',
  book: '<path d="M6 6h9a3 3 0 0 1 3 3v17a2.5 2.5 0 0 0-2.5-2.5H6z" fill="#fff" stroke="#55665d"/><path d="M26 6h-5a3 3 0 0 0-3 3v17a2.5 2.5 0 0 1 2.5-2.5H26z" fill="#dff3e7" stroke="#107c41"/>',
  fx: '<rect x="4" y="7" width="24" height="18" rx="2" fill="#fff" stroke="#55665d"/><text x="16" y="21" text-anchor="middle" font-family="Georgia,serif" font-style="italic" font-size="12" fill="#107c41">fx</text>',
  sheet: '<rect x="5" y="5" width="22" height="22" fill="#fff" stroke="#55665d"/><path d="M5 11h22M5 17h22M5 23h22M12 5v22M19 5v22" stroke="#9fb2a8"/><rect x="12" y="11" width="7" height="6" fill="#dff3e7" stroke="#107c41" stroke-width="1.6"/>',
  chart: '<path d="M5 27h22" stroke="#55665d"/><rect x="7" y="15" width="4" height="12" fill="#9fb2a8"/><rect x="14" y="10" width="4" height="17" fill="#c4441c"/><rect x="21" y="18" width="4" height="9" fill="#107c41"/>',
  target: '<circle cx="16" cy="16" r="10" fill="#fff" stroke="#55665d"/><circle cx="16" cy="16" r="5.5" fill="#dff3e7" stroke="#107c41"/><circle cx="16" cy="16" r="1.8" fill="#107c41"/>',
  kit: '<rect x="6" y="8" width="20" height="17" rx="2" fill="#fff" stroke="#55665d"/><path d="M12 8V6h8v2" stroke="#55665d" fill="none"/><path d="m11 16 3 3 7-7" stroke="#107c41" stroke-width="2" fill="none"/>',
  plug: '<path d="M12 5v6M20 5v6" stroke="#55665d" stroke-width="2"/><path d="M9 11h14v5a7 7 0 0 1-14 0z" fill="#dff3e7" stroke="#107c41"/><path d="M16 23v5" stroke="#55665d" stroke-width="2"/>',
  help: '<circle cx="16" cy="16" r="11" fill="#fff" stroke="#55665d"/><text x="16" y="21" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="14" fill="#107c41">?</text>',
};

const path = computed(() => route.path.replace(/\.html$/, ''));
const current = computed(() => {
  const p = path.value;
  if (/\/(guide|reference)\//.test(p)) return 'docs';
  for (const k of ['playground', 'benchmarks', 'ecosystem']) if (p.endsWith('/' + k)) return k;
  return 'home';
});
const tab = ref('home');
const collapsed = ref(true); // closed until the reader opens it; the choice is remembered
const backstage = ref(false);
const tools = ref([]);       // [{ group, items: [{ label, btns: [{ text, on, src }] }] }]
const headings = ref([]);    // [{ text, id }] of the open doc page
const here = ref('');        // id of the section in view
const root = ref(null);

const isHere = (link) => withBase(link).replace(/\/$/, '') === withBase(path.value).replace(/\/$/, '');
// The formula bar is shared with live.js, which writes the page's cells into it, so it is written directly too.
function hover(name, f) {
  const el = root.value;
  if (!el) return;
  el.querySelector('.lfbar .nb').textContent = name;
  const fmEl = el.querySelector('.lfbar .fm');
  fmEl.textContent = f.slice(1);
  const op = document.createElement('span'); op.className = 'op'; op.textContent = f[0];
  fmEl.prepend(op);
}

function headerOffset() { return root.value ? root.value.getBoundingClientRect().height + 24 : 0; }
function scrollToId(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const top = el.getBoundingClientRect().top + scrollY - headerOffset();
  scrollTo({ top, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  history.replaceState(history.state, '', '#' + id);
}
// Wait for something on a page we just opened (components mount after the route changes).
function when(find, run, tries = 40) { const el = find(); if (el) run(el); else if (tries > 0) setTimeout(() => when(find, run, tries - 1), 50); }
function open(link) { if (!isHere(link)) router.go(withBase(link)); }
function jump(pageKey, id) {
  const link = pageKey === 'docs' ? path.value : PAGES.find((p) => p.key === pageKey).link;
  if (isHere(link)) scrollToId(id);
  else { router.go(withBase(link)); when(() => document.getElementById(id), () => scrollToId(id)); }
}
function openFile() {
  const find = () => document.querySelector('.drop input[type=file]');
  if (find()) find().click();
  else { router.go(withBase('/playground')); when(find, (el) => el.click()); }
}
function openSample(name) {
  backstage.value = false;
  const find = () => [...document.querySelectorAll('[data-tool="Sample"] button')].find((b) => b.textContent.trim() === name);
  if (!find()) router.go(withBase('/playground'));
  when(find, (b) => b.click());
}
function search() {
  // VitePress's own full-text search; its Ctrl+K listener stays mounted although its nav button is hidden.
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, metaKey: true, bubbles: true }));
}
function choose(t) {
  if (t === 'tools') { tab.value = 'tools'; collapsed.value = false; return; }
  if (collapsed.value && tab.value === t) { collapsed.value = false; return; }
  tab.value = t; collapsed.value = false;
  open(PAGES.find((p) => p.key === t).link);
}
function toggle() { collapsed.value = !collapsed.value; }
function press(b) { b.src.click(); setTimeout(scan, 30); }

// Read the open page: its switches (data-tool) and, on doc pages, its headings.
function scan() {
  const groups = new Map();
  document.querySelectorAll('.VPContent [data-tool]').forEach((el) => {
    const group = el.closest('[data-win]')?.dataset.win || 'This page';
    const items = groups.get(group) || [];
    items.push({ label: el.dataset.tool, btns: [...el.querySelectorAll('button')].map((b) => ({ text: b.textContent.trim(), on: b.getAttribute('aria-pressed') === 'true' || b.getAttribute('aria-selected') === 'true', src: b })) });
    groups.set(group, items);
  });
  tools.value = [...groups].map(([group, items]) => ({ group, items }));
  headings.value = current.value === 'docs' ? [...document.querySelectorAll('.vp-doc h2[id]')].map((h) => ({ text: h.textContent.replace(/​/g, '').replace(/#$/, '').trim(), id: h.id })) : [];
  if (tab.value === 'tools' && !tools.value.length) tab.value = current.value;
  spy();
}
function spy() {
  const ids = current.value === 'docs' ? headings.value.map((h) => h.id) : (SECTIONS[current.value] || []).map((s) => s[1]);
  const line = headerOffset() + 40;
  let best = '';
  for (const id of ids) { const el = document.getElementById(id); if (el && el.getBoundingClientRect().top <= line) best = id; }
  here.value = best || ids[0] || '';
}

// Keep --vp-nav-height equal to the ribbon's height, so the default theme's layout clears it.
let ro = null, mo = null;
let lastH = 0;
const sync = () => {
  if (!root.value) return;
  const h = root.value.offsetHeight;
  if (h === lastH) return;
  lastH = h;
  document.documentElement.style.setProperty('--vp-nav-height', h + 'px');
  dispatchEvent(new Event('resize')); // live.js redraws the row gutter under the new header
};
onMounted(() => {
  try { collapsed.value = localStorage.getItem('sm-ribbon') !== 'open'; } catch { /* stays closed */ }
  tab.value = current.value;
  ro = new ResizeObserver(sync); ro.observe(root.value); sync();
  mo = new MutationObserver(() => { clearTimeout(mo.t); mo.t = setTimeout(scan, 40); });
  const c = document.querySelector('.VPContent');
  if (c) mo.observe(c, { subtree: true, childList: true, attributes: true, attributeFilter: ['aria-pressed', 'aria-selected'] });
  addEventListener('scroll', spy, { passive: true });
  addEventListener('keydown', esc);
  setTimeout(scan, 300);
});
onBeforeUnmount(() => { ro?.disconnect(); mo?.disconnect(); removeEventListener('scroll', spy); removeEventListener('keydown', esc); });
const esc = (e) => { if (e.key === 'Escape') backstage.value = false; };
watch(collapsed, (v) => { try { localStorage.setItem('sm-ribbon', v ? 'collapsed' : 'open'); } catch { /* per-viewer convenience only */ } nextTick(sync); });
watch(() => route.path, () => { if (tab.value !== 'tools') tab.value = current.value; nextTick(() => setTimeout(scan, 200)); });
watch(tab, () => nextTick(sync));
const pageKey = computed(() => (tab.value === 'tools' ? current.value : tab.value));
</script>

<template>
  <header ref="root" class="rbx">
    <div class="rb-title">
      <span class="rb-logo" aria-hidden="true">#A</span>
      <a class="rb-doc" :href="withBase('/')"><b>Cellprose</b></a>
      <button class="rb-tell" type="button" @click="search" @mouseover="hover('Search', '=SEARCH(&quot;the whole site&quot;)')">
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="7" cy="7" r="4.5" /><path d="m10.5 10.5 3.5 3.5" /></svg>
        <span>Tell me what you want to do</span><kbd>Ctrl K</kbd>
      </button>
      <a class="rb-gh" :href="REPO" target="_blank" rel="noopener">GitHub ↗</a>
    </div>

    <div class="rb-tabs" role="tablist" @dblclick="(e) => e.target.closest('.rb-tab:not(.file)') && toggle()">
      <button class="rb-tab file" type="button" @click="backstage = true">File</button>
      <button v-for="p in PAGES" :key="p.key" class="rb-tab" role="tab" type="button" :aria-selected="!collapsed && tab === p.key" :class="{ cur: current === p.key }" @click="choose(p.key)">{{ p.label }}</button>
      <button v-if="tools.length" class="rb-tab ctx" role="tab" type="button" data-ctx="Page tools" :aria-selected="!collapsed && tab === 'tools'" @click="choose('tools')">View</button>
      <div class="rb-end">
        <button class="rb-col" type="button" :aria-label="collapsed ? 'Show the ribbon' : 'Hide the ribbon'" :title="collapsed ? 'Show the ribbon' : 'Hide the ribbon'" @click="toggle">{{ collapsed ? '▾' : '▴' }}</button>
      </div>
    </div>

    <div v-show="!collapsed" class="rb-body">
      <div class="rb-panel">
        <template v-if="tab === 'tools'">
          <div v-for="g in tools" :key="g.group" class="rb-group">
            <div class="rb-cmds"><div class="rb-toggles">
              <template v-for="it in g.items" :key="it.label">
                <span class="lab">{{ it.label }}</span>
                <div class="rb-seg" role="group" :aria-label="it.label">
                  <button v-for="b in it.btns" :key="b.text" type="button" :aria-pressed="b.on"
                    @mouseover="hover(it.label, `=SET(&quot;${it.label}&quot;,&quot;${b.text}&quot;)`)" @click="press(b)">{{ b.text }}</button>
                </div>
              </template>
            </div></div>
            <div class="rb-cap">{{ g.group }}</div>
          </div>
        </template>

        <template v-else>
          <div class="rb-group">
            <div class="rb-cmds">
              <template v-if="pageKey === 'docs'">
                <button v-for="d in DOCS" :key="d[1]" class="rb-big" type="button" :aria-current="isHere(d[1]) ? 'page' : null" @mouseover="hover(d[0], `=GOTO(&quot;${d[0]}&quot;)`)" @click="open(d[1])"><svg viewBox="0 0 32 32" aria-hidden="true" v-html="I[d[2]]" /><span>{{ d[0] }}</span></button>
              </template>
              <template v-else>
                <button v-if="pageKey === 'playground'" class="rb-big" type="button" @mouseover="hover('Open', '=OPEN(&quot;.xlsx&quot;)')" @click="openFile"><svg viewBox="0 0 32 32" aria-hidden="true" v-html="I.open" /><span>Open .xlsx…</span></button>
                <button v-for="k in GO[pageKey]" :key="k" class="rb-big" type="button" @mouseover="hover(PAGES.find((p) => p.key === k).label, `=GOTO(&quot;${PAGES.find((p) => p.key === k).label}&quot;)`)" @click="choose(k)">
                  <svg viewBox="0 0 32 32" aria-hidden="true" v-html="I[PAGES.find((p) => p.key === k).icon]" /><span>{{ PAGES.find((p) => p.key === k).label }}</span></button>
              </template>
            </div>
            <div class="rb-cap">{{ pageKey === 'docs' ? 'Docs pages' : 'Open' }}</div>
          </div>

          <div v-if="pageKey === 'docs' ? headings.length && current === 'docs' : SECTIONS[pageKey]" class="rb-group">
            <div class="rb-cmds"><div class="rb-jumps">
              <template v-if="pageKey === 'docs'">
                <button v-for="h in headings" :key="h.id" class="rb-jump" type="button" :class="{ here: here === h.id }" @mouseover="hover(h.text.split(' ')[0], `=SCROLL(&quot;${h.text}&quot;)`)" @click="jump('docs', h.id)"><b>↓</b>{{ h.text }}</button>
              </template>
              <template v-else>
                <button v-for="s in SECTIONS[pageKey]" :key="s[1]" class="rb-jump" type="button" :class="{ here: current === pageKey && here === s[1] }" @mouseover="hover(s[0].split(' ')[0], `=SCROLL(&quot;${s[0]}&quot;)`)" @click="jump(pageKey, s[1])"><b>↓</b>{{ s[0] }}</button>
              </template>
            </div></div>
            <div class="rb-cap">{{ pageKey === 'docs' ? `On “${pageData.title}”` : 'On this page' }}</div>
          </div>

          <div class="rb-group">
            <div class="rb-cmds"><div class="rb-jumps">
              <a v-for="l in [['Source on GitHub', REPO], ['Specification on GitHub', REPO + '/blob/main/docs/SPEC.md'], ['Report an issue', REPO + '/issues']]" :key="l[0]" class="rb-jump ext" :href="l[1]" target="_blank" rel="noopener"
                @mouseover="hover('GitHub', `=HYPERLINK(&quot;${l[1]}&quot;)`)"><b>↗</b>{{ l[0] }}</a>
            </div></div>
            <div class="rb-cap">Elsewhere</div>
          </div>
        </template>
      </div>
    </div>

    <div class="lfbar"><span class="nb">A1</span><span class="fx">fx</span><span class="fm"></span></div>
    <div class="lcols" aria-hidden="true"></div>
  </header>

  <div v-if="backstage" class="rb-backstage" role="dialog" aria-label="File">
    <nav class="rb-bsnav">
      <button type="button" aria-label="Back to the site" style="font-size:20px" @click="backstage = false">←</button>
      <button type="button" aria-pressed="true">Recent</button>
      <button type="button" @click="backstage = false; openFile()">Open .xlsx…</button>
    </nav>
    <div class="rb-bsmain">
      <h2>Recent workbooks</h2>
      <p class="lede">The benchmark samples. Opening one shows it in the playground, converted in your browser by the JS writer.</p>
      <div class="rb-recent">
        <button v-for="s in SAMPLES" :key="s[1]" type="button" @click="openSample(s[0])"><i>.md</i><span>{{ s[0] }}</span><small>{{ s[1] }}</small></button>
      </div>
    </div>
  </div>
</template>
