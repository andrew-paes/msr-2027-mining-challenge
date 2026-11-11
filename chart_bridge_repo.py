"""Generate the repo-level bridge chart (box + jitter of never-rate by accessibility).

Writes ``data/chart_bridge_repo.png`` — the per-repository ``never`` rate distribution
for repositories with vs without accessibility requirements, with each repository drawn
as an individual point (the unit of the Mann-Whitney U comparison).

Usage:
    python chart_bridge_repo.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import chart_style as cs

HERE = Path(__file__).resolve().parent
RES = HERE / "data" / "classification_results.csv"
A11Y = HERE / "data" / "accessibility_requirements.csv"
OUT_PNG = HERE / "data" / "chart_bridge_repo.png"


def main():
    cs.apply_style()

    a11y_repos = set(pd.read_csv(A11Y, usecols=["repo_name"]).repo_name)
    res = pd.read_csv(RES)
    res["has_a11y"] = res.repo_name.isin(a11y_repos)

    per_repo = (
        res.groupby("repo_name")
        .agg(never_rate=("classification", lambda s: (s == "never").mean() * 100),
             has_a11y=("has_a11y", "first"))
        .reset_index()
    )

    without = per_repo[~per_repo.has_a11y]["never_rate"].to_numpy()
    with_a11y = per_repo[per_repo.has_a11y]["never_rate"].to_numpy()
    _u, p_value = stats.mannwhitneyu(without, with_a11y, alternative="two-sided")

    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    ax.boxplot(
        [without, with_a11y], positions=[0, 1], widths=0.42, patch_artist=True,
        showfliers=False,
        medianprops=dict(color=cs.INK, lw=2.2),
        boxprops=dict(facecolor="#ececec", edgecolor=cs.INK, linewidth=0.8),
        whiskerprops=dict(color=cs.INK),
        capprops=dict(color=cs.INK),
    )

    rng = np.random.default_rng(42)
    for position, values in zip([0, 1], [without, with_a11y]):
        jitter = rng.uniform(-0.13, 0.13, len(values))
        ax.scatter(position + jitter, values, s=18, alpha=0.6, color=cs.BLUE,
                   edgecolor="white", linewidth=0.4, zorder=3)

    ax.set_ylim(-6, 118)
    ax.set_xlim(-0.55, 1.55)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    cs.pct_axis(ax, "y", 0)
    ax.grid(False, axis="x")
    ax.set_xticks([0, 1])
    ax.set_xticklabels([
        f"without accessibility requirements\n(n = {len(without)} repositories)",
        f"with accessibility requirements\n(n = {len(with_a11y)} repositories)",
    ])
    ax.set_ylabel("never rate of the repository's missing references")

    for position, values in zip([0, 1], [without, with_a11y]):
        ax.text(position, 110, f"median {np.median(values):.1f}%", ha="center",
                va="center", fontsize=9.5, color=cs.INK)

    verdict = "not significant at 0.05" if p_value >= 0.05 else "significant at 0.05"
    cs.title(
        ax,
        "The repository is the unit of the comparison",
        f"per-repository never rate, with and without accessibility requirements "
        f"(Mann-Whitney U, two-sided, p = {p_value:.3f} — {verdict})",
        width=76,
    )

    cs.source_note(
        fig,
        "Each dot is one repository and the thick horizontal line is the group median; "
        "the two groups overlap heavily, which is why the difference is reported as "
        "descriptive rather than as an effect.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
