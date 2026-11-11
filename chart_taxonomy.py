"""Generate the taxonomy chart: three-level split of the missing references.

Usage:
    python chart_taxonomy.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import chart_style as cs

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_taxonomy.png"
TAX = HERE / "data" / "taxonomy_e0.csv"

ORDER = ["clean_path", "bare_filename", "non_file"]
LABELS = {
    "clean_path": "clean relative path",
    "bare_filename": "bare filename (basename only)",
    "non_file": "non-file (glob, absolute or no extension)",
}
BLUE_HATCH = {"clean_path": "", "bare_filename": "///", "non_file": ""}


def main():
    cs.apply_style()

    df = pd.read_csv(TAX)
    counts = df["level"].value_counts().reindex(ORDER).fillna(0).astype(int)
    total = int(counts.sum())

    # ascending so the largest bar ends up on top of the barh
    order = counts.sort_values().index
    names = [LABELS[key] for key in order]
    values = [int(counts[key]) for key in order]
    colors = [cs.SLATE if key == "non_file" else cs.BLUE for key in order]
    hatches = [BLUE_HATCH[key] for key in order]

    fig, ax = plt.subplots(figsize=(8.4, 3.4))
    bars = ax.barh(names, values, color=colors, edgecolor=cs.INK, linewidth=0.8,
                   height=0.6)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    cs.hlabel(ax, bars, [f"{cs.fmt_int(v)}  ({v / total * 100:.1f}%)" for v in values],
              fontsize=10)
    cs.int_axis(ax, "x")
    cs.hgrid(ax)
    ax.set_xlabel("done-but-missing references")

    cs.title(
        ax,
        "Almost all of the missing are real file references",
        f"taxonomy of the {cs.fmt_int(total)} done-but-missing references; blue = real "
        "file reference (hatched when only the basename is given), grey = not a file",
        width=78,
    )

    cs.source_note(
        fig,
        "The taxonomy is a pure function of each path string (taxonomy.classify_path, "
        "reused by M5 and M7 so the definition cannot drift). Only the non-file class is "
        "noise; the missing is a real absence of code, not malformed references.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
