"""Generate the census chart: the done-but-missing gap, its denominator
boundary, the status breakdown, and the two complementary views of where it
lives (rate vs composition, by spec_role)."""
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

ROLE_COLORS = {"change_proposal": "#d62728", "archived": "#1f77b4"}


def main():
    conn = duckdb.connect()

    # done WITH anchor = the census denominator
    rows = conn.execute(f"""
        SELECT artifact_path, exists_at_anchor
        FROM read_parquet('{REF.as_posix()}')
        WHERE task_done = 1 AND anchor_sha IS NOT NULL
    """).fetchall()

    # done WITHOUT anchor = excluded from the census
    done_without_anchor = conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{REF.as_posix()}') "
        "WHERE task_done = 1 AND anchor_sha IS NULL"
    ).fetchone()[0]
    conn.close()

    done_with_anchor = len(rows)

    by_status = defaultdict(int)  # exists_at_anchor -> count
    by_role = defaultdict(lambda: [0, 0])  # role -> [refs, missing]
    for artifact_path, exists in rows:
        by_status[exists] += 1
        role = classify_spec_role(artifact_path)
        by_role[role][0] += 1
        if exists == 0:
            by_role[role][1] += 1

    total_refs = sum(v[0] for v in by_role.values())
    total_absent = sum(v[1] for v in by_role.values())
    overall = total_absent / total_refs * 100
    roles = ["change_proposal", "archived"]

    fig, axes = plt.subplots(2, 3, figsize=(14, 6.4))
    ax0 = axes[0, 0]
    ax1 = axes[0, 1]
    ax2 = axes[0, 2]
    ax3 = axes[1, 0]
    ax4 = axes[1, 1]
    axes[1, 2].axis("off")

    # 0) denominator boundary: done with vs without anchor
    labels0 = ["with anchor", "without anchor"]
    vals0 = [done_with_anchor, done_without_anchor]
    colors0 = ["#1f77b4", "#7f7f7f"]
    total_done = done_with_anchor + done_without_anchor
    bars0 = ax0.bar(labels0, vals0, color=colors0, edgecolor="white")
    for b, v in zip(bars0, vals0):
        ax0.text(b.get_x() + b.get_width() / 2, v + 8000,
                 f"{v:,}\n({v / total_done * 100:.1f}%)", ha="center", fontsize=8)
    ax0.set_ylabel("references (task_done = 1)")
    ax0.set_title("Done tasks: with vs without anchor")

    # 1) status breakdown: present vs absent vs ambiguous (pie)
    labels1 = [f"present ({by_status[1]:,}, {by_status[1] / total_refs * 100:.1f}%)",
               f"absent ({by_status[0]:,}, {by_status[0] / total_refs * 100:.1f}%)",
               f"ambiguous ({by_status[2]:,}, {by_status[2] / total_refs * 100:.2f}%)"]
    vals1 = [by_status[1], by_status[0], by_status[2]]
    colors1 = ["#1f77b4", "#d62728", "#7f7f7f"]
    ax1.pie(vals1, labels=labels1, colors=colors1, startangle=90)
    ax1.set_title("Status: present vs absent vs ambiguous")

    # 2) total tasks per group (the size disparity)
    totals = [by_role[r][0] for r in roles]
    bars2 = ax2.bar(roles, totals, color=[ROLE_COLORS[r] for r in roles], edgecolor="white")
    ax2.set_ylabel("references (done + anchor)")
    ax2.set_title("Tasks per group (size disparity)")
    for b, v in zip(bars2, totals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 6000, f"{v:,}", ha="center", fontsize=9)

    # 3) missing rate per group
    rates = [by_role[r][1] / by_role[r][0] * 100 for r in roles]
    bars3 = ax3.bar(roles, rates, color=[ROLE_COLORS[r] for r in roles], edgecolor="white")
    ax3.axhline(overall, color="#7f7f7f", ls="--", lw=1.5, label=f"overall {overall:.1f}%")
    ax3.set_ylabel("missing rate (%)")
    ax3.set_title("Missing rate per group (rate view)")
    for b, v in zip(bars3, rates):
        ax3.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}%", ha="center", fontsize=9)
    ax3.set_ylim(0, max(rates) * 1.25)
    ax3.legend(fontsize=8)

    # 4) share of the missing (composition view)
    shares = [by_role[r][1] / total_absent * 100 for r in roles]
    bars4 = ax4.bar(roles, shares, color=[ROLE_COLORS[r] for r in roles], edgecolor="white")
    ax4.set_ylabel("share of missing (%)")
    ax4.set_title("Where the missing live (composition view)")
    for b, v in zip(bars4, shares):
        ax4.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", fontsize=9)
    ax4.set_ylim(0, 100)
    ax4.text(0.5, -0.22, f"n = {total_absent:,} missing; non-openspec 125 (0.0%), living/na 0",
             transform=ax4.transAxes, ha="center", fontsize=8, color="#555555")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
