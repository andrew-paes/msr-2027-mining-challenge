"""Generate the clone-classify overall-outcome chart (the "84% genuinely absent" view).

Writes ``data/chart_outcomes.png`` — a horizontal bar of the classification
distribution across all sampled refs, highlighting "genuinely absent"
(never + deleted_before_anchor) so the 84% is visible at a glance.

Usage:
    python chart_outcomes.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "data" / "classification_results.csv"
OUT_PNG = HERE / "data" / "chart_outcomes.png"

ORDER = ["never", "deleted_before_anchor", "created_later",
         "renamed", "alternative_path", "other"]
COLORS = {
    "never": "#d62728",
    "deleted_before_anchor": "#ff7f0e",
    "created_later": "#1f77b4",
    "renamed": "#2ca02c",
    "alternative_path": "#9467bd",
    "other": "#7f7f7f",
}
LABELS = {
    "never": "never (never committed)",
    "deleted_before_anchor": "deleted before anchor",
    "created_later": "created later",
    "renamed": "renamed",
    "alternative_path": "alternative path",
    "other": "other",
}


def main():
    df = pd.read_csv(RESULTS)
    counts = df["classification"].value_counts()
    total = counts.sum()

    # only categories actually observed (alternative_path may be 0)
    order = [k for k in ORDER if k in counts.index]
    # reverse so the largest (never) is drawn at the top
    names = [LABELS[k] for k in order[::-1]]
    vals = [counts[k] / total * 100 for k in order[::-1]]
    colors = [COLORS[k] for k in order[::-1]]

    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    bars = ax.barh(names, vals, color=colors, edgecolor="white")
    ax.set_xlabel("%% of 'done but missing' references (n = %d)" % total)
    ax.set_title("Outcome of 'done but missing' references (overall)")
    for b, v in zip(bars, vals):
        ax.text(v + 0.5, b.get_y() + b.get_height() / 2, f"{v:.1f}%", va="center")

    absent = (counts.get("never", 0) + counts.get("deleted_before_anchor", 0)) / total * 100
    ax.text(0.98, 0.02, f"{absent:.1f}% genuinely absent\n(never + deleted)",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=9, color="#333333")
    ax.set_xlim(0, 65)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
