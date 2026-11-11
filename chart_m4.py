"""Generate the M4 chart: exists_at_anchor is not binary, and the absent
references decompose into done vs not-done.

Usage:
    python chart_m4.py
"""
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt

import chart_style as cs
from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m4_discovery.png"
FULL = Path(SPECMINE_DATA)

LABELS = {0: "0 (absent)", 1: "1 (present)", 2: "2 (ambiguous)", None: "NULL"}


def share(value: float, total: float) -> str:
    """Percentage with a second decimal for the classes too small to round."""
    pct = value / total * 100
    return f"{pct:.2f}%" if pct < 0.1 else f"{pct:.1f}%"


def main():
    cs.apply_style()

    conn = duckdb.connect(":memory:")
    refs = f"read_parquet('{FULL.as_posix()}/openspec_code_refs.parquet')"
    rows = conn.execute(
        f"SELECT exists_at_anchor, COUNT(*) FROM {refs} GROUP BY 1"
    ).fetchall()
    absent_done = conn.execute(
        f"SELECT COUNT(*) FROM {refs} WHERE exists_at_anchor = 0 AND task_done = 1"
    ).fetchone()[0]
    absent_not_done = conn.execute(
        f"SELECT COUNT(*) FROM {refs} WHERE exists_at_anchor = 0 AND task_done = 0"
    ).fetchone()[0]
    null_done = conn.execute(
        f"SELECT COUNT(*) FROM {refs} WHERE exists_at_anchor IS NULL AND task_done = 1"
    ).fetchone()[0]
    conn.close()

    counts = {key: n for key, n in rows}
    total = sum(counts.values())

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.6))

    # left: exists_at_anchor is not binary (NULL <=> anchor_sha NULL)
    order = [1, 0, None, 2]  # display order, largest at the top
    names = [LABELS[key] for key in reversed(order)]
    values = [counts.get(key, 0) for key in reversed(order)]
    is_null = [key is None for key in reversed(order)]

    bars = ax.barh(names, values,
                   color=[cs.VERMILLION if flag else cs.BLUE for flag in is_null],
                   edgecolor=cs.INK, linewidth=0.8, height=0.62)
    for bar, flag in zip(bars, is_null):
        if flag:
            bar.set_hatch("///")
    cs.hlabel(ax, bars, [f"{cs.fmt_int(v)}  ({share(v, total)})" for v in values],
              fontsize=9.5)
    cs.int_axis(ax, "x")
    cs.hgrid(ax)
    ax.set_xlabel("code references")
    cs.title(ax, "Four values, not two",
             f"exists_at_anchor over the whole corpus; NULL happens exactly when "
             "anchor_sha is NULL", width=46)

    # right: the absent refs decompose into done vs not-done
    labels2 = ["done", "not done"]
    values2 = [absent_done, absent_not_done]
    colors2 = [cs.VERMILLION, cs.SLATE]
    bars2 = ax2.barh(labels2, values2, color=colors2, edgecolor=cs.INK,
                     linewidth=0.8, height=0.42)
    cs.hlabel(ax2, bars2, [f"{cs.fmt_int(v)}" for v in values2], fontsize=9.5)
    cs.int_axis(ax2, "x")
    ax2.locator_params(axis="x", nbins=4)  # a narrow panel cannot hold 8 ticks
    cs.hgrid(ax2)
    ax2.set_xlabel("references with exists_at_anchor = 0")
    cs.title(ax2, "The absent references split in two",
             f"the {cs.fmt_int(absent_done + absent_not_done)} absent references, by "
             "whether the task was marked done (task_done = 1 vs 0)", width=46)

    cs.source_note(
        fig,
        f"Only the done half is a traceability gap: {cs.fmt_int(absent_done)} tasks are "
        f"checked off with no code at the anchor. Of the {cs.fmt_int(counts.get(None, 0))} "
        f"NULL references, {cs.fmt_int(null_done)} are task_done = 1 — done tasks with no "
        "anchor at all. The column is under-documented in the corpus, which is itself a "
        "data-quality finding.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
