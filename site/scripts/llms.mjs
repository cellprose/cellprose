// Builds /llms.txt (an index for agents, per llmstxt.org) and /llms-full.txt (the spec, the skill and the install
// steps in one file) from the repo's own docs, so they cannot drift from them.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const RAW = 'https://raw.githubusercontent.com/cellprose/cellprose/main/';
const BLOB = 'https://github.com/cellprose/cellprose/blob/main/';

// SITE_URL (for example https://example.org/) turns the site links into absolute ones; unset, the index links to the
// repository, which is where the same files live.
export function llmsIndex(siteUrl = '') {
  const site = (path, repo) => (siteUrl ? new URL(path, siteUrl.replace(/\/?$/, '/')).href : repo);
  return `# Cellprose

> Cellprose (.sheet.md) is an open plain-text format for spreadsheet workbooks. A workbook becomes one GitHub-Flavored Markdown file: values in tables with row numbers and column letters, formulas as fill ranges, number formats and named ranges. Models answer questions about it with fewer total tokens than with CSV, Markdown or TOON, and can tell typed-in numbers from formulas. The current format is v0.3.

How to read a file, in short: address cells as Sheet!C4 from the column header and the row number; every cell inside a fill range such as B4:E4 = B2*B3 is a formula, shifted like Excel's fill handle; a number in no fill range is typed in; formula results are rounded to 6 significant figures.

## Format

- [Specification v0.3](${site('reference/spec', RAW + 'docs/SPEC.md')}): the full format, with examples that are tested against the writer
- [Design decisions](${site('reference/design', RAW + 'docs/DESIGN.md')}): benchmark results, why each choice was made, limitations
- [Agent skill](${RAW}skills/cellprose/SKILL.md): a short guide that teaches a model to read and edit the format

## Use it

- [Install and integrations](${RAW}INTEGRATIONS.md): CLI, Python, MCP server (list_sheets, read_workbook, write_cells), agent skill, git hooks
- [Source and README](${BLOB}README.md)

## Optional

- [Benchmark protocol](${site('reference/protocol', RAW + 'docs/PROTOCOL.md')}): how runs are done, scored and reported
- [Conformance kit](${BLOB}conformance/README.md): language-neutral test cases for writers and readers
- [Full text of the above in one file](${siteUrl ? new URL('llms-full.txt', siteUrl.replace(/\/?$/, '/')).href : 'llms-full.txt'})
`;
}

const strip = (md) => md.replace(/^---\n[\s\S]*?\n---\n/, '').trim();

export function llmsFull(repo, siteUrl = '') {
  const read = (f) => readFileSync(join(repo, f), 'utf8');
  const integ = read('INTEGRATIONS.md');
  // the MCP server and agent skill sections, without the maintainers' note about refreshing the vendored copy
  const install = integ.slice(integ.indexOf('## MCP server'), integ.indexOf('After changing `src/cellprose/`'));
  return [
    llmsIndex(siteUrl).trimEnd(),
    '# Install: MCP server and agent skill\n\n' + install.trim(),
    '# The agent skill (skills/cellprose/SKILL.md)\n\n' + strip(read('skills/cellprose/SKILL.md')),
    '# Specification (docs/SPEC.md)\n\n' + read('docs/SPEC.md').trim(),
  ].join('\n\n---\n\n') + '\n';
}
