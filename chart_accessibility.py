"""Generate the accessibility chart: verifiable share by spec tool."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_accessibility.png"
A11Y = HERE / "data" / "accessibility_requirements.csv"


def main():
    df = pd.read_csv(A11Y)
    g = df.groupby("spec_tool")["verifiable"].agg(["count", "mean"]).reset_index()
    g = g[g["count"] >= 500].sort_values("mean", ascending=False)
    g["mean_pct"] = g["mean"] * 100

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = ["#1f77b4" if t in ("openspec", "speckit") else "#7f7f7f" for t in g["spec_tool"]]
    ax.barh(g["spec_tool"], g["mean_pct"], color=colors, edgecolor="white")
    ax.set_xlabel("% of accessibility requirement lines that are verifiable")
    ax.set_title("Verifiable accessibility requirements by spec tool")
    for i, (_, r) in enumerate(g.iterrows()):
        ax.text(r["mean_pct"], i, f"  {r['mean_pct']:.1f}%  (n={r['count']:,})", va="center")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
