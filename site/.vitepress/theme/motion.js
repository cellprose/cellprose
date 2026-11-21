// Three always-moving touches, all off for readers whose system asks for reduced motion:
// a blinking cursor in the formula bar that types example formulas while the reader is idle, marching ants around
// the home page's numbers, and a status bar that cycles between Ready and Calculating.
const $ = (s) => document.querySelector(s);
const FORMULAS = [['B4:E4', '=B2*B3'], ['F2', '=SUM(B2:E2)'], ['C6:N6', '=B6*(1+$B$1)'], ['D9', '=IF(C9>0,C9/B9-1,"")'], ['B12', '=XLOOKUP(A12,Rates!A:A,Rates!B:B)']];
const IDLE_MS = 2500;
let started = false, box = null;

const busy = () => !!$('.lsel.show'); // a selected cell owns the formula bar and status bar
const esc = (s) => s.replace(/[&<]/g, (c) => (c === '&' ? '&amp;' : '&lt;'));

function typing() {
  let last = Date.now(), fi = 0, ci = 0, phase = 'type', hold = 0;
  addEventListener('mousemove', () => { last = Date.now(); }, { passive: true });
  addEventListener('keydown', () => { last = Date.now(); });
  setInterval(() => {
    const fm = $('.lfbar .fm'), nb = $('.lfbar .nb');
    if (!fm || !nb || Date.now() - last < IDLE_MS || busy()) return;
    const [a, f] = FORMULAS[fi];
    if (phase === 'type') { nb.textContent = a; ci++; fm.innerHTML = '<span class="op">=</span>' + esc(f.slice(1, ci)); if (ci >= f.length) { phase = 'hold'; hold = 0; } }
    else if (phase === 'hold') { if (++hold > 22) phase = 'erase'; }
    else { ci = Math.max(0, ci - 3); fm.innerHTML = ci ? '<span class="op">=</span>' + esc(f.slice(1, ci)) : ''; if (!ci) { phase = 'type'; fi = (fi + 1) % FORMULAS.length; } }
  }, 70);
}

// Hug the numbers with a little room, inside the white sheet they sit on.
function ants() {
  const s = $('.VPContent .stats');
  if (!s || !s.offsetParent) { box.style.display = 'none'; return; }
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  s.querySelectorAll('.stat').forEach((e) => { const r = e.getBoundingClientRect(); x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); });
  const P = 10, w = (s.closest('[data-win]') || s).getBoundingClientRect();
  x0 = Math.max(w.left + 4, x0 - P); x1 = Math.min(w.right - 4, x1 + P); y0 -= P; y1 += P;
  Object.assign(box.style, { display: 'block', left: x0 + scrollX + 'px', top: y0 + scrollY + 'px', width: x1 - x0 + 'px', height: y1 - y0 + 'px' });
}

function status() {
  const st = $('.lstat'), msg = st && st.querySelector('.msg');
  if (!msg) return;
  const bar = document.createElement('span');
  bar.className = 'mo-bar'; bar.innerHTML = '<i></i>';
  msg.after(bar);
  setInterval(() => {
    if (busy() || msg.textContent !== 'Ready') return;
    st.classList.add('calc'); msg.textContent = 'Calculating (4 threads)…';
    const i = bar.firstChild; i.style.animation = 'none'; void i.offsetWidth; i.style.animation = '';
    setTimeout(() => { st.classList.remove('calc'); if (!busy()) msg.textContent = 'Ready'; }, 1700);
  }, 6000);
}

export function start() {
  if (started || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  started = true;
  document.body.classList.add('mo');
  box = document.createElement('div'); box.className = 'mo-ants'; document.body.appendChild(box);
  typing(); status(); ants();
  addEventListener('resize', ants);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(ants);
  setInterval(ants, 1500);
}
export function routeChanged() { if (started) setTimeout(ants, 120); }
