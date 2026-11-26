import { defineConfig } from 'vitepress';

function docsSidebar() {
  return [
    {
      text: 'Guide',
      items: [
        { text: 'Why Cellprose', link: '/guide/' },
        { text: 'The format in ten minutes', link: '/guide/format' },
        { text: 'FAQ', link: '/guide/faq' },
      ],
    },
    {
      text: 'Reference',
      items: [
        { text: 'Specification v0.3', link: '/reference/spec' },
        { text: 'Design decisions', link: '/reference/design' },
        { text: 'Benchmark protocol', link: '/reference/protocol' },
      ],
    },
  ];
}

const GITHUB = 'https://github.com/cellprose/cellprose';
const SITE_URL = (process.env.SITE_URL || 'https://cellprose.com').replace(/\/$/, '');
const DESCRIPTION = 'An open plain-text format for spreadsheet workbooks. Models answer questions about it more accurately and for less cost per correct answer than from CSV or MarkItDown, and it renders as tables on GitHub.';

const PAGE_DESC: Record<string, string> = {
  'index.md': DESCRIPTION,
  'playground.md': 'Drop in an .xlsx and see it as Cellprose text, with a token count against CSV. Runs in your browser; nothing is uploaded.',
  'benchmarks.md': 'Pre-registered benchmark of 11 Nov 2026: 58 held-out workbooks, four models, three repeats. Accuracy and cost per correct answer for Cellprose, CSV and MarkItDown, with limitations.',
  'ecosystem.md': 'Cellprose works with Python, JavaScript, an MCP server, a LangChain loader, a GitHub viewer and an agent skill. Where to get each.',
  'guide/index.md': 'Why models read spreadsheets badly from CSV or raw .xlsx, and how Cellprose keeps the grid and puts the logic in a short block of fill ranges.',
  'guide/format.md': 'A walk through a real Cellprose file: front matter, sheet and region headings, compact tables, formula fill ranges, formats and names.',
  'guide/faq.md': 'Is Cellprose lossless, why not give a model the .xlsx, how does it compare with CSV, and other common questions.',
  'reference/spec.md': 'The Cellprose v0.3 specification: file layout, tables, formulas, formats, merges, comments, validation and names.',
  'reference/design.md': 'Cellprose design decisions: benchmark results, format choices, architecture and roadmap.',
  'reference/protocol.md': 'How the publishable Cellprose benchmark is run, scored and reported.',
  'privacy.md': 'Cellprose collects almost no data: the playground runs in your browser and workbooks are never uploaded.',
};

export default defineConfig({
  title: 'Cellprose',
  description: DESCRIPTION,
  sitemap: { hostname: SITE_URL },
  transformPageData(pageData) {
    const path = pageData.relativePath.replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '');
    const url = `${SITE_URL}/${path}`;
    const isHome = pageData.relativePath === 'index.md';
    const title = isHome ? 'Cellprose: spreadsheets models read right' : pageData.title ? `${pageData.title} | Cellprose` : 'Cellprose';
    const desc = pageData.description || PAGE_DESC[pageData.relativePath] || DESCRIPTION;
    const ld = isHome
      ? {
          '@context': 'https://schema.org',
          '@graph': [
            { '@type': 'WebSite', '@id': `${SITE_URL}/#website`, url: `${SITE_URL}/`, name: 'Cellprose', description: DESCRIPTION },
            {
              '@type': 'SoftwareSourceCode',
              name: 'Cellprose',
              description: DESCRIPTION,
              codeRepository: GITHUB,
              url: `${SITE_URL}/`,
              license: 'https://www.apache.org/licenses/LICENSE-2.0',
              author: { '@type': 'Person', name: 'Utkarsh Gaikwad', url: 'https://utkarshgaikwad.com/' },
            },
          ],
        }
      : pageData.relativePath === 'privacy.md'
        ? null
        : {
            '@context': 'https://schema.org',
            '@type': 'TechArticle',
            headline: pageData.title || 'Cellprose',
            description: desc,
            mainEntityOfPage: url,
            image: `${SITE_URL}/og.png`,
            author: { '@type': 'Person', name: 'Utkarsh Gaikwad', url: 'https://utkarshgaikwad.com/' },
            publisher: { '@type': 'Organization', name: 'Cellprose', url: `${SITE_URL}/` },
          };
    pageData.description = desc;
    pageData.frontmatter.head ??= [];
    if (ld) pageData.frontmatter.head.push(['script', { type: 'application/ld+json' }, JSON.stringify(ld)]);
    pageData.frontmatter.head.push(
      ['meta', { property: 'og:image', content: `${SITE_URL}/og.png` }],
      ['meta', { property: 'og:image:width', content: '1200' }],
      ['meta', { property: 'og:image:height', content: '630' }],
      ['meta', { name: 'twitter:image', content: `${SITE_URL}/og.png` }],
      ['link', { rel: 'canonical', href: url }],
      ['meta', { property: 'og:type', content: 'website' }],
      ['meta', { property: 'og:site_name', content: 'Cellprose' }],
      ['meta', { property: 'og:title', content: title }],
      ['meta', { property: 'og:description', content: desc }],
      ['meta', { property: 'og:url', content: url }],
      ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
      ['meta', { name: 'twitter:title', content: title }],
      ['meta', { name: 'twitter:description', content: desc }],
    );
  },
  base: process.env.SITE_BASE || '/',
  cleanUrls: true,
  srcExclude: ['README.md'],
  appearance: false,
  lastUpdated: false,
  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800&family=Geist+Mono:wght@400;500;600&display=swap' }],
    ['meta', { name: 'theme-color', content: '#107c41' }],
    ['link', { rel: 'icon', type: 'image/svg+xml', href: (process.env.SITE_BASE || '/') + 'favicon.svg' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: (process.env.SITE_BASE || '/') + 'favicon-32.png' }],
    ['link', { rel: 'apple-touch-icon', href: (process.env.SITE_BASE || '/') + 'apple-touch-icon.png' }],
  ],
  themeConfig: {
    logo: false,
    siteTitle: 'Cellprose',
    nav: [
      { text: 'Playground', link: '/playground' },
      { text: 'Docs', link: '/guide/', activeMatch: '^/(guide|reference)/' },
      { text: 'Benchmarks', link: '/benchmarks' },
      { text: 'Ecosystem', link: '/ecosystem' },
    ],
    sidebar: {
      '/guide/': docsSidebar(),
      '/reference/': docsSidebar(),
    },
    socialLinks: [{ icon: 'github', link: GITHUB }],
    search: { provider: 'local' },
    outline: { level: [2, 3], label: 'On this sheet' },
    docFooter: { prev: 'Previous', next: 'Next' },
    footer: {
      message: 'Cellprose is an open format for spreadsheet workbooks. Benchmarks: pre-registered run of 11 Nov 2026, 58 held-out workbooks, four models, three repeats. <a href="/privacy">Privacy</a> · Hosted tools built on Cellprose: <a href="https://tablient.com">Tablient</a> · By <a href="https://utkarshgaikwad.com">Utkarsh Gaikwad</a>',
      copyright: `Copyright © 2026 Utkarsh Gaikwad · Code under <a href="${GITHUB}/blob/main/LICENSE">Apache-2.0</a> · Spec under <a href="${GITHUB}/blob/main/LICENSE-SPEC">CC-BY-4.0</a>`,
    },
  },
});
