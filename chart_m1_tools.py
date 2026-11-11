"""Generate the M1 tool-composition chart: the full corpus is equally dominated.

Usage:
    python chart_m1_tools.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd

import chart_style as cs
from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m1_tools.png"
FULL = Path(SPECMINE_DATA)
SHARE_CUT = 1.0  # tools below 1% of the files are grouped into one bar


def main():
    cs.apply_style()

    conn = duckdb.connect(":memory:")
    df = conn.execute(
        f"SELECT spec_tool, COUNT(*) AS n FROM read_parquet('{FULL.as_posix()}/spec_files.parquet') "
        "GROUP BY spec_tool ORDER BY n DESC"
    ).df()
    conn.close()

    total = int(df["n"].sum())
    keep = df[df["n"] / total * 100 >= SHARE_CUT].copy()
    tail = df[df["n"] / total * 100 < SHARE_CUT]
    if len(tail):
        keep = pd.concat(
            [keep, pd.DataFrame([{"spec_tool": f"other tools (n = {len(tail)})",
                                  "n": int(tail["n"].sum())}])],
            ignore_index=True,
        )
    keep["pct"] = keep["n"] / total * 100
    openspec_pct = float(keep.loc[keep["spec_tool"].eq("openspec"), "pct"].sum())
    keep = keep.sort_values("n")  # ascending: the largest bar ends up on top

    is_openspec = keep["spec_tool"].eq("openspec")
    is_other_group = keep["spec_tool"].str.startswith("other tools")
    colors = [
        cs.VERMILLION if flag else cs.SLATE if tail_flag else cs.BLUE
        for flag, tail_flag in zip(is_openspec, is_other_group)
    ]
    hatches = ["///" if flag else "" for flag in is_openspec]

    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    bars = ax.barh(keep["spec_tool"], keep["n"], color=colors, edgecolor=cs.INK,
                   linewidth=0.8, height=0.62)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    cs.hlabel(
        ax, bars,
        [f"{cs.fmt_int(n)}  ({pct:.1f}%)" for n, pct in zip(keep["n"], keep["pct"])],
        fontsize=9.5,
    )
    cs.int_axis(ax, "x")
    cs.hgrid(ax)
    ax.set_xlabel("spec files in the full dataset")

    entries = [("OpenSpec — majority of the corpus", cs.VERMILLION, "///")]
    if (~is_openspec & ~is_other_group).any():
        entries.append(("other named tools", cs.BLUE, ""))
    if is_other_group.any():
        entries.append((f"tools under {SHARE_CUT:.0f}% each", cs.SLATE, ""))
    cs.legend(ax, entries, loc="lower right")

    cs.title(
        ax,
        "One tool dominates the full corpus as well",
        f"spec files per spec tool; tools under {SHARE_CUT:.0f}% of the files are "
        f"grouped (n = {cs.fmt_int(total)} files)",
    )

    cs.source_note(
        fig,
        f"OpenSpec holds {openspec_pct:.1f}% of the full census, so the sample's "
        "over-representation of the tool (M0) is a matter of degree, not of kind — "
        "and the task-traceability question can only be asked of OpenSpec files.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
