"""Generate the M4 chart: exists_at_anchor is not binary (0/1/2/NULL).

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
    conn.close()

    data = sorted(
        ((LABELS.get(r[0], "NULL"), r[1]) for r in rows),
        key=lambda x: -x[1],
    )
    names = [d[0] for d in data]
    vals = [d[1] for d in data]

    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.barh(names, vals, color="#1f77b4", edgecolor="white")
    ax.set_xlabel("references")
    ax.set_title("exists_at_anchor is not binary (NULL <=> anchor_sha NULL)")
    for b, v in zip(bars, vals):
        ax.text(v, b.get_y() + b.get_height() / 2, f"  {v:,}", va="center")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
