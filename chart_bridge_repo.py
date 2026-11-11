"""Generate the repo-level bridge chart (box + jitter of never-rate by accessibility).

Writes ``data/chart_bridge_repo.png`` — the per-repository ``never`` rate distribution
for repositories with vs without accessibility requirements, with each repository drawn
as an individual point (the unit of the Mann-Whitney U comparison).

Usage:
    python chart_bridge_repo.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "data" / "classification_results.csv"
A11Y = HERE / "data" / "accessibility_requirements.csv"
OUT_PNG = HERE / "data" / "chart_bridge_repo.png"


def main():
    res = pd.read_csv(RES)
    a11y_repos = set(pd.read_csv(A11Y).repo_name)
    res["has_a11y"] = res.repo_name.isin(a11y_repos)

    g = (
        res.groupby("repo_name")
        .agg(never_rate=("classification", lambda s: (s == "never").mean() * 100),
             has_a11y=("has_a11y", "first"))
        .reset_index()
    )

    without = g[~g.has_a11y]["never_rate"].to_numpy()
    with_a11y = g[g.has_a11y]["never_rate"].to_numpy()

    fig, ax = plt.subplots(figsize=(5.1, 3.5))
    groups = [without, with_a11y]
    labels = [f"without accessibility requirements\n(n = {len(without)})",
              f"with accessibility requirements\n(n = {len(with_a11y)})"]

    ax.boxplot(
        groups, positions=[0, 1], widths=0.4, patch_artist=True,
        showfliers=False,
        medianprops=dict(color="#d62728", lw=2),
        boxprops=dict(facecolor="#e8e8e8", edgecolor="#555555"),
        whiskerprops=dict(color="#555555"),
        capprops=dict(color="#555555"),
    )

    rng = np.random.default_rng(42)
    for pos, vals in zip([0, 1], groups):
        jitter = rng.uniform(-0.13, 0.13, len(vals))
        ax.scatter(pos + jitter, vals, s=16, alpha=0.55, color="#1f77b4",
                   edgecolor="white", linewidth=0.4, zorder=3)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels)
    ax.set_ylabel("% of 'done but missing' refs classified 'never' (per repository)")
    ax.set_title("Repository-level never rate by accessibility requirements\n(Mann-Whitney U, two-sided, p = 0.169)", fontsize=10)
    ax.set_ylim(-5, 110)

    ax.text(0, 106, f"median {np.median(without):.1f}%", ha="center", fontsize=9, color="#333333")
    ax.text(1, 106, f"median {np.median(with_a11y):.1f}%", ha="center", fontsize=9, color="#333333")
    ax.text(0.5, -0.18, "Each dot represents one repository; red horizontal lines indicate group medians.", transform=ax.transAxes, ha="center", va="top", fontsize=8, color="#555555")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
