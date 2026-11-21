'use strict';
// A small XML parser for OOXML parts: elements with local names (prefixes dropped), attributes, direct text, children.
// Not a validating parser. It does not resolve DTDs or external entities.

const ENTITIES = { lt: '<', gt: '>', amp: '&', quot: '"', apos: "'" };

function decode(s) {
  if (!s.includes('&')) return s;
  return s.replace(/&(?:#x([0-9a-fA-F]+)|#(\d+)|(\w+));/g, (m, hex, dec, name) => {
    const cp = hex ? parseInt(hex, 16) : dec ? parseInt(dec, 10) : -1;
    if (cp >= 0) return cp <= 0x10ffff ? String.fromCodePoint(cp) : m;
    return ENTITIES[name] !== undefined ? ENTITIES[name] : m;
  });
}

const bad = (what) => { throw new Error(`malformed XML: ${what}`); };
const find = (src, token, from, what) => {
  const k = src.indexOf(token, from);
  return k < 0 ? bad(`unterminated ${what}`) : k;
};

const local = (n) => n.slice(n.indexOf(':') + 1);

function parseXml(src) {
  const root = { name: '#root', attrs: {}, children: [], text: '' };
  const stack = [root];
  const ATTR = /([^\s=]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g;
  let i = 0;
  const n = src.length;
  while (i < n) {
    const lt = src.indexOf('<', i);
    const top = stack[stack.length - 1];
    if (lt < 0) break;
    if (lt > i) top.text += decode(src.slice(i, lt));
    if (src.startsWith('<!--', lt)) {
      i = find(src, '-->', lt, 'comment') + 3;
    } else if (src.startsWith('<![CDATA[', lt)) {
      const end = find(src, ']]>', lt, 'CDATA section');
      top.text += src.slice(lt + 9, end);
      i = end + 3;
    } else if (src[lt + 1] === '?' || src[lt + 1] === '!') {
      i = find(src, '>', lt, 'declaration') + 1;
    } else if (src[lt + 1] === '/') {
      if (stack.length > 1) stack.pop();
      i = find(src, '>', lt, 'closing tag') + 1;
    } else {
      const end = find(src, '>', lt, 'tag');
      const selfClosing = src[end - 1] === '/';
      const tag = src.slice(lt + 1, selfClosing ? end - 1 : end);
      const sp = tag.search(/\s/);
      const node = { name: local(sp < 0 ? tag : tag.slice(0, sp)), attrs: {}, children: [], text: '' };
      if (sp >= 0) {
        ATTR.lastIndex = 0;
        for (let m; (m = ATTR.exec(tag.slice(sp))); ) node.attrs[local(m[1])] = decode(m[2] !== undefined ? m[2] : m[3]);
      }
      top.children.push(node);
      if (!selfClosing) stack.push(node);
      i = end + 1;
    }
  }
  return root.children[0];
}

const child = (node, name) => (node ? node.children.find((c) => c.name === name) : undefined);
const kids = (node, name) => (node ? node.children.filter((c) => c.name === name) : []);

module.exports = { parseXml, child, kids };
