"""Generate the M0 tool-composition chart: the sample is dominated by one tool.

Usage:
    python chart_m0_tools.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd

import chart_style as cs
from db import SAMPLE_SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m0_tools.png"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)
SHARE_CUT = 1.0  # tools below 1% of the files are grouped into one bar


def main():
    cs.apply_style()

    conn = duckdb.connect(":memory:")
    df = conn.execute(
        f"SELECT spec_tool, COUNT(*) AS n FROM read_parquet('{SAMPLE.as_posix()}/spec_files.parquet') "
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

    fig, ax = plt.subplots(figsize=(7.8, 4.2))
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
    ax.set_xlabel("spec files in the sample")

    entries = [("OpenSpec — the only tool with task-done and anchor marking",
                cs.VERMILLION, "///")]
    if (~is_openspec & ~is_other_group).any():
        entries.append(("other named tools", cs.BLUE, ""))
    if is_other_group.any():
        entries.append((f"tools under {SHARE_CUT:.0f}% each", cs.SLATE, ""))
    cs.legend(ax, entries, loc="lower right")

    cs.title(
        ax,
        "One tool dominates the sample",
        f"spec files per spec tool; tools under {SHARE_CUT:.0f}% of the files are "
        f"grouped (n = {cs.fmt_int(total)} files)",
    )

    cs.source_note(
        fig,
        f"The sample is {openspec_pct:.0f}% OpenSpec because OpenSpec is the only tool in "
        "the corpus that records, per task, whether it was checked off and which commit "
        "is the anchor — the two fields the traceability question needs.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
