# %% [0] M6 — Accessibility: what do the specs ask, and is it verifiable?
#   Question:    Which accessibility concerns appear, and what share are verifiable?
#   Data:        data/accessibility_requirements.csv (verifiable column)
#   Criterion:   verifiable = shall/must OR a measurable threshold (per line)
#   Result:      97,883 lines in 10,717 repos; 27.1% verifiable; openspec 37.0%
#                vs docs_embedded 8.9%
#   Meaning:     formal spec tools write testable accessibility requirements
#                far more often than informal specs
# =====================================================================

from pathlib import Path
import subprocess
import sys

import pandas as pd

from chart_utils import chart_status
from db import SPECMINE_DATA

HERE = Path(__file__).resolve().parent
CSV = HERE / "data" / "accessibility_requirements.csv"
SPEC_FILES = Path(SPECMINE_DATA) / "spec_files.parquet"

if CSV.exists():
    print("loading committed data/accessibility_requirements.csv (fast path)")
else:
    sys.exit("accessibility_requirements.csv not found. Run extract_accessibility.py "
             "(needs specs.jsonl). See README.")

df = pd.read_csv(CSV)
n = len(df)
repos = df.repo_name.nunique()
verifiable = int(df.verifiable.sum())
print(f"=== M6 — accessibility (n={n:,} lines, {repos:,} repos) ===")
print(f"  verifiable: {verifiable:,} ({verifiable / n * 100:.1f}%)")

g = df.groupby("spec_tool")["verifiable"].agg(["count", "mean"]).reset_index()
g = g[g["count"] >= 500].sort_values("mean", ascending=False)
print("\n  verifiable share by spec tool (top 6):")
for _, r in g.head(6).iterrows():
    print(f"    {r['spec_tool']:<16} {r['mean'] * 100:>5.1f}%  (n={r['count']:,})")

png = HERE / "data" / "chart_accessibility.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_accessibility.py")], check=True)
    print("\nchart: data/chart_accessibility.png")
else:
    _, stale = chart_status(png, CSV, SPEC_FILES)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_accessibility.png{note}")
