// How links in docs/ are rewritten when those files become pages of the site.
import { posix } from 'node:path';

export const GITHUB = 'https://github.com/cellprose/cellprose/blob/main/';
// docs/ file -> page under reference/
export const REFERENCE = { 'SPEC.md': 'spec', 'DESIGN.md': 'design', 'PROTOCOL.md': 'protocol' };

// `from` is the file's path in the repo. Links to another reference page stay on the site, images come from
// public/img, and anything else in the repo goes to GitHub.
export function rewriteLinks(md, from) {
  return md.replace(/(!?)\[([^\]]*)\]\(([^)\s]+)\)/g, (m, bang, text, href) => {
    if (/^(https?:|mailto:|#)/.test(href)) return m;
    const [path, hash] = href.split('#');
    const target = posix.normalize(posix.join(posix.dirname(from), path));
    const anchor = hash ? '#' + hash : '';
    if (target.startsWith('docs/img/')) return `${bang}[${text}](/img/${target.slice('docs/img/'.length)})`;
    const page = target.startsWith('docs/') && REFERENCE[target.slice(5)];
    if (page) return `${bang}[${text}](./${page}${anchor})`;
    return `${bang}[${text}](${GITHUB}${target}${anchor})`;
  });
}
