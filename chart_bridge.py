"""Generate the bridge chart: never rate, with vs without accessibility, by maturity.

Usage:
    python chart_bridge.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import chart_style as cs

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_bridge.png"
A11Y = HERE / "data" / "accessibility_requirements.csv"
RES = HERE / "data" / "classification_results.csv"

BUCKETS = ["0-9", "10-99", "100+"]


def main():
    cs.apply_style()

    a11y_repos = set(pd.read_csv(A11Y, usecols=["repo_name"]).repo_name)
    res = pd.read_csv(RES)
    res["has_a11y"] = res.repo_name.isin(a11y_repos)

    never_rate = res.groupby(["star_bucket", "has_a11y"])["classification"].apply(
        lambda s: (s == "never").mean()).unstack() * 100
    never_rate = never_rate.reindex(BUCKETS)

    x = np.arange(len(BUCKETS))
    width = 0.36

    fig, ax = plt.subplots(figsize=(8.2, 3.7))
    bars_no = ax.bar(x - width / 2, never_rate[False], width,
                     color=cs.BLUE, edgecolor=cs.INK, linewidth=0.8)
    bars_yes = ax.bar(x + width / 2, never_rate[True], width,
                      color=cs.VERMILLION, edgecolor=cs.INK, linewidth=0.8,
                      hatch="///")

    cs.vlabel(ax, bars_no, [f"{v:.1f}%" for v in never_rate[False]], fontsize=9.5)
    cs.vlabel(ax, bars_yes, [f"{v:.1f}%" for v in never_rate[True]], fontsize=9.5)
    cs.pct_axis(ax, "y", 0)
    ax.set_ylim(0, 82)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{bucket} stars" for bucket in BUCKETS])
    ax.set_ylabel("never rate among the missing references")
    ax.set_xlabel("repository star bucket (maturity)")

    cs.legend(
        ax,
        [("without accessibility requirements", cs.BLUE, ""),
         ("with accessibility requirements", cs.VERMILLION, "///")],
        loc="upper left",
        ncol=1,
    )
    cs.title(
        ax,
        "Accessibility requirements go with more missing code",
        "share of the done-but-missing references classified as never, by star bucket "
        "and by whether the repository states accessibility requirements",
        width=76,
    )

    gap = never_rate[True] - never_rate[False]
    cs.source_note(
        fig,
        "The accessibility group is higher in every bucket (by "
        f"{gap.min():.1f} to {gap.max():.1f} percentage points), but this is an "
        "association in a sample: repositories that write accessibility requirements "
        "aspire more than they implement, or they are simply the ones that write "
        "requirements at all. Nothing here is causal.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
