"""Generate the M2 chart: every spec-touching PR is merged (Q3 unanswerable).

Usage:
    python chart_m2.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt

import chart_style as cs
from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m2_pivot.png"
FULL = Path(SPECMINE_DATA)


def main():
    cs.apply_style()

    conn = duckdb.connect(":memory:")
    rows = conn.execute(
        f"SELECT is_merged, COUNT(*) FROM read_parquet('{FULL.as_posix()}/pull_requests.parquet') "
        "GROUP BY 1 ORDER BY 1"
    ).fetchall()
    conn.close()

    counts = {row[0]: row[1] for row in rows}
    merged = counts.get(1, 0)
    rejected = counts.get(0, 0)
    total = merged + rejected

    fig, ax = plt.subplots(figsize=(7.4, 2.6))
    bars = ax.barh(["merged"], [merged], height=0.42, color=cs.BLUE,
                   edgecolor=cs.INK, linewidth=0.8)
    cs.hlabel(ax, bars, [f"{cs.fmt_int(merged)}  ({merged / total * 100:.1f}%)"],
              fontsize=10)
    cs.int_axis(ax, "x")
    cs.hgrid(ax)
    ax.set_ylim(-0.9, 0.7)
    ax.set_xlabel("spec-touching pull requests in the full dataset")
    ax.text(0.0, -0.72,
            f"rejected (is_merged = 0): {cs.fmt_int(rejected)} — no rejected "
            "spec-touching PR exists in the corpus",
            fontsize=9.5, color=cs.MUTED, va="center", ha="left")

    cs.title(ax, "Every spec-touching PR in the corpus is merged",
             f"is_merged for the {cs.fmt_int(total)} pull requests that touch a spec file")

    cs.source_note(
        fig,
        "Rejection by a human reviewer is never observed, so the review question (Q3) "
        "cannot be asked of this data; the traceability question (M3 to M8) can.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
