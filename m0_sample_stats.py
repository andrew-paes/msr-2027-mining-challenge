# %% [0] M0 — Sample stats: is the data strongly right-skewed?
#   Question:    What does the SpecMine SAMPLE look like?
#   Data:        SpecMine sample (v1.1): spec_content_features.n_lines,
#                spec_files.spec_role, spec_files.spec_tool
#   Criterion:   mean / median / skew + Shapiro-Wilk (5,000-row subsample, the
#                Shapiro-Wilk limit is n <= 5000)
#   Result:      n_lines mean ~91, median ~56, skew ~11.4, Shapiro p ~ 0
#                (the spec_role composition is now an M1 input, not an M0 finding)
#   Meaning:     strongly right-skewed and non-normal -> justifies non-parametric tests
#                throughout the analysis
# =====================================================================

from pathlib import Path
import subprocess
import sys

import duckdb
import pandas as pd
from scipy import stats

from chart_utils import chart_status
from db import SAMPLE_SPECMINE_DATA

HERE = Path(__file__).resolve().parent
CSV = HERE / "data" / "sample_stats.csv"
sample = Path(SAMPLE_SPECMINE_DATA)
FEATS = sample / "spec_content_features.parquet"
FILES = sample / "spec_files.parquet"
PNG = HERE / "data" / "chart_m0_sample.png"

# ---------------- Bootstrap (three tiers) ----------------
if CSV.exists():
    # 1) fast path: the committed CSV always wins (never regenerate by default)
    print("loading committed data/sample_stats.csv (fast path)")
    summary = pd.read_csv(CSV)
else:
    # 2) regenerate only if the CSV is missing AND the sample is present
    if not FEATS.exists():
        # 3) friendly message, no stack trace
        sys.exit(
            "SpecMine sample (v1.1) not found.\n"
            "  -> Clone https://github.com/shyamagarwal13/specmine-official and place\n"
            "     its 'data/' at ../specmine-official/data/ (see README 'Datasets'),\n"
            "     or use the committed data/sample_stats.csv.\n"
        )
    print("regenerating sample stats from the sample dataset ...")

    # ---------------- Compute ----------------
    conn = duckdb.connect(":memory:")
    conn.execute(
        f"CREATE VIEW feats AS SELECT * FROM read_parquet('{FEATS}')"
    )
    conn.execute(
        f"CREATE VIEW files AS SELECT * FROM read_parquet('{FILES}')"
    )

    n_lines = conn.execute("SELECT n_lines FROM feats WHERE n_lines IS NOT NULL").df()["n_lines"]
    spec_role = conn.execute("SELECT spec_role FROM files").df()["spec_role"]

    # skew on the full sample; shapiro on a 5,000-row subsample (n <= 5000 limit)
    s = n_lines if len(n_lines) <= 5000 else n_lines.sample(5000, random_state=0)

    role_counts = spec_role.value_counts().to_dict()
    tool_counts = conn.execute("SELECT spec_tool FROM files").df()["spec_tool"].value_counts().to_dict()

    summary = pd.DataFrame([{
        "n_lines_n": int(len(n_lines)),
        "n_lines_mean": round(float(n_lines.mean()), 1),
        "n_lines_median": round(float(n_lines.median()), 1),
        "n_lines_skew": round(float(stats.skew(n_lines)), 1),
        "n_lines_shapiro_p": float(stats.shapiro(s).pvalue),
        "pct_archived": round(float((spec_role == "archived").mean() * 100), 1),
        **{f"n_role_{k}": v for k, v in sorted(role_counts.items(), key=lambda kv: -kv[1])},
        **{f"n_tool_{k}": v for k, v in sorted(tool_counts.items(), key=lambda kv: -kv[1])},
    }])

    summary.to_csv(CSV, index=False)

# ---------------- Report ----------------
print("\n=== M0 — SpecMine sample stats ===")
print(summary.to_string(index=False))

# ---------------- Chart ----------------
if not PNG.exists():
    subprocess.run(["python", str(HERE / "chart_m0.py")], check=True)
    print("\nchart: data/chart_m0_sample.png")
else:
    _, stale = chart_status(PNG, FEATS, FILES)
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_m0_sample.png{note}")
