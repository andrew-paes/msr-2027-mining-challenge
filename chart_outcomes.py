"""Generate the clone-classify overall-outcome chart (the genuinely-absent view).

Writes ``data/chart_outcomes.png`` — the classification distribution across all
sampled references, so "genuinely absent" (never + deleted_before_anchor) is
visible at a glance.

Usage:
    python chart_outcomes.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import chart_style as cs

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "data" / "classification_results.csv"
SAMPLE_FRAME = HERE / "data" / "classification_sample.csv"
OUT_PNG = HERE / "data" / "chart_outcomes.png"


def main():
    cs.apply_style()

    df = pd.read_csv(RESULTS)
    counts = df["classification"].value_counts()
    total = len(df)
    repos = df["repo_name"].nunique()
    drawn = len(pd.read_csv(SAMPLE_FRAME)) if SAMPLE_FRAME.exists() else None

    # only the classes actually observed, largest at the top
    observed = [key for key, *_ in cs.CLASSES if key in counts.index]
    order = list(reversed(observed))
    names = [cs.CLASS_LABEL[key] for key in order]
    values = [counts[key] / total * 100 for key in order]
    colors = [cs.CLASS_COLOR[key] for key in order]
    hatches = [cs.CLASS_HATCH[key] for key in order]

    fig, ax = plt.subplots(figsize=(8.0, 3.2))
    bars = ax.barh(names, values, color=colors, edgecolor=cs.INK, linewidth=0.8,
                   height=0.58)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    ax.set_xlim(0, 62)
    cs.hlabel(ax, bars, [f"{value:.1f}%" for value in values], fontsize=10)
    cs.pct_axis(ax, "x", 0)
    cs.hgrid(ax)
    ax.set_xlabel("share of the sampled done-but-missing references")

    absent = (counts.get("never", 0) + counts.get("deleted_before_anchor", 0))
    ax.text(0.985, 0.06,
            f"{absent / total * 100:.1f}% genuinely absent\n"
            "(never + deleted before anchor)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9.5,
            color=cs.INK)

    cs.title(ax, "Most of the missing were never implemented",
             f"classification of the {cs.fmt_int(total)} sampled references in {repos} "
             "repositories; the two absent classes carry a hatch texture",
             width=72)

    cs.source_note(
        fig,
        (f"The sample is {repos} of the {drawn} repositories drawn for clone-classify "
         f"({drawn - repos} could not be cloned), so these are sample estimates, not "
         "census counts"
         if drawn else
         f"The sample is {repos} classified repositories, so these are sample estimates")
        + "; the 100+ star bucket is exhaustive. All-branch classification makes "
        "'never' the conservative reading: an unmerged feature branch counts as "
        "implemented.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
