# %% [0] M1 — Sample vs Full: is the sample representative?
#   Question:    How does the SAMPLE differ from the FULL dataset?
#   Data:        SpecMine sample (v1.1) vs full (v1.0): spec_files,
#                openspec_code_refs, spec_links, pull_requests
#   Criterion:   row counts (specs, refs, traceability links, PRs)
#   Result:      sample 28,583 specs = 6.1% of the full 470,795; the PR layer is
#                5,992 in BOTH (complete in the sample); refs are a small subset
#   Meaning:     the sample is a small star-curated slice; the full is needed
#                for the census -> migrate from sample to full
# =====================================================================

from pathlib import Path
import subprocess
import sys

import duckdb
from scipy import stats

HERE = Path(__file__).resolve().parent
from db import SAMPLE_SPECMINE_DATA, SPECMINE_DATA  # noqa: E402
from chart_utils import chart_status  # noqa: E402

sample = Path(SAMPLE_SPECMINE_DATA)
full = Path(SPECMINE_DATA)

for p in (sample / "spec_files.parquet", full / "spec_files.parquet"):
    if not p.exists():
        sys.exit(f"{p} not found. See README 'Datasets' for the expected paths.")


def count(dirpath, table):
    conn = duckdb.connect()
    n = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{dirpath}/{table}.parquet')").fetchone()[0]
    conn.close()
    return n


print("=== M1 — Sample vs Full ===")
print(f"{'table':<22} {'sample':>9} {'full':>11} {'sample%':>8}")
for table in ("spec_files", "openspec_code_refs", "spec_links", "pull_requests"):
    s = count(sample, table)
    f = count(full, table)
    print(f"{table:<22} {s:>9,} {f:>11,} {s/f*100:>7.1f}%")

print("\nNote: the PR layer is 5,335 in the sample (89% of the full 5,992), but the "
      "specs are only 6% -> the sample is nearly complete for PRs, thin for specs.")


def archived_pct(dirpath):
    conn = duckdb.connect()
    n_arch = conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{dirpath}/spec_files.parquet') "
        "WHERE spec_role = 'archived'"
    ).fetchone()[0]
    n_all = conn.execute(
        f"SELECT COUNT(*) FROM read_parquet('{dirpath}/spec_files.parquet')"
    ).fetchone()[0]
    conn.close()
    return n_arch, n_all


arch_s, all_s = archived_pct(sample)
arch_f, all_f = archived_pct(full)
print("\n=== M1 — spec_role composition: archived in sample vs full ===")
print(f"  archived: sample {arch_s:,} / {all_s:,} = {arch_s/all_s*100:.1f}%  vs  "
      f"full {arch_f:,} / {all_f:,} = {arch_f/all_f*100:.1f}%")
print("  (the star-curated sample over-represents archived specs) -> use the full")

# ---- spec_tool composition (full) ----
conn = duckdb.connect()
tool_df = conn.execute(
    f"SELECT spec_tool, COUNT(*) AS n FROM read_parquet('{full}/spec_files.parquet') "
    "GROUP BY spec_tool ORDER BY n DESC"
).df()
conn.close()
tot = int(tool_df["n"].sum())
tool_df["pct"] = (tool_df["n"] / tot * 100).round(1)
print("\n=== M1 — spec_tool composition (full) ===")
print(tool_df.to_string(index=False))

# ---- OpenSpec-only n_lines (full) ----
conn = duckdb.connect()
q = (
    f"SELECT f.n_lines FROM read_parquet('{full}/spec_content_features.parquet') f "
    f"JOIN read_parquet('{full}/spec_files.parquet') s ON f.file_url_sha16 = s.file_url_sha16 "
    "WHERE s.spec_tool = 'openspec' AND f.n_lines IS NOT NULL"
)
nl = conn.execute(q).df()["n_lines"]
conn.close()
n = len(nl)
sub = nl.sort_values().reset_index(drop=True).sample(5000, random_state=0)
print("\n=== M1 — OpenSpec-only n_lines (full) ===")
print(f"  n = {n:,}; mean = {round(float(nl.mean()), 1)}; median = {round(float(nl.median()), 1)}; "
      f"skew = {round(float(stats.skew(nl)), 1)}; Shapiro p = {float(stats.shapiro(sub).pvalue):.2e}")

# ---------------- Chart ----------------
png = HERE / "data" / "chart_m1_sample_full.png"
if not png.exists():
    subprocess.run(["python", str(HERE / "chart_m1.py")], check=True)
    print("\nchart: data/chart_m1_sample_full.png")
else:
    _, stale = chart_status(png, sample / "spec_files.parquet", full / "spec_files.parquet")
    note = "  [STALE - run 'make charts']" if stale else ""
    print(f"\nchart: data/chart_m1_sample_full.png{note}")
