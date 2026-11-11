"""Generate the M4 chart: exists_at_anchor is not binary (0/1/2/NULL), and the
absent refs decompose into done vs not-done.

Usage:
    python chart_m4.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import duckdb

from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m4_discovery.png"
FULL = Path(SPECMINE_DATA)

LABELS = {0: "0 (absent)", 1: "1 (present)", 2: "2 (ambiguous)"}


def main():
    conn = duckdb.connect(":memory:")
    rows = conn.execute(
        f"SELECT exists_at_anchor, COUNT(*) FROM read_parquet('{FULL}/openspec_code_refs.parquet') "
        "GROUP BY 1 ORDER BY 1"
    ).fetchall()

    absent_done = conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{FULL}/openspec_code_refs.parquet') "
        "WHERE exists_at_anchor = 0 AND task_done = 1"
    ).fetchone()[0]
    absent_not_done = conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{FULL}/openspec_code_refs.parquet') "
        "WHERE exists_at_anchor = 0 AND task_done = 0"
    ).fetchone()[0]
    conn.close()

    data = sorted(
        ((LABELS.get(r[0], "NULL"), r[1]) for r in rows),
        key=lambda x: -x[1],
    )
    names = [d[0] for d in data]
    vals = [d[1] for d in data]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 3.2))

    # left: exists_at_anchor is not binary
    bars = ax.barh(names, vals, color="#1f77b4", edgecolor="white")
    ax.set_xlabel("references")
    ax.set_title("exists_at_anchor is not binary (NULL <=> anchor_sha NULL)")
    for b, v in zip(bars, vals):
        ax.text(v, b.get_y() + b.get_height() / 2, f"  {v:,}", va="center")
    ax.text(0.5, -0.22, "of the NULL (22,209): 8,746 are task_done=1 (done without an anchor)",
            transform=ax.transAxes, ha="center", fontsize=8, color="#555555")

    # right: the absent refs decompose into done vs not-done
    labels2 = ["done (task_done=1)", "not done (task_done=0)"]
    vals2 = [absent_done, absent_not_done]
    colors2 = ["#d62728", "#7f7f7f"]
    bars2 = ax2.bar(labels2, vals2, color=colors2, edgecolor="white")
    ax2.set_ylabel("references (exists_at_anchor = 0)")
    ax2.set_title("Absent refs: done vs not done")
    for b, v in zip(bars2, vals2):
        ax2.text(b.get_x() + b.get_width() / 2, v + 1500, f"{v:,}", ha="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
