"""Generate the M0 chart: the SpecMine sample is strongly right-skewed.

Usage:
    python chart_m0.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

import chart_style as cs
from db import SAMPLE_SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m0_sample.png"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)


def main():
    cs.apply_style()

    conn = duckdb.connect(":memory:")
    n_lines = conn.execute(
        f"SELECT n_lines FROM read_parquet('{SAMPLE.as_posix()}/spec_content_features.parquet') "
        "WHERE n_lines IS NOT NULL"
    ).df()["n_lines"]
    conn.close()

    total = len(n_lines)
    skew_val = float(stats.skew(n_lines))
    mean_val = float(n_lines.mean())
    median_val = float(n_lines.median())
    clip = float(n_lines.quantile(0.99))
    above = int((n_lines > clip).sum())

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(9.8, 3.6))

    # left: n_lines histogram, clipped to show the bulk (the tail is extreme)
    ax.hist(n_lines.clip(upper=clip), bins=60, color=cs.BLUE, edgecolor="white",
            linewidth=0.4)
    ax.axvline(mean_val, color=cs.VERMILLION, ls="--", lw=1.6,
               label=f"mean {mean_val:.0f} lines")
    ax.axvline(median_val, color=cs.INK, ls=":", lw=1.6,
               label=f"median {median_val:.0f} lines")
    ax.legend(loc="upper right", labelcolor=cs.INK)
    ax.set_xlabel("spec length in lines (clipped at the 99th percentile)")
    ax.set_ylabel("specs")
    cs.title(ax, "The bulk sits below 100 lines",
             "60 bins, clipped at the 99th percentile so the bulk is visible",
             width=44)

    # right: Q-Q plot against the normal — the tail curves off the diagonal
    (osm, osr), (slope, intercept, _r) = stats.probplot(n_lines.to_numpy(), dist="norm")
    ax2.scatter(osm, osr, s=6, color=cs.BLUE, alpha=0.55, edgecolor="white",
                linewidth=0.2, label="one spec")
    xs = np.array([osm.min(), osm.max()])
    ax2.plot(xs, slope * xs + intercept, color=cs.INK, ls="--", lw=1.4,
             label="normal reference")
    ax2.legend(loc="upper left", labelcolor=cs.INK)
    ax2.set_xlabel("theoretical quantiles of a normal distribution")
    ax2.set_ylabel("spec length, ordered")
    cs.title(ax2, "The tail leaves the diagonal at once",
             "a normal distribution would follow the dashed line; this one does not",
             width=44)

    cs.source_note(
        fig,
        f"Sample v1.1: n = {cs.fmt_int(total)} specs; skew {skew_val:.1f}, mean "
        f"{mean_val:.0f}, median {median_val:.0f}, maximum {cs.fmt_int(n_lines.max())} "
        f"lines. The {cs.fmt_int(above)} specs above the 99th percentile "
        f"({clip:.0f} lines) are clipped for display only. Right skew this strong is why "
        "every comparison that follows uses non-parametric tests.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
