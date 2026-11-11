"""Generate the M0 tool-composition chart: the sample is dominated by OpenSpec.

Usage:
    python chart_m0_tools.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import duckdb

from db import SAMPLE_SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m0_tools.png"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)


def main():
    conn = duckdb.connect(":memory:")
    df = conn.execute(
        f"SELECT spec_tool, COUNT(*) AS n FROM read_parquet('{SAMPLE}/spec_files.parquet') "
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
    ax.set_xlabel("spec files (sample v1.1)")
    ax.set_title("spec_tool composition (sample): OpenSpec dominates at 77.4%")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
