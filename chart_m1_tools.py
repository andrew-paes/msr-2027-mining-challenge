"""Generate the M1 tool-composition chart: OpenSpec dominates the full census.

Usage:
    python chart_m1_tools.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import duckdb

from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m1_tools.png"
FULL = Path(SPECMINE_DATA)


def main():
    conn = duckdb.connect(":memory:")
    df = conn.execute(
        f"SELECT spec_tool, COUNT(*) AS n FROM read_parquet('{FULL}/spec_files.parquet') "
        "GROUP BY spec_tool ORDER BY n DESC"
    ).df()
    conn.close()

    total = int(df["n"].sum())
    df["pct"] = df["n"] / total * 100
    df = df.sort_values("n")  # ascending so the largest bar sits at the top

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["#d62728" if t == "openspec" else "#1f77b4" for t in df["spec_tool"]]
    bars = ax.barh(df["spec_tool"], df["n"], color=colors, edgecolor="white")
    for b, (_, row) in zip(bars, df.iterrows()):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2,
                f"  {row['n']:,} ({row['pct']:.1f}%)", va="center", fontsize=7)
    ax.set_xlabel("spec files (full v1.0)")
    ax.set_title("spec_tool composition (full): OpenSpec dominates at 58.4%")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
