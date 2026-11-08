# %% [0] M5 — Taxonomy: real file or path noise?
#   Question:    Of the 34,227 done-but-missing, how many are real file paths?
#   Data:        data/taxonomy_e0.csv (level column)
#   Criterion:   classify_path() by path SHAPE: relative_ext (dir+ext),
#                bare_ext (name+ext), non_file (glob/absolute/no-ext)
#   Result:      17,799 clean + 13,326 bare = 91% real file; 3,102 non-file (9%)
#   Meaning:     the "missing" is real absence, not malformed paths
# =====================================================================

from pathlib import Path
import subprocess
import sys

import pandas as pd

from chart_utils import chart_status
from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
CSV = HERE / "data" / "taxonomy_e0.csv"
PARQUET = Path(SPECMINE_DATA) / "openspec_code_refs.parquet"

if CSV.exists():
    print("loading committed data/taxonomy_e0.csv (fast path)")
else:
    if not PARQUET.exists():
        sys.exit("Full SpecMine dataset not found. See README 'Datasets'.")
    print("regenerating taxonomy_e0.csv via taxonomy.py")
    subprocess.run(["python", str(HERE / "taxonomy.py")], check=True)

df = pd.read_csv(CSV)
counts = df["level"].value_counts()
total = counts.sum()
print("=== M5 — three-level taxonomy ===")
for level, n in counts.items():
    print(f"  {level:<14} {n:,} ({n / total * 100:.1f}%)")
real = counts.get("clean_path", 0) + counts.get("bare_filename", 0)
print(f"\n  real file references = {real:,} ({real / total * 100:.1f}%)")

png = HERE / "data" / "chart_taxonomy.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_taxonomy.py")], check=True)
    print("\nchart: data/chart_taxonomy.png")
else:
    _, stale = chart_status(png, CSV, PARQUET)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_taxonomy.png{note}")
