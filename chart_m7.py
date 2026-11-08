"""Generate the M7 chart: the real rename signal is 15.2%, not 94.8% (bare).

Usage:
    python chart_m7.py
"""
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import duckdb

from db import SPECMINE_DATA
from taxonomy import classify_path

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m7_calibration.png"
FULL = Path(SPECMINE_DATA)

SHAPES = ["relative_ext", "bare_ext", "glob", "absolute"]


def main():
    conn = duckdb.connect(":memory:")
    rows = conn.execute(f"""
        SELECT code_path, resolved_path
        FROM read_parquet('{FULL}/openspec_code_refs.parquet')
        WHERE task_done = 1 AND anchor_sha IS NOT NULL
          AND exists_at_anchor = 1 AND resolved_path IS NOT NULL AND resolved_path != ''
    """).fetchall()
    conn.close()

    diff = Counter()
    total = Counter()
    for cp, rp in rows:
        _, shape = classify_path(cp)
        if shape in SHAPES:
            total[shape] += 1
            if rp != cp:
                diff[shape] += 1

    pcts = [diff[s] / total[s] * 100 if total[s] else 0.0 for s in SHAPES]

    fig, ax = plt.subplots(figsize=(7, 3.2))
    colors = ["#d62728" if s == "relative_ext" else "#7f7f7f" for s in SHAPES]
    bars = ax.barh(SHAPES, pcts, color=colors, edgecolor="white")
    ax.set_xlabel("% of resolved refs whose resolved_path != code_path")
    ax.set_title("Calibration: 15.2% rename (relative_ext) vs 94.8% bare (tautological)")
    for b, v in zip(bars, pcts):
        ax.text(v, b.get_y() + b.get_height() / 2, f"  {v:.1f}%", va="center")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
