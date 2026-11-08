# %% [0] M7 — Calibration: how much is path normalization?
#   Question:    How much of the "missing" could be a path written differently?
#   Data:        openspec_code_refs (full): resolved_path vs code_path (exists=1)
#   Criterion:   resolved_path != code_path among resolved references
#   Result:      relative paths resolve elsewhere 15.2%; bare names 94.8% (but
#                that is tautological — a bare name always gains a directory)
#   Meaning:     15.2% motivates the rename/temporal layer; do NOT cite the 94.8%
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

from collections import Counter

import duckdb

from taxonomy import classify_path  # reuse the exact classifier (relative_ext etc.)

conn = duckdb.connect()
rows = conn.execute(f"""
    SELECT code_path, resolved_path
    FROM read_parquet('{p}')
    WHERE task_done = 1 AND anchor_sha IS NOT NULL
      AND exists_at_anchor = 1 AND resolved_path IS NOT NULL AND resolved_path != ''
""").fetchall()
conn.close()

diff = Counter()
total = Counter()
for cp, rp in rows:
    _, shape = classify_path(cp)
    if shape in ("relative_ext", "bare_ext", "glob", "absolute"):
        total[shape] += 1
        if rp != cp:
            diff[shape] += 1

print("=== M7 — resolved_path != code_path among resolved references (exists=1) ===")
for shape in ("relative_ext", "bare_ext", "glob", "absolute"):
    if total[shape]:
        print(f"  {shape:<12} {diff[shape]:,} / {total[shape]:,} = {diff[shape] / total[shape] * 100:.1f}%")

print("\nThe ~15% for relative_ext is the real rename/normalization signal; the ~95% "
      "for bare_ext is tautological (a bare name always gains a directory).")

# ---------------- Chart ----------------
png = HERE / "data" / "chart_m7_calibration.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_m7.py")], check=True)
    print("\nchart: data/chart_m7_calibration.png")
else:
    _, stale = chart_status(png, p)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_m7_calibration.png{note}")
