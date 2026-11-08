"""Generate the M1 chart: the sample is thin for specs, near-complete for PRs.

Usage:
    python chart_m1.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import duckdb

from db import SAMPLE_SPECMINE_DATA, SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m1_sample_full.png"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)
FULL = Path(SPECMINE_DATA)

TABLES = ["spec_files", "openspec_code_refs", "spec_links", "pull_requests"]


def count(conn, dirpath, table):
    return conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{dirpath}/{table}.parquet')"
    ).fetchone()[0]


def main():
    conn = duckdb.connect(":memory:")
    rows = []
    for t in TABLES:
        s = count(conn, SAMPLE, t)
        f = count(conn, FULL, t)
        rows.append((t, s / f * 100))
    conn.close()

    names = [r[0] for r in rows]
    pcts = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(7, 3.2))
    colors = ["#d62728" if n == "pull_requests" else "#1f77b4" for n in names]
    bars = ax.barh(names, pcts, color=colors, edgecolor="white")
    ax.set_xlabel("sample as % of full")
    ax.set_title("Sample vs full: thin for specs, near-complete for PRs")
    for b, v in zip(bars, pcts):
        ax.text(v, b.get_y() + b.get_height() / 2, f"  {v:.1f}%", va="center")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
