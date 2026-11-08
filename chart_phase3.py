"""Generate the Phase 3 stacked-bar chart (never/deleted by maturity).

Writes ``data/phase3_by_bucket.png`` — a stacked bar of the classification
outcomes by star bucket, with ``never`` (red) and ``deleted_before_anchor``
(orange) highlighted so the maturity inversion (R3) is visible at a glance.

Usage:
    python chart_phase3.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, no display needed
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "data" / "phase3_results.csv"
OUT_PNG = HERE / "data" / "phase3_by_bucket.png"

ORDER = ["never", "deleted_before_anchor", "created_later",
         "renamed", "alternative_path", "other"]

COLORS = {
    "never": "#d62728",                  # red
    "deleted_before_anchor": "#ff7f0e",  # orange
    "created_later": "#1f77b4",          # blue
    "renamed": "#2ca02c",                # green
    "alternative_path": "#9467bd",       # purple
    "other": "#7f7f7f",                  # grey
}


def main():
    df = pd.read_csv(RESULTS)

    bucket_refs = pd.crosstab(df["star_bucket"], df["classification"])
    bucket_refs = bucket_refs.reindex(columns=ORDER).fillna(0).astype(int)
    bucket_refs_pct = bucket_refs.div(bucket_refs.sum(axis=1), axis=0) * 100
    bucket_refs_pct = bucket_refs_pct.reindex(["0-9", "10-99", "100+"])

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bucket_refs_pct[ORDER].plot(
        kind="bar", stacked=True, ax=ax, edgecolor="white",
        color=[COLORS[c] for c in ORDER],
    )
    ax.set_ylabel("% of 'done but missing' references")
    ax.set_xlabel("Star bucket")
    ax.set_title("Outcome of 'done but missing' references by maturity")
    ax.legend(title="Classification", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
