"""Headline chart for benchmarks/RESULTS.md: Cellprose cost per correct answer as a ratio to each baseline, one row per
model with its 95% interval, one panel per corpus and baseline. Reads the verdicts.json that analyze.py wrote; it adds
no statistics of its own.

    python3 plot_results.py results/run_rw2 results/run_sb ../docs/img/benchmark-run.png
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402

BASELINES = [("markitdown", "MarkItDown"), ("csv", "CSV (reference)"),
             ("agent_xlsx", "Agent + shell on .xlsx"), ("agent_xlsx_viewer", "Agent + formula viewer")]
MODELS = [("haiku55", "Claude Haiku 5.5"), ("sonnet55", "Claude Sonnet 5.5"),
          ("gpt6luna", "GPT-6 Luna"), ("gpt61sol", "GPT-6.1 Sol")]
INK, MUTED, GRID, SURFACE, MARK = "#0b0b0b", "#52514e", "#d9d8d4", "#fcfcfb", "#2a78d6"


def main(rw2: str, sb: str, out: str):
    corpora = [("Real-world (30 workbooks, 163 questions)", rw2), ("SpreadsheetBench (28 workbooks, 111 questions)", sb)]
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharex=True, sharey=True, facecolor=SURFACE)
    titles = []
    for r, (title, d) in enumerate(corpora):
        v = [x for x in json.loads((Path(d) / "verdicts.json").read_text()) if x["set"] == "held_out"]
        for c, (base, blabel) in enumerate(BASELINES):
            ax = axes[r][c]
            ax.set_facecolor(SURFACE)
            ax.axvline(1.0, color=MUTED, lw=1, ls=(0, (3, 3)))
            for i, (m, _) in enumerate(MODELS):
                x = next(e for e in v if e["model"] == m and e["baseline"] == base)
                y = len(MODELS) - 1 - i
                ax.plot([x["ratio_lo"], x["ratio_hi"]], [y, y], color=MARK, lw=2, solid_capstyle="round")
                win = x["verdict"] == "win"
                ax.plot(x["ratio"], y, "o", ms=8, color=MARK, mfc=MARK if win else SURFACE, mew=2)
                ax.text(14, y, "win" if win else ("loss" if x["verdict"] == "loss" else "no diff."),
                        va="center", ha="right", fontsize=8.5, color=INK if win else MUTED)
            ax.set_xscale("log")
            ax.set_xlim(0.1, 15)
            ax.set_xticks([0.25, 0.5, 1, 2, 4])
            ax.set_xticklabels(["0.25", "0.5", "1", "2", "4"], color=MUTED, fontsize=8.5)
            ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
            ax.grid(axis="x", color=GRID, lw=0.6)
            for s in ax.spines.values():
                s.set_visible(False)
            ax.tick_params(length=0)
            ax.set_title(f"vs {blabel}", fontsize=10, color=INK)
        axes[r][0].set_yticks(range(len(MODELS)))
        axes[r][0].set_yticklabels([lbl for _, lbl in reversed(MODELS)], color=INK, fontsize=9)
        titles.append(title)
    fig.suptitle("Cellprose cost per correct answer, as a ratio to each baseline (below 1 = cheaper)",
                 fontsize=12, color=INK, x=0.01, ha="left")
    fig.text(0.01, 0.01, "Dot: ratio; line: 95% paired bootstrap interval over workbooks. Filled dot = win "
             "(whole interval below 1, at most 1 accuracy point lost). Tokens priced uncached at list price, "
             "prices checked 2026-11-11; 3 repeats.", fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95), h_pad=3.5)
    for r, title in enumerate(titles):
        y = axes[r][0].get_position().y1 + 0.045
        fig.text(0.01, y, title, fontsize=10.5, color=INK, weight="bold")
    fig.savefig(out, dpi=150, facecolor=SURFACE)


if __name__ == "__main__":
    main(*sys.argv[1:4])
