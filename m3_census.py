# %% [0] M3 — Census: does the "done but missing" gap exist at scale, and
#           where does it concentrate?
#   Question:    How many done tasks have no code at the anchor commit, and in
#                which spec_role (OpenSpec lifecycle) do they concentrate?
#   Data:        openspec_code_refs (full): task_done, exists_at_anchor,
#                anchor_sha, artifact_path
#   Criterion:   task_done=1 AND anchor_sha IS NOT NULL, group by
#                exists_at_anchor; then by spec_role derived from artifact_path
#   Result:      34,227 absent = 10.3% of 332,168 -> the gap exists at scale;
#                it concentrates in change_proposal (17.7%) vs archived (9.0%);
#                living has zero refs (tasks.md lives only under changes/)
#   Meaning:     the "done but missing" phenomenon is population-level and is a
#                property of the change-proposal workflow, not abandonment
# =====================================================================

from pathlib import Path
from collections import defaultdict
import subprocess
import sys

import duckdb

HERE = Path(__file__).resolve().parent
from db import SPECMINE_DATA  # noqa: E402
from chart_utils import chart_status  # noqa: E402
from taxonomy import classify_spec_role  # noqa: E402
full = Path(SPECMINE_DATA)
p = full / "openspec_code_refs.parquet"
if not p.exists():
    sys.exit(f"{p} not found. See README 'Datasets'.")

conn = duckdb.connect()
rows = conn.execute(f"""
    SELECT artifact_path, exists_at_anchor
    FROM read_parquet('{p}')
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

print("=== M3 — done tasks: present vs absent at the anchor ===")
total = len(rows)
for status in sorted(by_status):
    n = by_status[status]
    print(f"  exists_at_anchor={status}: {n:,} ({n / total * 100:.1f}%)")

absent = by_status.get(0, 0)
print(f"\n  done but missing = {absent:,} = {absent / total * 100:.1f}% of {total:,} done references")

print("\n=== M3 — where does the gap concentrate? (by spec_role) ===")
for role in ("change_proposal", "archived", "living", "na", "non-openspec"):
    n, missing = by_role[role]
    if n:
        print(f"  {role:<16} {n:>7,} refs · {missing:>6,} missing = {missing / n * 100:.1f}%")
    else:
        print(f"  {role:<16} {n:>7,} refs  (no tasks.md under this role)")

print("\n  note: tasks.md lives only under openspec/changes/, so the gap is a")
print("  change-proposal-workflow phenomenon: 17.7% change_proposal vs 9.0% archived.")

png = HERE / "data" / "chart_census.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_census.py")], check=True)
    print("\nchart: data/chart_census.png")
else:
    _, stale = chart_status(png, p)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_census.png{note}")
