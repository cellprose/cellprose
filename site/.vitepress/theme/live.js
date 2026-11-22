// The page grid: column letters across the top and row numbers down the gutter, drawn from the same 104 x 28 px cells
// that the green section tabs use for their ranges. Purely visual; nothing on the page is clickable as a cell.
const CW = 104, RH = 28;
const $ = (s) => document.querySelector(s);
const col = (n) => { let s = ''; n++; while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); } return s; };
const addr = (x) => col(x.c) + x.r;
// Where the row gutter is drawn (0 on phones, where it is hidden).
const gutter = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sm-g')) || 0;
// Page y of the top of row 1: the bottom of the ribbon (--vp-nav-height tracks its height), so row 1 sits right below it.
const OY = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--vp-nav-height')) || 0;
const SECTIONS = 'section.block,.VPDoc .content-container';

let rowsEl, colsEl, raf = 0, started = false;

const cellAt = (px, py) => ({ c: Math.max(0, Math.floor((px - gutter()) / CW)), r: Math.max(1, Math.floor((py - OY()) / RH) + 1) });
function headerBottom() {
  const rb = $('.rbx');
  return rb ? Math.max(0, rb.getBoundingClientRect().bottom) : 0;
}

function drawCols() {
  const n = Math.ceil((innerWidth - gutter()) / CW) + 1;
  let h = '';
  for (let i = 0; i < n; i++) h += `<span data-c="${i}" style="left:${i * CW}px;width:${CW}px">${col(i)}</span>`;
  colsEl.innerHTML = h;
}
function drawRows() {
  const top = headerBottom(), oy = OY(), r0 = Math.max(1, Math.floor((scrollY + top - oy) / RH) + 1), n = Math.ceil(innerHeight / RH) + 2;
  let h = `<b style="height:${top}px"></b>`;
  for (let r = r0; r < r0 + n; r++) h += `<span data-r="${r}" style="top:${oy + (r - 1) * RH - scrollY}px">${r}</span>`;
  rowsEl.innerHTML = h;
}
// Each section's green tab carries the range it covers on the page grid.
function ranges() {
  document.querySelectorAll(SECTIONS).forEach((s) => {
    if (!s.dataset.win) s.dataset.win = (document.title.split('|')[0] || 'Docs').trim();
    const r = s.getBoundingClientRect();
    const a = cellAt(r.left + scrollX, r.top + scrollY), b = cellAt(r.right + scrollX - 1, r.bottom + scrollY - 1);
    s.dataset.range = addr(a) + ':' + addr(b);
  });
}
export function routeChanged() {
  if (!started) return;
  setTimeout(() => { ranges(); drawRows(); }, 60);
  setTimeout(ranges, 500);
}

export function start() {
  if (started) return;
  started = true;
  rowsEl = $('.lrows'); colsEl = $('.lcols');
  const frame = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(drawRows); };
  addEventListener('scroll', frame, { passive: true });
  addEventListener('resize', () => { drawCols(); drawRows(); ranges(); });
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(() => ranges()).observe(document.getElementById('app') || document.body);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(ranges);
  drawCols(); drawRows(); ranges();
}
