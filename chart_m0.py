"""Generate the M0 chart: the SpecMine sample is strongly right-skewed.

Usage:
    python chart_m0.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import duckdb

from db import SAMPLE_SPECMINE_DATA
from scipy import stats
import numpy as np

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m0_sample.png"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)


def main():
    conn = duckdb.connect(":memory:")
    n_lines = conn.execute(
        f"SELECT n_lines FROM read_parquet('{SAMPLE}/spec_content_features.parquet') "
        "WHERE n_lines IS NOT NULL"
    ).df()["n_lines"]
    conn.close()

    # skew on the full sample (same as m0_sample_stats.py).
    skew_val = float(stats.skew(n_lines))

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 3.2))

    # left: n_lines histogram, clipped to show the bulk (the tail is extreme)
    clip = float(n_lines.quantile(0.99))
    ax.hist(n_lines.clip(upper=clip), bins=60, color="#1f77b4", edgecolor="white")
    ax.axvline(float(n_lines.mean()), color="#d62728", ls="--", lw=1.5,
               label=f"mean {n_lines.mean():.0f}")
    ax.axvline(float(n_lines.median()), color="#ff7f0e", ls="--", lw=1.5,
               label=f"median {n_lines.median():.0f}")
    ax.set_title(f"n_lines is strongly right-skewed (skew {skew_val:.1f})")
    ax.set_xlabel("n_lines (clipped at 99th pct)")
    ax.set_ylabel("specs")
    ax.legend(fontsize=8)

    # right: Q-Q plot against the normal — the tail curves off the diagonal
    (osm, osr), (slope, intercept, _r) = stats.probplot(n_lines.to_numpy(), dist="norm")
    ax2.scatter(osm, osr, s=4, color="#1f77b4", alpha=0.4)
    xs = np.array([osm.min(), osm.max()])
    ax2.plot(xs, slope * xs + intercept, color="#d62728", ls="--", lw=1.5)
    ax2.set_title("Q-Q plot: the tail curves off the normal line")
    ax2.set_xlabel("theoretical quantiles (normal)")
    ax2.set_ylabel("ordered n_lines")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
