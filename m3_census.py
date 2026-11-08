# %% [0] M3 — Census: does the "done but missing" gap exist at scale?
#   Question:    How many done tasks have no code at the anchor commit?
#   Data:        openspec_code_refs (full): task_done, exists_at_anchor, anchor_sha
#   Criterion:   task_done=1 AND anchor_sha IS NOT NULL, group by exists_at_anchor
#   Result:      34,227 absent = 10.3% of 332,168 -> the gap exists at scale
#   Meaning:     the "done but missing" phenomenon is population-level, not a
#                sample artifact
# =====================================================================

from pathlib import Path
import subprocess
import sys

import duckdb

HERE = Path(__file__).resolve().parent
from db import SPECMINE_DATA  # noqa: E402
from chart_utils import chart_status  # noqa: E402
full = Path(SPECMINE_DATA)
p = full / "openspec_code_refs.parquet"
if not p.exists():
    sys.exit(f"{p} not found. See README 'Datasets'.")

conn = duckdb.connect()
print("=== M3 — done tasks: present vs absent at the anchor ===")
rows = conn.execute(f"""
    SELECT exists_at_anchor, COUNT(*) AS n
    FROM read_parquet('{p}')
    WHERE task_done = 1 AND anchor_sha IS NOT NULL
    GROUP BY 1 ORDER BY 1
""").fetchall()
conn.close()

total = sum(r[1] for r in rows)
for r in rows:
    print(f"  exists_at_anchor={r[0]}: {r[1]:,} ({r[1] / total * 100:.1f}%)")

absent = next(r[1] for r in rows if r[0] == 0)
print(f"\n  done but missing = {absent:,} = {absent / total * 100:.1f}% of {total:,} done references")

png = HERE / "data" / "chart_census.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_census.py")], check=True)
    print("\nchart: data/chart_census.png")
else:
    _, stale = chart_status(png, p)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_census.png{note}")
