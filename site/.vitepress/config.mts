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

const GITHUB = 'https://github.com/Utkarsh-Gaikwad/cellprose';
const SITE_URL = (process.env.SITE_URL || 'https://cellprose.com').replace(/\/$/, '');
const DESCRIPTION = 'An open plain-text format for spreadsheet workbooks. Models answer questions about it more accurately and for less cost per correct answer than from CSV or MarkItDown, and it renders as tables on GitHub.';

export default defineConfig({
  title: 'Cellprose',
  description: DESCRIPTION,
  sitemap: { hostname: SITE_URL },
  transformPageData(pageData) {
    const path = pageData.relativePath.replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '');
    const url = `${SITE_URL}/${path}`;
    const title = pageData.title && pageData.relativePath !== 'index.md' ? `${pageData.title} | Cellprose` : 'Cellprose';
    const desc = pageData.description || DESCRIPTION;
    pageData.frontmatter.head ??= [];
    pageData.frontmatter.head.push(
      ['link', { rel: 'canonical', href: url }],
      ['meta', { property: 'og:type', content: 'website' }],
      ['meta', { property: 'og:site_name', content: 'Cellprose' }],
      ['meta', { property: 'og:title', content: title }],
      ['meta', { property: 'og:description', content: desc }],
      ['meta', { property: 'og:url', content: url }],
      ['meta', { name: 'twitter:card', content: 'summary' }],
      ['meta', { name: 'twitter:title', content: title }],
      ['meta', { name: 'twitter:description', content: desc }],
    );
  },
  base: process.env.SITE_BASE || '/',
  cleanUrls: true,
  appearance: false,
  lastUpdated: false,
  head: [
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800&family=Geist+Mono:wght@400;500;600&display=swap' }],
    ['meta', { name: 'theme-color', content: '#107c41' }],
    ['link', { rel: 'icon', type: 'image/svg+xml', href: (process.env.SITE_BASE || '/') + 'favicon.svg' }],
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
      message: 'Cellprose is an open format for spreadsheet workbooks. Benchmarks: pre-registered run of 11 Nov 2026, 58 held-out workbooks, four models, three repeats. <a href="/privacy">Privacy</a>',
      copyright: `Copyright © 2026 Utkarsh Gaikwad · Code under <a href="${GITHUB}/blob/main/LICENSE">Apache-2.0</a> · Spec under <a href="${GITHUB}/blob/main/LICENSE-SPEC">CC-BY-4.0</a>`,
    },
  },
});
