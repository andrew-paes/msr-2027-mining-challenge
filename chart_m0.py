"""Generate the M0 chart: the SpecMine sample is heavy-tailed and half-archived.

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

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m0_sample.png"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)


def main():
    conn = duckdb.connect(":memory:")
    n_lines = conn.execute(
        f"SELECT n_lines FROM read_parquet('{SAMPLE}/spec_content_features.parquet') "
        "WHERE n_lines IS NOT NULL"
    ).df()["n_lines"]
    roles = conn.execute(
        f"SELECT spec_role FROM read_parquet('{SAMPLE}/spec_files.parquet')"
    ).df()["spec_role"]
    conn.close()

    # skew on a 5,000-row subsample, exactly as m0_sample_stats.py does
    # (Shapiro-Wilk's n <= 5000 limit); the full-sample skew is a bit higher.
    subsample = n_lines if len(n_lines) <= 5000 else n_lines.sample(5000, random_state=0)
    skew_val = float(stats.skew(subsample))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.4))

    # left: n_lines histogram, clipped to show the bulk (the tail is extreme)
    clip = float(n_lines.quantile(0.99))
    ax1.hist(n_lines.clip(upper=clip), bins=60, color="#1f77b4", edgecolor="white")
    ax1.axvline(float(n_lines.mean()), color="#d62728", ls="--", lw=1.5,
                label=f"mean {n_lines.mean():.0f}")
    ax1.axvline(float(n_lines.median()), color="#ff7f0e", ls="--", lw=1.5,
                label=f"median {n_lines.median():.0f}")
    ax1.set_title(f"n_lines is heavy-tailed (skew {skew_val:.1f})")
    ax1.set_xlabel("n_lines (clipped at 99th pct)")
    ax1.set_ylabel("specs")
    ax1.legend(fontsize=8)

    # right: archived vs other (the ~51.5% finding)
    archived = float((roles == "archived").mean() * 100)
    ax2.bar(["archived", "other"], [archived, 100 - archived],
            color=["#d62728", "#7f7f7f"], edgecolor="white")
    ax2.set_title(f"spec_role: {archived:.1f}% archived")
    ax2.set_ylabel("% of specs")
    for i, v in enumerate([archived, 100 - archived]):
        ax2.text(i, v + 2, f"{v:.1f}%", ha="center")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
