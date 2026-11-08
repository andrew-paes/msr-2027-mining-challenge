"""Generate the taxonomy chart: three-level split of the 34,227 missing refs."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_taxonomy.png"
TAX = HERE / "data" / "taxonomy_e0.csv"

LABELS = {"clean_path": "clean path (relative_ext)",
          "bare_filename": "bare filename (bare_ext)",
          "non_file": "non-file (glob/absolute/no-ext)"}
COLORS = {"clean path (relative_ext)": "#1f77b4",
          "bare filename (bare_ext)": "#ff7f0e",
          "non-file (glob/absolute/no-ext)": "#7f7f7f"}


def main():
    df = pd.read_csv(TAX)
    counts = df["level"].value_counts().reindex(["clean_path", "bare_filename", "non_file"]).fillna(0).astype(int)
    names = [LABELS[k] for k in counts.index]
    vals = counts.values
    total = sum(vals)

    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.barh(names, vals, color=[COLORS[n] for n in names], edgecolor="white")
    ax.set_xlabel("references (done but missing, n = %d)" % total)
    ax.set_title("Taxonomy: real file references vs path noise")
    for b, v in zip(bars, vals):
        ax.text(v, b.get_y() + b.get_height() / 2,
                f"  {v:,} ({v / total * 100:.1f}%)", va="center")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
