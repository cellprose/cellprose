"""Encoding / variant ids. The Nov 2026 rename keeps the old ids working: `canon` maps an old id to its current one.

Meaning is unchanged: the old `sheetmark_v03` was the v0.3 text WITHOUT the row-number legend (E28-E30), the old
`sheetmark_v031` the text WITH it (E31, E32); the legend is now part of v0.3 (SPEC section 3.1).
"""
LEGACY = {"sheetmark_v03": "cellprose_v03_nolegend", "sheetmark_v031": "cellprose_v03",
          "agent_sheetmark_v03": "agent_cellprose_v03_nolegend", "agent_sheetmark_v031": "agent_cellprose_v03"}


def canon(enc):
    return LEGACY.get(enc, enc)
