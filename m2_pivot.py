# %% [0] M2 — The pivot: which question does the data actually support?
#   Question:    Which research question is the most novel and data-supported?
#   Data:        (decision, informed by) pull_requests.is_merged
#   Criterion:   is_merged distribution (any rejected/closed PRs visible?)
#   Result:      all 5,992 spec-touching PRs are merged (is_merged=1) -> the
#                rejected/closed PRs are invisible -> the review question (Q3)
#                cannot be answered
#   Meaning:     scope to the traceability question (Q2); trust becomes
#                motivation, never a causal conclusion
# =====================================================================

from pathlib import Path
import subprocess
import sys

import duckdb

HERE = Path(__file__).resolve().parent
from db import SPECMINE_DATA  # noqa: E402
from chart_utils import chart_status  # noqa: E402
full = Path(SPECMINE_DATA)
p = full / "pull_requests.parquet"
if not p.exists():
    sys.exit(f"{p} not found. See README 'Datasets'.")

conn = duckdb.connect()
print("=== M2 — is_merged distribution (why the review question was dropped) ===")
for r in conn.execute(f"SELECT is_merged, COUNT(*) FROM read_parquet('{p}') GROUP BY 1 ORDER BY 1").fetchall():
    print(f"  is_merged={r[0]}: {r[1]:,}")

print("\nEvery spec-touching PR is merged, so 'rejected by a human reviewer' is not "
      "observable. The traceability question (does a checked-off task actually ship "
      "as code?) is the one the data supports.")

# ---------------- Chart ----------------
png = HERE / "data" / "chart_m2_pivot.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_m2.py")], check=True)
    print("\nchart: data/chart_m2_pivot.png")
else:
    _, stale = chart_status(png, p)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_m2_pivot.png{note}")
