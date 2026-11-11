"""Generate the bridge chart: never rate, with vs without accessibility, by maturity."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_bridge.png"
A11Y = HERE / "data" / "accessibility_requirements.csv"
RES = HERE / "data" / "classification_results.csv"

BUCKETS = ["0-9", "10-99", "100+"]


def main():
    a11y = pd.read_csv(A11Y)
    res = pd.read_csv(RES)
    a11y_repos = set(a11y.repo_name)
    res["has_a11y"] = res.repo_name.isin(a11y_repos)

    never_rate = res.groupby(["star_bucket", "has_a11y"])["classification"].apply(
        lambda s: (s == "never").mean()).unstack() * 100
    never_rate = never_rate.reindex(BUCKETS)

    x = np.arange(len(BUCKETS))
    w = 0.38
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.bar(x - w / 2, never_rate[False], w, label="without accessibility", color="#1f77b4", edgecolor="white")
    ax.bar(x + w / 2, never_rate[True], w, label="with accessibility", color="#d62728", edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(BUCKETS)
    ax.set_xlabel("Star bucket")
    ax.set_ylabel("% of 'done but missing' refs that are 'never'")
    ax.set_title("Accessibility and non-implementation, by maturity")
    ax.legend()
    for i, b in enumerate(BUCKETS):
        ax.text(i - w / 2, never_rate.loc[b, False] + 0.5, f"{never_rate.loc[b, False]:.0f}%", ha="center")
        ax.text(i + w / 2, never_rate.loc[b, True] + 0.5, f"{never_rate.loc[b, True]:.0f}%", ha="center")
    ax.set_ylim(0, 75)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
