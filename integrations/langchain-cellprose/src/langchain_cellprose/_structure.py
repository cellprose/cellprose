"""Read the layout of Cellprose text: front matter, sheets, regions, blocks and names.

This is a line-level reader for splitting. It never builds cells, so it also works on compact-profile text, which
`cellprose.load` refuses. Geometry uses the same `openpyxl.utils.range_boundaries` as the core reader.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from openpyxl.utils import range_boundaries

LEGEND_PREFIX = "Note: the first field of each table row is its row number, not a cell;"
SHEET_LEVEL = {"cells", "merges", "arrays", "comments", "validation"}
Box = tuple[int, int, int, int]          # (first row, first column, last row, last column)
_LEAD = re.compile(r"^\$?([A-Z]{1,3})\$?(\d+)(?::\$?([A-Z]{1,3})\$?(\d+))?(?= = |: |$)")


@dataclass
class Block:
    kind: str
    lines: list[str]

    def text(self) -> str:
        return "\n".join([f"```{self.kind}", *self.lines, "```"])


@dataclass
class Region:
    heading: str
    box: Box
    table: list[str] = field(default_factory=list)       # column header, rule, then rows
    blocks: list[Block] = field(default_factory=list)


@dataclass
class SheetPart:
    name: str
    index: int
    heading: str
    meta: Block | None = None
    regions: list[Region] = field(default_factory=list)
    tail: list[Block] = field(default_factory=list)       # sheet-level blocks (cells, merges, comments, ...)


@dataclass
class Parsed:
    front: list[str]                                      # front matter lines, fences included
    meta: dict[str, str]
    legend: str | None
    sheets: list[SheetPart]
    names: Block | None


def box_of(rng: str) -> Box | None:
    try:
        c1, r1, c2, r2 = range_boundaries(rng.replace("$", ""))
    except (ValueError, TypeError):
        return None
    if None in (c1, r1, c2, r2):
        return None
    return r1, c1, r2, c2


def line_box(line: str) -> Box | None:
    """The range a block line talks about (`D2:D3 = B2*C2`, `C3: text`, `A1:C1`), or None when unreadable."""
    m = _LEAD.match(line.strip())
    return box_of(m.group(0)) if m else None


def overlaps(a: Box, b: Box) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def sheet_name(heading: str) -> str:
    name = heading[len("# Sheet: "):].strip()
    return name[1:-1] if len(name) >= 2 and name[0] == name[-1] == '"' else name


def row_number(line: str) -> int | None:
    first = line.lstrip("|").split("|", 1)[0].strip()
    return int(first) if first.isdigit() else None


def _front_matter(lines: list[str]) -> tuple[list[str], dict[str, str], int]:
    if not lines or lines[0].strip() != "---" or "---" not in [x.strip() for x in lines[1:]]:
        return [], {}, 0
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    meta: dict[str, str] = {}
    for line in lines[1:end]:
        k, sep, v = line.partition(":")
        if sep:
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] == "'":
                v = v[1:-1]
            meta[k.strip()] = v
    return lines[: end + 1], meta, end + 1


def parse(text: str) -> Parsed:
    lines = text.split("\n")
    front, meta, i = _front_matter(lines)
    legend = None
    out = Parsed(front, meta, None, [], None)
    sheet: SheetPart | None = None
    region: Region | None = None
    in_names = False
    prev_kind = ""
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            kind = line[3:].strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            block = Block(kind, lines[i + 1: j])
            i = j + 1
            if in_names:
                if kind == "names":
                    out.names = block
            elif sheet is None:
                pass
            elif kind == "meta" and not sheet.regions and sheet.meta is None:
                sheet.meta = block
            elif region is not None and kind not in SHEET_LEVEL and not (kind == "formats" and prev_kind in
                                                                           SHEET_LEVEL | {"tail-formats"}):
                region.blocks.append(block)
            else:
                sheet.tail.append(block)
                prev_kind = "tail-formats" if kind == "formats" else kind
                continue
            prev_kind = kind
            continue
        i += 1
        if line.startswith("# Sheet: "):
            sheet = SheetPart(sheet_name(line), len(out.sheets), line)
            out.sheets.append(sheet)
            region, in_names, prev_kind = None, False, ""
        elif line.strip() == "# Names":
            sheet, region, in_names = None, None, True
        elif line.startswith("## ") and sheet is not None:
            box = box_of(line[3:].strip())
            if box is None:
                continue
            region = Region(line, box)
            sheet.regions.append(region)
            prev_kind = ""
        elif region is not None and (line.startswith(("#|", "|#|")) or
                                     (region.table and (line.startswith(("|", "-|", "…|"))
                                                        or row_number(line) is not None))):
            region.table.append(line)
        elif line.startswith(LEGEND_PREFIX) and sheet is None and not in_names:
            legend = line
    out.legend = legend
    return out


def names_in(block: Block | None) -> list[tuple[str | None, str, str]]:
    """(scope sheet or None, name, target) for each line of a `names` block."""
    found = []
    for line in block.lines if block else []:
        left, sep, target = line.partition(" = ")
        if not sep:
            continue
        scope, bang, name = left.rpartition("!")
        found.append((scope.strip("'") if bang else None, name, target))
    return found


def target_box(target: str) -> tuple[str, Box] | None:
    """(sheet, box) for a name target such as `Plan!$B$2:$B$3` or `'My Sheet'!A1`; None for anything else."""
    sheet, bang, ref = target.rpartition("!")
    if not bang:
        return None
    box = box_of(ref)
    return (sheet.strip("'").replace("''", "'"), box) if box else None
