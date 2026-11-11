"""Generate the accessibility chart: verifiable share by spec tool.

Usage:
    python chart_accessibility.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

import chart_style as cs

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_accessibility.png"
A11Y = HERE / "data" / "accessibility_requirements.csv"
MIN_LINES = 500  # tools below this are too thin to show individually
FORMAL = ("openspec", "speckit")


def main():
    cs.apply_style()

    df = pd.read_csv(A11Y)
    grouped = df.groupby("spec_tool")["verifiable"].agg(["count", "mean"]).reset_index()
    grouped = grouped[grouped["count"] >= MIN_LINES].sort_values("mean")
    grouped["mean_pct"] = grouped["mean"] * 100

    total_lines = len(df)
    total_repos = df["repo_name"].nunique()
    overall = df["verifiable"].mean() * 100
    omitted = df["spec_tool"].nunique() - len(grouped)
    is_formal = grouped["spec_tool"].isin(FORMAL)

    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    bars = ax.barh(grouped["spec_tool"], grouped["mean_pct"],
                   color=[cs.VERMILLION if flag else cs.BLUE for flag in is_formal],
                   edgecolor=cs.INK, linewidth=0.8, height=0.62)
    for bar, flag in zip(bars, is_formal):
        if flag:
            bar.set_hatch("///")

    cs.hlabel(
        ax, bars,
        [f"{pct:.1f}%  (n = {cs.fmt_int(n)} lines)"
         for pct, n in zip(grouped["mean_pct"], grouped["count"])],
        fontsize=9.5,
        backdrop=True,  # the overall reference line crosses the label column
    )
    cs.pct_axis(ax, "x", 0)
    cs.hgrid(ax)
    ax.set_xlabel("accessibility requirement lines that are verifiable")

    cs.legend(
        ax,
        [("formal spec tool (openspec, speckit)", cs.VERMILLION, "///"),
         ("informal or embedded spec", cs.BLUE, "")],
        loc="lower right",
    )
    cs.title(
        ax,
        "Formal spec tools write testable accessibility requirements",
        "share of requirement lines that are verifiable, by spec tool; the dotted line "
        f"marks the overall {overall:.1f}% (n = {cs.fmt_int(total_lines)} lines in "
        f"{cs.fmt_int(total_repos)} repositories)",
        width=76,
    )

    ax.axvline(overall, color=cs.INK, ls=":", lw=1.4)

    cs.source_note(
        fig,
        f"Tools with fewer than {MIN_LINES} lines are omitted ({omitted} tools). "
        "A line counts as verifiable when it carries a mandatory verb (shall, must) or "
        "a measurable threshold (a number, a ratio, or a WCAG A/AA/AAA level).",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
