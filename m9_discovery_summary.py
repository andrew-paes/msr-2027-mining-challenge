# %% [0] M9 — Summary: the arc of the discovery
#   Question:    What is the whole story, from data to the central result?
#   Data:        the five result charts (committed PNGs)
#   Criterion:   the milestone order M0 -> M8
#   Result:      10.3% done-but-missing (concentrating in change_proposal,
#                17.7% vs 9.0% archived) -> 91% real files -> 84% genuinely
#                absent (54% never + 30% deleted) -> inverts with maturity ->
#                accessibility makes it worse
#   Meaning:     the central result: most "done but missing" is genuinely never
#                implemented, the gap concentrates in active change proposals,
#                and the composition shifts with maturity
# =====================================================================

from pathlib import Path

from chart_utils import chart_status
from db import SAMPLE_SPECMINE_DATA, SPECMINE_DATA

HERE = Path(__file__).resolve().parent
SAMPLE = Path(SAMPLE_SPECMINE_DATA)
FULL = Path(SPECMINE_DATA)

CHARTS = [
    ("chart_m0_sample.png", "M0 - strongly right-skewed n_lines", "chart_m0.py",
     [SAMPLE / "spec_content_features.parquet", SAMPLE / "spec_files.parquet"]),
    ("chart_m0_tools.png", "M0 - 77.4% OpenSpec (17 tools)", "chart_m0_tools.py",
     [SAMPLE / "spec_files.parquet"]),
    ("chart_m1_sample_full.png", "M1 - sample 6.1% of specs, 89% of PRs", "chart_m1.py",
     [SAMPLE / "spec_files.parquet", FULL / "spec_files.parquet"]),
    ("chart_m1_tools.png", "M1 - 58.4% OpenSpec in the full", "chart_m1_tools.py",
     [FULL / "spec_files.parquet"]),
    ("chart_m2_pivot.png", "M2 - all PRs merged -> traceability", "chart_m2.py",
     [FULL / "pull_requests.parquet"]),
    ("chart_census.png", "M3 - 10.3% missing; 17.7% change_proposal vs 9.0% archived", "chart_census.py",
     [FULL / "openspec_code_refs.parquet"]),
    ("chart_m4_discovery.png", "M4 - exists_at_anchor not binary", "chart_m4.py",
     [FULL / "openspec_code_refs.parquet"]),
    ("chart_taxonomy.png", "M5 - 91% real file references", "chart_taxonomy.py",
     [HERE / "data" / "taxonomy_e0.csv", FULL / "openspec_code_refs.parquet"]),
    ("chart_accessibility.png", "M6 - 27.1% verifiable", "chart_accessibility.py",
     [HERE / "data" / "accessibility_requirements.csv", FULL / "spec_files.parquet"]),
    ("chart_m7_calibration.png", "M7 - 15.2% rename (94.8% tautological)", "chart_m7.py",
     [FULL / "openspec_code_refs.parquet"]),
    ("chart_outcomes.png", "M8 - 84% genuinely absent (never + deleted)", "chart_outcomes.py",
     [HERE / "data" / "classification_results.csv"]),
    ("chart_by_bucket.png", "M8 - never/deleted inverts with maturity", "chart_by_bucket.py",
     [HERE / "data" / "classification_results.csv"]),
    ("chart_bridge.png", "M8 - accessibility -> more never", "chart_bridge.py",
     [HERE / "data" / "classification_results.csv", HERE / "data" / "accessibility_requirements.csv"]),
    ("chart_bridge_repo.png", "M8 - repo-level never rate (Mann-Whitney p=0.17)", "chart_bridge_repo.py",
     [HERE / "data" / "classification_results.csv", HERE / "data" / "accessibility_requirements.csv"]),
]

print("=== M9 — the arc of the discovery ===")
print("1. The data is strongly right-skewed (M0).")
print("2. The sample is a star-curated 6% slice; migrate to full (M1).")
print("3. The traceability question is the one the data supports (M2).")
print("4. 10.3% of done tasks have no code at the anchor; the gap concentrates")
print("   in active change proposals: 17.7% vs 9.0% archived (M3).")
print("5. 91% of those are real file references, not noise (M5).")
print("6. 27.1% of accessibility requirements are verifiable (M6).")
print("7. 15.2% of resolved paths normalize elsewhere (M7).")
print("8. 84% are genuinely absent: 54% never + 30% written-then-removed; the")
print("   never/deleted composition inverts with maturity; accessibility")
print("   correlates with more never (M8).")

print("\n=== the five result charts ===")
for fname, meaning, script, sources in CHARTS:
    p = HERE / "data" / fname
    exists, stale = chart_status(p, *sources)
    if not exists:
        status = f"MISSING - run 'python {script}'"
    elif stale:
        status = "STALE - run 'make charts'"
    else:
        status = "ok"
    print(f"  {fname:<28} {meaning:<46} [{status}]")

print("\nRegenerate all charts (and the CSVs that feed them) with:  make charts")
print("\nRead order: m0 -> m1 -> ... -> m8 -> m9 (this file).")
