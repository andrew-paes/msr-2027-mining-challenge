"""Streamlit dashboard: the SpecMine discovery walkthrough (M0-M8 + Discovery).

Run with:  py -m streamlit run app.py
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="MSR 2027 - Discovery walkthrough", layout="wide")
st.title("SpecMine discovery walkthrough")
st.caption("The line of reasoning from the data to the central result (SpecMine-only).")

DATA_DIR = Path(__file__).resolve().parent / "data"


def phase(title):
    st.markdown(
        f'<h3 style="color:#0b5394; margin-top:1.5rem; margin-bottom:0.5rem;">{title}</h3>',
        unsafe_allow_html=True,
    )


def caption(text):
    st.markdown(
        f'<div style="font-size:1.5rem; line-height:1.5; color:#666;">{text}</div>',
        unsafe_allow_html=True,
    )


def show_png(fname):
    p = DATA_DIR / fname
    if p.exists():
        st.image(str(p), width="stretch")
    else:
        st.info(f"{fname} not found - run the matching chart_*.py script.")


t0, t1, t2, t3, t4, t5, t6, t7, t8, td = st.tabs(
    ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "Discovery"]
)

with t0:
    phase("M0 - Sample stats: is the data strongly right-skewed?")
    caption(
        "The SpecMine sample is strongly right-skewed: n_lines has mean 91, median 56 and skew 11.4 "
        "(Shapiro-Wilk p ~ 0). This justifies non-parametric "
        "tests throughout the analysis. The sample is 77.4% OpenSpec, the only of the 17 tools with "
        "the task-done + anchor-commit marking that makes traceability answerable."
    )
    show_png("chart_m0_sample.png")
    show_png("chart_m0_tools.png")

with t1:
    phase("M1 - Sample vs Full: is the sample representative?")
    caption(
        "The sample is a small star-curated slice: 28,583 specs = 6.1% of the full 470,795 and "
        "7.0% of the code references; the PR layer is 5,335 (89% of 5,992). The full dataset is "
        "needed for the census. OpenSpec dominates the full (58.4%), and the sample over-represents it (77.4%)."
    )
    show_png("chart_m1_sample_full.png")
    show_png("chart_m1_tools.png")

with t2:
    phase("M2 - The pivot: which question does the data support?")
    caption(
        "Every spec-touching PR in the dataset is merged (is_merged=1 for all 5,992), so "
        "'rejected by a human reviewer' is not observable - the review question (Q3) is dropped. "
        "The traceability question (does a checked-off task actually ship as code?) is the one "
        "the data supports."
    )
    show_png("chart_m2_pivot.png")

with t3:
    phase("M3 - Census: does the gap exist at scale?")
    caption(
        "34,227 references (10.3% of the 332,168 done references with a resolvable anchor) are "
        "marked done but have no code at the anchor commit - a population-level phenomenon. The gap concentrates in active change proposals: 17.7% vs 9.0% archived."
    )
    show_png("chart_census.png")

with t4:
    phase("M4 - Discovery: exists_at_anchor is not binary")
    caption(
        "exists_at_anchor is 0 (51,979), 1 (361,083), 2 (130, in 5 repos) and NULL (22,209); "
        "NULL happens exactly when anchor_sha is NULL. The column is under-documented - a "
        "data-quality contribution."
    )
    show_png("chart_m4_discovery.png")

with t5:
    phase("M5 - Taxonomy: real file or path noise?")
    caption(
        "91% of the done-but-missing are real file references (17,799 clean + 13,326 bare), 9% "
        "are non-file noise. The 'missing' is real absence, not malformed paths."
    )
    show_png("chart_taxonomy.png")

with t6:
    phase("M6 - Accessibility: what do the specs ask?")
    caption(
        "97,883 requirement lines across 10,717 repos; 27.1% are verifiable. Formal spec tools "
        "(openspec 37.0%, speckit 35.6%) write testable accessibility requirements far more "
        "often than informal specs (docs_embedded 8.9%)."
    )
    show_png("chart_accessibility.png")

with t7:
    phase("M7 - Calibration: how much is path normalization?")
    caption(
        "Among the references with a clean relative path that DO resolve, 15.2% resolve at a "
        "different path than written - the rename/normalization burden the next layer must "
        "recover. (The 94.8% for bare names is tautological.)"
    )
    show_png("chart_m7_calibration.png")

with t8:
    phase("M8 - clone-classify + Bridge: how many are truly 'never'?")
    caption(
        "84% are genuinely absent at the anchor: 54% never (median 66.7% per repo) + 30% "
        "written-then-removed. The never/deleted composition inverts with maturity (churn in "
        "0-star, non-implementation in serious repos), and repositories with accessibility "
        "requirements have more 'never' (60.4% vs 41.5%)."
    )
    show_png("chart_outcomes.png")
    show_png("chart_by_bucket.png")
    show_png("chart_bridge.png")
    show_png("chart_bridge_repo.png")

with td:
    phase("Discovery - the full arc (M0 -> M8)")
    caption(
        "10.3% done-but-missing (17.7% change_proposal vs 9.0% archived) -> 91% real files -> 84% genuinely absent (54% never + 30% "
        "deleted) -> the composition inverts with maturity -> accessibility correlates with "
        "more never."
    )
    for label, fname, meaning in [
        ("M0", "chart_m0_sample.png", "strongly right-skewed: skew 11.4"),
        ("M1", "chart_m1_sample_full.png", "sample = 6.1% of specs, 89% of PRs"),
        ("M2", "chart_m2_pivot.png", "all 5,992 PRs merged -> scope to traceability"),
        ("M3", "chart_census.png", "34,227 = 10.3% done-but-missing; 17.7% change_proposal vs 9.0% archived"),
        ("M4", "chart_m4_discovery.png", "exists_at_anchor is 0/1/2/NULL, not binary"),
        ("M5", "chart_taxonomy.png", "91% real file references"),
        ("M6", "chart_accessibility.png", "27.1% verifiable"),
        ("M7", "chart_m7_calibration.png", "15.2% rename (94.8% tautological)"),
        ("M8", "chart_outcomes.png", "84% genuinely absent (54% never + 30% deleted)"),
        ("M8", "chart_by_bucket.png", "never/deleted inverts with maturity"),
        ("M8", "chart_bridge.png", "accessibility -> more never"),
        ("M8", "chart_bridge_repo.png", "repo-level never rate (Mann-Whitney p=0.17)"),
    ]:
        st.markdown(f"**{label}** - {meaning}")
        show_png(fname)
