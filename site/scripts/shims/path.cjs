// The part of Node's path module that js/src/xlsx.js uses: path.posix.{normalize, join, dirname}.
function normalize(p) {
  const out = [];
  for (const part of p.split('/')) {
    if (part === '..') out.pop();
    else if (part && part !== '.') out.push(part);
  }
  return (p.startsWith('/') ? '/' : '') + out.join('/');
}
const join = (...parts) => normalize(parts.filter(Boolean).join('/'));
const dirname = (p) => {
  const i = p.lastIndexOf('/');
  return i < 0 ? '.' : i === 0 ? '/' : p.slice(0, i);
};
const posix = { normalize, join, dirname };
module.exports = { posix, ...posix };
