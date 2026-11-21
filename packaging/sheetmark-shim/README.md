# sheetmark (renamed to cellprose)

Sheetmark is now called **Cellprose**. This package exists so that `pip install sheetmark`, `import sheetmark` and the
`sheetmark` command keep working. It depends on `cellprose` and forwards everything to it. Use `cellprose` in new code.

Files keep working too: the reader accepts both the old `sheetmark:` and the new `cellprose:` front-matter key, and both
`.sheet.md` and `.cellprose.md` file names.
