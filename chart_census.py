"""Generate the census chart: done-but-missing references at scale, and where
the gap concentrates (by spec_role)."""
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import duckdb

import db
from taxonomy import classify_spec_role

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_census.png"
REF = Path(db.SPECMINE_DATA) / "openspec_code_refs.parquet"

LABELS = {0: "absent (done but missing)", 1: "present", 2: "ambiguous"}
COLORS = {"absent (done but missing)": "#d62728", "present": "#1f77b4", "ambiguous": "#7f7f7f"}
ROLE_COLORS = {"change_proposal": "#d62728", "archived": "#1f77b4"}


def main():
    conn = duckdb.connect()
    rows = conn.execute(f"""
        SELECT artifact_path, exists_at_anchor
        FROM read_parquet('{REF.as_posix()}')
        WHERE task_done = 1 AND anchor_sha IS NOT NULL
    """).fetchall()
    conn.close()

    by_status = defaultdict(int)
    by_role = defaultdict(lambda: [0, 0])  # role -> [refs, missing]
    for artifact_path, exists in rows:
        by_status[exists] += 1
        role = classify_spec_role(artifact_path)
        by_role[role][0] += 1
        if exists == 0:
            by_role[role][1] += 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.2))

    # left: present vs absent vs ambiguous
    data = sorted(((LABELS.get(s, str(s)), by_status[s]) for s in by_status), key=lambda x: -x[1])
    names = [d[0] for d in data]
    vals = [d[1] for d in data]
    total = sum(vals)
    bars = ax1.barh(names, vals, color=[COLORS[n] for n in names], edgecolor="white")
    ax1.set_xlabel("references (task_done = 1, with an anchor)")
    ax1.set_title("Done tasks: code present vs absent at the anchor commit")
    for b, v in zip(bars, vals):
        ax1.text(v, b.get_y() + b.get_height() / 2,
                 f"  {v:,} ({v / total * 100:.1f}%)", va="center")

    # right: missing rate by spec_role (the gap concentrates in change_proposal)
    roles = ["change_proposal", "archived"]
    pcts = [by_role[r][1] / by_role[r][0] * 100 for r in roles]
    bars2 = ax2.bar(roles, pcts, color=[ROLE_COLORS[r] for r in roles], edgecolor="white")
    ax2.axhline(10.3, color="#7f7f7f", ls="--", lw=1.5, label="overall 10.3%")
    ax2.set_ylabel("missing rate (%)")
    ax2.set_title("The gap concentrates in active change proposals")
    for b, v in zip(bars2, pcts):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.1f}%", ha="center")
    ax2.legend(fontsize=8)
    ax2.set_ylim(0, max(pcts) * 1.2)
    ax2.text(0.0, -0.30, "living: 0 refs — tasks.md lives only under openspec/changes/",
             transform=ax2.transAxes, fontsize=8, va="top", color="#555555")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
