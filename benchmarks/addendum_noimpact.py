"""The primary real-world view of docs/PROTOCOL_ADDENDUM.md section 4: impact questions left out of every arm's
accuracy, cost per call unchanged. Writes <run dir>_noimpact with the run's raw files (linked) and a scores.csv without
impact rows; then run analyze.py on it.

    python3 addendum_noimpact.py results/addendum_rw2
    CELLPROSE_CORPUS=external/realworld2 RESULTS_DIR=results/addendum_rw2_noimpact COMPARE_ENC=agent_cellprose_lean python3 analyze.py
"""
import sys
from pathlib import Path

import pandas as pd


def main(run_dir: str) -> Path:
    src = Path(run_dir).resolve()
    out = src.with_name(src.name + "_noimpact")
    out.mkdir(exist_ok=True)
    if not (out / "raw").exists():
        (out / "raw").symlink_to(src / "raw", target_is_directory=True)
    s = pd.read_csv(src / "scores.csv")
    s[s.task != "impact"].to_csv(out / "scores.csv", index=False)
    print(f"{out}: {int((s.task == 'impact').sum())} impact rows left out, {int((s.task != 'impact').sum())} kept")
    return out


if __name__ == "__main__":
    main(sys.argv[1])
