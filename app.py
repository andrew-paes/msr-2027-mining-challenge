"""Streamlit dashboard for GitSkills + SpecMine exploratory analysis.

Run with:  py -m streamlit run app.py
"""
import pandas as pd
import streamlit as st

import charts
import db
import queries
import stats

st.set_page_config(page_title="MSR 2027 — GitSkills + SpecMine", layout="wide")
st.title("MSR 2027 Mining Challenge — Análise exploratória")
st.caption("GitSkills (SQLite) + SpecMine (Parquet) via DuckDB")


conn = db.get_conn()


def q(sql):
    return conn.execute(sql).df()


def show(fig):
    """Render a matplotlib figure at its native (~600px) size."""
    st.pyplot(fig, width="content")


tab_gs, tab_sm, tab_stats = st.tabs(["GitSkills", "SpecMine", "Estatística"])

# ---------------- GitSkills ----------------
with tab_gs:
    st.header("GitSkills — agent skills")

    st.subheader("Reuso / duplicação (cauda longa)")
    copies = q(queries.GITSKILLS["copy_distribution"])
    expanded = copies["copies"].repeat(copies["n_contents"])
    show(charts.log_hist(expanded, "Distribuição de cópias por conteúdo (log)", bins=40))
    st.write(f"Conteúdos distintos: {int(copies['n_contents'].sum()):,}")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Classe de localização")
        show(charts.bar(q(queries.GITSKILLS["location_class"]), "location_class", "n", "Location class"))
    with c2:
        st.subheader("Validade do front matter")
        show(charts.bar(q(queries.GITSKILLS["frontmatter"]), "frontmatter_valid", "n", "Front matter válido"))

    st.subheader("Comprimento do corpo (body_chars) + curva normal")
    body = q(queries.GITSKILLS["body_chars"])["body_chars"]
    show(charts.hist_with_normal(body, "Distribuição de body_chars (representantes)"))

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Skills por repositório (concentração)")
        spr = q(queries.GITSKILLS["skills_per_repo"])
        show(charts.log_hist(spr["n"], "Skills por repo (log)", bins=40))
    with c2:
        st.subheader("Estrelas por repositório")
        stars = q(queries.GITSKILLS["stars"])["stars"]
        show(charts.log_hist(stars, "Estrelas (log)", bins=40))

    st.subheader("Linguagens")
    show(charts.bar(q(queries.GITSKILLS["languages"]), "language", "n", "Top linguagens", horizontal=True, top=15))

    st.subheader("Adoção no tempo (amostrada)")
    show(charts.time_series(q(queries.GITSKILLS["adoption_time"]), "d", "n", "Skills por data de primeiro commit"))

# ---------------- SpecMine ----------------
with tab_sm:
    st.header("SpecMine — spec-driven development")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ciclo de vida (spec_role)")
        show(charts.bar(q(queries.SPECMINE["spec_role"]), "spec_role", "n", "spec_role"))
    with c2:
        st.subheader("Ferramentas (spec_tool)")
        show(charts.bar(q(queries.SPECMINE["spec_tool"]), "spec_tool", "n", "spec_tool", horizontal=True, top=15))

    st.subheader("Comprimento do spec (n_lines) + curva normal")
    nl = q(queries.SPECMINE["n_lines"])["n_lines"]
    show(charts.hist_with_normal(nl, "Distribuição de n_lines"))

    st.subheader("Rastreabilidade (spec_links.rel)")
    show(charts.bar(q(queries.SPECMINE["spec_links_rel"]), "rel", "n", "Tipos de referência"))

    st.subheader("Co-change (touches_code)")
    show(charts.bar(q(queries.SPECMINE["touches_code"]), "touches_code", "n", "PRs que mudam spec + código"))

    st.subheader("Adoção no tempo")
    show(charts.time_series(q(queries.SPECMINE["adoption_time"]), "d", "n", "Specs por data de primeiro commit"))

# ---------------- Estatística ----------------
with tab_stats:
    st.header("Estatística descritiva")

    st.subheader("GitSkills — body_chars")
    body = q(queries.GITSKILLS["body_chars"])["body_chars"]
    st.dataframe(pd.DataFrame([stats.describe_numeric(body, "body_chars")]))

    st.subheader("SpecMine — n_lines")
    nl = q(queries.SPECMINE["n_lines"])["n_lines"]
    st.dataframe(pd.DataFrame([stats.describe_numeric(nl, "n_lines")]))

    st.subheader("Inferencial — Mann-Whitney: body_chars (canonical vs other)")
    loc = q(
        """
        SELECT location_class, body_chars FROM gitskills.artifacts
        WHERE dedup_primary = 1 AND body_chars IS NOT NULL
        """
    )
    canon = loc[loc.location_class == "canonical"]["body_chars"]
    other = loc[loc.location_class != "canonical"]["body_chars"]
    st.json(stats.mannwhitney(canon, other))
