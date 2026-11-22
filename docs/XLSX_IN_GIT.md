# Using Cellprose with .xlsx files in git

Two pieces make `.xlsx` files reviewable on GitHub. Both ship in the `cellprose` package.

## One-time setup, per clone

```bash
pip install cellprose
cellprose git-setup          # add --no-hook for the diff driver only
```

This sets `diff.cellprose.textconv` in the repo's git config, adds `*.xlsx diff=cellprose` to `.gitattributes` (commit that file so teammates get the attribute), and appends a call to `cellprose pre-commit` to `.git/hooks/pre-commit`. Running it again changes nothing. Git config and hooks are not versioned, so every clone runs the command once.

## Diff driver

`git diff`, `git log -p` and `git show` print the Cellprose text of each workbook, so a changed cell or formula shows as a normal line diff. The driver never recalculates (no LibreOffice needed) and leaves out the `source:` line, so diffs only contain real changes. Run `cellprose textconv book.xlsx` to see what git sees.

## Pre-commit hook

On commit, each staged `.xlsx`/`.xlsm` is encoded from the **staged** content to a sidecar `name.sheet.md` in the same folder, and the sidecar is staged with it. GitHub renders the sidecar as tables and diffs it line by line. When a workbook is deleted, its sidecar is removed. A workbook that cannot be read aborts the commit with the file name.

Formula results come from the workbook's cached values; a file saved by a library that did not calculate formulas shows `?` for them. Open and save it in Excel or LibreOffice first.

### With the pre-commit framework

```yaml
repos:
  - repo: https://github.com/cellprose/cellprose
    rev: main
    hooks:
      - id: cellprose
```

This needs `cellprose` on the PATH (`language: system`).

## Extension

The sidecar extension is the constant `EXT` in `src/cellprose/gitflow.py`.
