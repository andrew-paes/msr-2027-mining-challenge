"""Generate the M1 chart: the sample is thin for specs, near-complete for PRs.

Usage:
    python chart_m1.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt

import chart_style as cs
from db import SAMPLE_SPECMINE_DATA, SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m1_sample_full.png"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)
FULL = Path(SPECMINE_DATA)

TABLES = ["spec_files", "openspec_code_refs", "spec_links", "pull_requests"]


def count(conn, dirpath, table):
    return conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{dirpath}/{table}.parquet')"
    ).fetchone()[0]


def main():
    cs.apply_style()

    conn = duckdb.connect(":memory:")
    rows = []
    for table in TABLES:
        n_sample = count(conn, SAMPLE.as_posix(), table)
        n_full = count(conn, FULL.as_posix(), table)
        rows.append((table, n_sample, n_full, n_sample / n_full * 100))
    conn.close()

    names = [cs.word(row[0]) for row in rows]
    pcts = [row[3] for row in rows]
    is_pr = [row[0] == "pull_requests" for row in rows]
    colors = [cs.VERMILLION if pr else cs.BLUE for pr in is_pr]
    hatches = ["///" if pr else "" for pr in is_pr]

    fig, ax = plt.subplots(figsize=(7.8, 3.1))
    bars = ax.barh(names, pcts, color=colors, edgecolor=cs.INK, linewidth=0.8,
                   height=0.5)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    cs.hlabel(ax, bars, [f"{pct:.1f}%" for pct in pcts], fontsize=10)
    cs.pct_axis(ax, "x", 0)
    cs.hgrid(ax)
    ax.invert_yaxis()  # keep the table order (specs first) reading top to bottom
    ax.set_xlabel("share of the full dataset")

    cs.legend(
        ax,
        [("pull-request layer (near-complete)", cs.VERMILLION, "///"),
         ("spec layer (thin sample)", cs.BLUE, "")],
        loc="upper right",
    )
    cs.title(ax, "The sample is thin for specs but covers the pull-request layer",
             "each row is the sample table as a share of the same table in the full dataset")

    cs.source_note(
        fig,
        "; ".join(f"{cs.word(t)} {cs.fmt_int(s)} of {cs.fmt_int(f)}"
                   for t, s, f, _ in rows)
        + ". The sample cannot carry a census of the spec layer, but the pull-request "
        "layer is usable as-is.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
