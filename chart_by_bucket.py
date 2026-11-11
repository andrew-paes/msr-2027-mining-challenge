"""Generate the clone-classify stacked-bar chart (never/deleted by maturity).

Writes ``data/chart_by_bucket.png`` — a 100% stacked bar of the classification
outcomes by star bucket, so the maturity inversion (R3) is visible at a glance:
churn dominates immature repositories, non-implementation dominates mature ones.

Usage:
    python chart_by_bucket.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import chart_style as cs

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "data" / "classification_results.csv"
OUT_PNG = HERE / "data" / "chart_by_bucket.png"

BUCKETS = ["0-9", "10-99", "100+"]
MIN_LABEL_SHARE = 8.0  # label a segment only when it is wide enough to hold text


def main():
    cs.apply_style()

    df = pd.read_csv(RESULTS)
    cross = pd.crosstab(df["star_bucket"], df["classification"]).reindex(BUCKETS)
    totals = cross.sum(axis=1)
    share = cross.div(totals, axis=0) * 100

    observed = [key for key, *_ in cs.CLASSES if key in cross.columns]
    x = np.arange(len(BUCKETS))

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    bottom = np.zeros(len(BUCKETS))
    for key in observed:
        values = share[key].fillna(0).to_numpy()
        bars = ax.bar(x, values, 0.56, bottom=bottom, color=cs.CLASS_COLOR[key],
                      edgecolor=cs.INK, linewidth=0.8,
                      hatch=cs.CLASS_HATCH[key] or None)
        for xi, value, base in zip(x, values, bottom):
            if value >= MIN_LABEL_SHARE:
                ax.text(xi, base + value / 2, f"{value:.0f}%", ha="center",
                        va="center", fontsize=9.5, color=cs.INK,
                        bbox=dict(facecolor="white", edgecolor="none", pad=1.2,
                                  alpha=0.85))
        bottom += values

    for xi, total in zip(x, totals):
        ax.text(xi, 101.5, f"n = {cs.fmt_int(total)}", ha="center", va="bottom",
                fontsize=9.5, color=cs.INK)
    ax.set_ylim(0, 110)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    cs.pct_axis(ax, "y", 0)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{bucket} stars" for bucket in BUCKETS])
    ax.set_ylabel("share of the bucket's references")
    ax.grid(False, axis="x")

    cs.legend(
        ax,
        [(cs.CLASS_LABEL[key], cs.CLASS_COLOR[key], cs.CLASS_HATCH[key])
         for key in observed],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=2,
        columnspacing=1.4,
    )
    cs.title(
        ax,
        "Churn gives way to non-implementation as repositories mature",
        "classification of the sampled references in each repository star bucket; "
        f"segments above {MIN_LABEL_SHARE:.0f}% are labelled",
        width=62,
    )

    cs.source_note(
        fig,
        "The never share rises with maturity while deleted-before-anchor falls: in "
        "0-star repositories the references were written and then removed, in 100+ star "
        "repositories most were never written at all. Counts are sample estimates (the "
        "100+ bucket is a census).",
        y=-0.02,
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
