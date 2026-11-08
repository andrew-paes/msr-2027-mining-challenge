# %% [0] M4 — Discovery: is exists_at_anchor really binary?
#   Question:    Is the exists_at_anchor column just 0/1?
#   Data:        openspec_code_refs (full): exists_at_anchor, anchor_sha
#   Criterion:   GROUP BY exists_at_anchor; NULL anchor_sha correlation
#   Result:      0 (51,979), 1 (361,083), 2 (130, in 5 repos), NULL (22,209);
#                NULL <=> anchor_sha=NULL (perfect correlation)
#   Meaning:     the column is under-documented (DATA_DICTIONARY says "1 if
#                existed"); documenting it is a data-quality contribution
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
print("=== M4 — exists_at_anchor distribution ===")
for r in conn.execute(f"SELECT exists_at_anchor, COUNT(*) FROM read_parquet('{p}') GROUP BY 1 ORDER BY 1").fetchall():
    print(f"  exists_at_anchor={r[0]}: {r[1]:,}")

n_null = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{p}') WHERE exists_at_anchor IS NULL AND anchor_sha IS NULL").fetchone()[0]
n_null_total = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{p}') WHERE exists_at_anchor IS NULL").fetchone()[0]
print(f"\n  exists_at_anchor IS NULL: {n_null_total:,} -> all have anchor_sha NULL? {n_null == n_null_total}")

print("\n  exists_at_anchor=2 (ambiguous) by repo:")
for r in conn.execute(f"SELECT repo_name, COUNT(*) FROM read_parquet('{p}') WHERE exists_at_anchor = 2 GROUP BY 1 ORDER BY 2 DESC").fetchall():
    print(f"    {r[0]}: {r[1]}")
conn.close()

# ---------------- Chart ----------------
png = HERE / "data" / "chart_m4_discovery.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_m4.py")], check=True)
    print("\nchart: data/chart_m4_discovery.png")
else:
    _, stale = chart_status(png, p)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_m4_discovery.png{note}")
