"""Generate the M2 chart: every spec-touching PR is merged (Q3 unanswerable).

Usage:
    python chart_m2.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import duckdb

from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m2_pivot.png"
FULL = Path(SPECMINE_DATA)


def main():
    conn = duckdb.connect(":memory:")
    rows = conn.execute(
        f"SELECT is_merged, COUNT(*) FROM read_parquet('{FULL}/pull_requests.parquet') "
        "GROUP BY 1 ORDER BY 1"
    ).fetchall()
    conn.close()

    counts = {r[0]: r[1] for r in rows}
    merged = counts.get(1, 0)
    rejected = counts.get(0, 0)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(["merged (1)", "rejected (0)"], [merged, rejected],
           color=["#1f77b4", "#d62728"], edgecolor="white")
    ax.set_ylabel("spec-touching PRs")
    ax.set_title("Every PR is merged -> the review question (Q3) is unanswerable")
    for i, v in enumerate([merged, rejected]):
        ax.text(i, v + max(merged, rejected) * 0.02, f"{v:,}", ha="center")
    ax.set_ylim(0, merged * 1.18)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
