# %% [0] M8 — Phase 3 + Bridge: how many are truly "never"?
#   Question:    Of the done-but-missing, how many are genuinely never implemented
#                (vs renamed or created later)? Does accessibility make it worse?
#   Data:        data/phase3_results.csv + data/accessibility_requirements.csv
#   Criterion:   classify_ref() 5 buckets (git log --diff-filter=A / --follow);
#                never rate by maturity and by accessibility
#   Result:      never 54.5% (median 66.7% per repo); never/deleted inverts with
#                maturity; a11y repos 60.4% never vs 41.5% without
#   Meaning:     84% genuinely absent; churn in 0-star, non-implementation in
#                serious repos; accessibility is aspirational
# =====================================================================

from pathlib import Path
import subprocess
import sys

import pandas as pd

from chart_utils import chart_status

HERE = Path(__file__).resolve().parent
RES = HERE / "data" / "phase3_results.csv"
A11Y = HERE / "data" / "accessibility_requirements.csv"
TAXONOMY = HERE / "data" / "taxonomy_e0.csv"

if not RES.exists():
    sys.exit("phase3_results.csv not found. Run phase3.py (needs git clone). See README.")
if not A11Y.exists():
    sys.exit("accessibility_requirements.csv not found. Run extract_accessibility.py.")

res = pd.read_csv(RES)
a11y_repos = set(pd.read_csv(A11Y).repo_name)
res["has_a11y"] = res.repo_name.isin(a11y_repos)

print("=== M8 — classification distribution (refs) ===")
counts = res.classification.value_counts()
for cls, n in counts.items():
    print(f"  {cls:<22} {n:,} ({n / len(res) * 100:.1f}%)")

never_rate = res.groupby("repo_name")["classification"].apply(lambda s: (s == "never").mean())
print(f"\n  median 'never' per repo: {never_rate.median() * 100:.1f}%")

print("\n=== never vs deleted by maturity (refs %) ===")
bucket = pd.crosstab(res.star_bucket, res.classification, normalize="index") * 100
for b in ["0-9", "10-99", "100+"]:
    if b in bucket.index:
        print(f"  {b}: never {bucket.loc[b, 'never']:.1f}% | deleted {bucket.loc[b, 'deleted_before_anchor']:.1f}%")

print("\n=== bridge: never rate with vs without accessibility ===")
for b in ["0-9", "10-99", "100+"]:
    sub = res[res.star_bucket == b]
    na = sub[sub.has_a11y]["classification"].eq("never").mean()
    nn = sub[~sub.has_a11y]["classification"].eq("never").mean()
    print(f"  {b}: a11y {na * 100:.1f}% vs no-a11y {nn * 100:.1f}%")

for name, script in [("phase3_by_bucket.png", "chart_phase3.py"), ("chart_bridge.png", "chart_bridge.py")]:
    png = HERE / "data" / name
    if not png.exists():
        subprocess.run(["python", str(HERE / script)], check=True)
        print(f"chart: data/{name}")
    else:
        _, stale = chart_status(png, RES, A11Y, TAXONOMY)
        note = "  [STALE - run 'make charts']" if stale else ""
        print(f"chart: data/{name}{note}")
