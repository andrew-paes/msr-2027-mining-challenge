"""Generate the census chart: done-but-missing references at scale."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import duckdb

import db

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_census.png"
REF = Path(db.SPECMINE_DATA) / "openspec_code_refs.parquet"

LABELS = {0: "absent (done but missing)", 1: "present", 2: "ambiguous"}
COLORS = {"absent (done but missing)": "#d62728", "present": "#1f77b4", "ambiguous": "#7f7f7f"}


def main():
    conn = duckdb.connect()
    rows = conn.execute(f"""
        SELECT exists_at_anchor, COUNT(*) AS n
        FROM read_parquet('{REF.as_posix()}')
        WHERE task_done = 1 AND anchor_sha IS NOT NULL
        GROUP BY 1
    """).fetchall()
    conn.close()

    data = sorted(((LABELS.get(r[0], str(r[0])), r[1]) for r in rows), key=lambda x: -x[1])
    names = [d[0] for d in data]
    vals = [d[1] for d in data]
    total = sum(vals)

    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.barh(names, vals, color=[COLORS[n] for n in names], edgecolor="white")
    ax.set_xlabel("references (task_done = 1, with an anchor)")
    ax.set_title("Done tasks: code present vs absent at the anchor commit")
    for b, v in zip(bars, vals):
        ax.text(v, b.get_y() + b.get_height() / 2,
                f"  {v:,} ({v / total * 100:.1f}%)", va="center")
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
