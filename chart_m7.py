"""Generate the M7 chart: which path shapes carry a real rename signal.

Usage:
    python chart_m7.py
"""
from collections import Counter
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt

import chart_style as cs
from db import SPECMINE_DATA
from taxonomy import classify_path

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_m7_calibration.png"
FULL = Path(SPECMINE_DATA)

# display order, top to bottom: the two shapes that can carry a real signal first
SHAPES = ["relative_ext", "glob", "bare_ext", "absolute"]
MEANING = {
    "relative_ext": "relative path",
    "glob": "glob pattern",
    "bare_ext": "bare filename",
    "absolute": "absolute path",
}


def main():
    cs.apply_style()

    conn = duckdb.connect(":memory:")
    rows = conn.execute(f"""
        SELECT code_path, resolved_path
        FROM read_parquet('{FULL.as_posix()}/openspec_code_refs.parquet')
        WHERE task_done = 1 AND anchor_sha IS NOT NULL
          AND exists_at_anchor = 1 AND resolved_path IS NOT NULL AND resolved_path != ''
    """).fetchall()
    conn.close()

    diff = Counter()
    total = Counter()
    for code_path, resolved_path in rows:
        _prefix, shape = classify_path(code_path)
        if shape in SHAPES:
            total[shape] += 1
            if resolved_path != code_path:
                diff[shape] += 1

    pcts = {s: (diff[s] / total[s] * 100 if total[s] else 0.0) for s in SHAPES}

    order = list(reversed(SHAPES))  # barh draws the first item at the bottom
    names = [MEANING[s] for s in order]
    values = [pcts[s] for s in order]
    colors = [
        cs.VERMILLION if s == "relative_ext" else cs.BLUE if s == "glob" else cs.SLATE
        for s in order
    ]
    hatches = ["///" if s == "relative_ext" else "" for s in order]

    fig, ax = plt.subplots(figsize=(8.2, 3.4))
    bars = ax.barh(names, values, color=colors, edgecolor=cs.INK, linewidth=0.8,
                   height=0.6)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    cs.hlabel(
        ax, bars,
        [f"{pcts[s]:.1f}%  (n = {cs.fmt_int(total[s])})" for s in order],
        fontsize=10,
    )
    cs.pct_axis(ax, "x", 0)
    cs.hgrid(ax)
    ax.set_xlim(0, 100)
    ax.set_xlabel("resolved references whose resolved path differs from the path as written")

    cs.title(
        ax,
        "Only the relative-path rate is a real rename signal",
        "share of resolved references whose resolved path differs from the path as "
        "written, by path shape; orange = the real signal, blue = the same signal over "
        "fewer references, grey = not comparable (the resolver rewrites the string)",
        width=82,
    )

    cs.source_note(
        fig,
        "For a bare filename or an absolute path the resolver rewrites the string by "
        "construction, so their rate measures the resolver rather than the repository. "
        f"The {pcts['relative_ext']:.1f}% of the relative paths is the burden the "
        "classification layer (M8) has to recover.",
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
