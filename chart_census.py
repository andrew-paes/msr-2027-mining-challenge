"""Generate the census chart: the done-but-missing gap, its denominator
boundary, the status breakdown, and the two complementary views of where it
lives (rate vs composition, by spec_role).

Usage:
    python chart_census.py
"""
from pathlib import Path
from collections import defaultdict

import duckdb
import matplotlib.pyplot as plt

import chart_style as cs
import db
from taxonomy import classify_spec_role

HERE = Path(__file__).resolve().parent
OUT_PNG = HERE / "data" / "chart_census.png"
REF = Path(db.SPECMINE_DATA) / "openspec_code_refs.parquet"

ROLE_COLOR = {"change_proposal": cs.NAVY, "archived": cs.BROWN}
ROLE_LABEL = {"change_proposal": "change proposal", "archived": "archived"}
STATUS = [("present", 1, cs.BLUE), ("absent", 0, cs.VERMILLION),
          ("ambiguous", 2, cs.SLATE)]


def share(value: float, total: float) -> str:
    """Percentage with a second decimal for the cases too small to round."""
    pct = value / total * 100
    return f"{pct:.2f}%" if pct < 0.1 else f"{pct:.1f}%"


def main():
    cs.apply_style()

    conn = duckdb.connect()
    refs = f"read_parquet('{REF.as_posix()}')"
    rows = conn.execute(
        f"SELECT artifact_path, exists_at_anchor FROM {refs} "
        "WHERE task_done = 1 AND anchor_sha IS NOT NULL"
    ).fetchall()
    done_without_anchor = conn.execute(
        f"SELECT COUNT(*) FROM {refs} WHERE task_done = 1 AND anchor_sha IS NULL"
    ).fetchone()[0]
    ambiguous_repos = conn.execute(
        f"SELECT COUNT(DISTINCT repo_name) FROM {refs} WHERE exists_at_anchor = 2"
    ).fetchone()[0]
    conn.close()

    by_status = defaultdict(int)           # exists_at_anchor -> count
    by_role = defaultdict(lambda: [0, 0])  # role -> [refs, missing]
    for artifact_path, exists in rows:
        by_status[exists] += 1
        role = classify_spec_role(artifact_path)
        by_role[role][0] += 1
        if exists == 0:
            by_role[role][1] += 1

    done_with_anchor = len(rows)
    total_done = done_with_anchor + done_without_anchor
    total_refs = sum(v[0] for v in by_role.values())
    total_absent = sum(v[1] for v in by_role.values())
    overall = total_absent / total_refs * 100
    roles = ["change_proposal", "archived"]

    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(2, 2, figsize=(10.6, 6.8))

    # 0) denominator boundary: done with vs without anchor
    labels0 = ["with anchor", "without anchor"]
    vals0 = [done_with_anchor, done_without_anchor]
    bars0 = ax0.bar(labels0, vals0, width=0.55,
                    color=[cs.BLUE, cs.SLATE], edgecolor=cs.INK, linewidth=0.8)
    cs.vlabel(ax0, bars0,
              [f"{cs.fmt_int(v)}\n({share(v, total_done)})" for v in vals0],
              fontsize=9.5)
    cs.int_axis(ax0, "y")
    ax0.grid(False, axis="x")
    ax0.set_ylabel("references with task_done = 1")
    cs.title(ax0, "The census denominator",
             "done references with and without a resolvable anchor", width=46)

    # 1) status breakdown: present vs absent vs ambiguous
    status_names = [name for name, _key, _c in STATUS]
    status_vals = [by_status[key] for _n, key, _c in STATUS]
    bars1 = ax1.bar(status_names, status_vals, width=0.55,
                    color=[color for _n, _k, color in STATUS],
                    edgecolor=cs.INK, linewidth=0.8)
    cs.vlabel(ax1, bars1[:2],
              [f"{cs.fmt_int(v)}\n({share(v, total_refs)})" for v in status_vals[:2]],
              fontsize=9.5)
    # 130 references are invisible at this scale: a leader line keeps the label
    # from being read as a value of its own
    ax1.annotate(f"{cs.fmt_int(status_vals[2])} ({share(status_vals[2], total_refs)})",
                 xy=(2, status_vals[2]), xytext=(2, status_vals[2] + 90_000),
                 ha="center", fontsize=9.5, color=cs.INK,
                 arrowprops=dict(arrowstyle="-", color=cs.MUTED, lw=0.8))
    cs.int_axis(ax1, "y")
    ax1.grid(False, axis="x")
    ax1.set_ylabel("references with a resolvable anchor")
    cs.title(ax1, "Present, absent and ambiguous",
             f"exists_at_anchor at the anchor commit; ambiguous = "
             f"{cs.fmt_int(by_status[2])} references in {ambiguous_repos} repos",
             width=46)

    # 2) missing rate per group (the rate view)
    rates = [by_role[r][1] / by_role[r][0] * 100 for r in roles]
    bars2 = ax2.bar([ROLE_LABEL[r] for r in roles], rates, width=0.55,
                    color=[ROLE_COLOR[r] for r in roles],
                    edgecolor=cs.INK, linewidth=0.8)
    cs.vlabel(ax2, bars2, [f"{v:.1f}%" for v in rates], fontsize=10)
    cs.pct_axis(ax2, "y", 0)
    ax2.grid(False, axis="x")
    ax2.set_ylim(0, max(rates) * 1.35)
    ax2.set_ylabel("missing rate")
    ax2.set_xticks(range(len(roles)))
    ax2.set_xticklabels([f"{ROLE_LABEL[r]}\n(n = {cs.fmt_int(by_role[r][0])})"
                         for r in roles])
    cs.title(ax2, "The rate view: where the gap is worse",
             "share of the done references that are missing, per spec role; "
             f"the overall rate is {overall:.1f}%", width=46)

    # 3) share of the missing (the composition view)
    shares = [by_role[r][1] / total_absent * 100 for r in roles]
    bars3 = ax3.bar([ROLE_LABEL[r] for r in roles], shares, width=0.55,
                    color=[ROLE_COLOR[r] for r in roles],
                    edgecolor=cs.INK, linewidth=0.8)
    cs.vlabel(ax3, bars3, [f"{v:.1f}%" for v in shares], fontsize=10)
    cs.pct_axis(ax3, "y", 0)
    ax3.grid(False, axis="x")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("share of the missing references")
    ax3.set_xticks(range(len(roles)))
    ax3.set_xticklabels([f"{ROLE_LABEL[r]}\n({cs.fmt_int(by_role[r][1])} missing)"
                         for r in roles])
    cs.title(ax3, "The composition view: where the gap lives",
             f"split of the {cs.fmt_int(total_absent)} missing references by spec role",
             width=52)

    cs.source_note(
        fig,
        f"Census over the whole corpus: {cs.fmt_int(total_refs)} done references with a "
        f"resolvable anchor; the {cs.fmt_int(done_without_anchor)} done references without "
        "one are excluded. The rate and the composition disagree because the groups "
        "differ in size: "
        f"{share(by_role['change_proposal'][0], total_refs)} of the references are active "
        f"change proposals and {share(by_role['archived'][0], total_refs)} are archived "
        "changes. Both views are shown so that neither is read as the whole answer.",
        y=-0.04,
    )

    fig.tight_layout()
    cs.save(fig, OUT_PNG)


if __name__ == "__main__":
    main()
