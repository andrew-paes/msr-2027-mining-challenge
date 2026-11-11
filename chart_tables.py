"""The table behind each figure, for the dashboard's "data" expander.

Kept out of ``app.py`` so the Streamlit page stays a layout file, and every
loader fails softly: a chart whose dataset is missing simply has no table, and
the page still renders. Each function mirrors the computation in its
``chart_*.py`` counterpart, so the table and the picture cannot disagree.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

import chart_style as cs
import db

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RES = DATA / "classification_results.csv"
A11Y = DATA / "accessibility_requirements.csv"
TAX = DATA / "taxonomy_e0.csv"

BUCKETS = ["0-9", "10-99", "100+"]


def _query(sql: str) -> list[tuple]:
    conn = duckdb.connect(":memory:")
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def _refs() -> str:
    path = Path(db.SPECMINE_DATA) / "openspec_code_refs.parquet"
    return f"read_parquet('{path.as_posix()}')"


def _sample(table: str) -> str:
    path = Path(db.SAMPLE_SPECMINE_DATA) / f"{table}.parquet"
    return f"read_parquet('{path.as_posix()}')"


def _full(table: str) -> str:
    path = Path(db.SPECMINE_DATA) / f"{table}.parquet"
    return f"read_parquet('{path.as_posix()}')"


def _a11y_repos() -> set:
    return set(pd.read_csv(A11Y, usecols=["repo_name"]).repo_name)


# --- chart loaders ----------------------------------------------------------
def m0_sample() -> pd.DataFrame:
    rows = _query(f"SELECT n_lines FROM {_sample('spec_content_features')} "
                  "WHERE n_lines IS NOT NULL")
    series = pd.Series([row[0] for row in rows], name="n_lines")
    return pd.DataFrame([{
        "specs": len(series),
        "mean": round(series.mean(), 1),
        "median": round(series.median(), 1),
        "p99": round(series.quantile(0.99), 1),
        "max": int(series.max()),
    }])


def m0_tools() -> pd.DataFrame:
    rows = _query(f"SELECT spec_tool, COUNT(*) FROM {_sample('spec_files')} "
                  "GROUP BY 1 ORDER BY 2 DESC")
    table = pd.DataFrame(rows, columns=["spec_tool", "spec files (sample)"])
    total = table["spec files (sample)"].sum()
    table["share (%)"] = (table["spec files (sample)"] / total * 100).round(1)
    return table


def m1_sample_full() -> pd.DataFrame:
    rows = []
    for name in ["spec_files", "openspec_code_refs", "spec_links", "pull_requests"]:
        n_sample = _query(f"SELECT COUNT(*) FROM {_sample(name)}")[0][0]
        n_full = _query(f"SELECT COUNT(*) FROM {_full(name)}")[0][0]
        rows.append({"table": cs.word(name), "sample": n_sample, "full": n_full,
                     "sample as % of full": round(n_sample / n_full * 100, 1)})
    return pd.DataFrame(rows)


def m1_tools() -> pd.DataFrame:
    rows = _query(f"SELECT spec_tool, COUNT(*) FROM {_full('spec_files')} "
                  "GROUP BY 1 ORDER BY 2 DESC")
    table = pd.DataFrame(rows, columns=["spec_tool", "spec files (full)"])
    total = table["spec files (full)"].sum()
    table["share (%)"] = (table["spec files (full)"] / total * 100).round(1)
    return table


def m2_pivot() -> pd.DataFrame:
    rows = _query(f"SELECT is_merged, COUNT(*) FROM {_full('pull_requests')} GROUP BY 1")
    table = pd.DataFrame(rows, columns=["is_merged", "pull requests"])
    table["is_merged"] = table["is_merged"].map({1: "1 (merged)", 0: "0 (rejected)"})
    return table


def census() -> pd.DataFrame:
    from taxonomy import classify_spec_role

    rows = _query(
        "SELECT artifact_path, exists_at_anchor FROM " + _refs() +
        " WHERE task_done = 1 AND anchor_sha IS NOT NULL"
    )
    frame = pd.DataFrame(rows, columns=["artifact_path", "exists_at_anchor"])
    frame["role"] = frame["artifact_path"].map(classify_spec_role)
    table = (frame.groupby("role")
             .agg(references=("exists_at_anchor", "size"),
                  missing=("exists_at_anchor", lambda s: int((s == 0).sum())))
             .reset_index())
    table["missing rate (%)"] = (table["missing"] / table["references"] * 100).round(1)
    table["share of the missing (%)"] = (
        table["missing"] / table["missing"].sum() * 100).round(1)
    return table


def m4_discovery() -> pd.DataFrame:
    rows = _query(f"SELECT exists_at_anchor, COUNT(*) FROM {_refs()} GROUP BY 1")
    labels = {0: "0 (absent)", 1: "1 (present)", 2: "2 (ambiguous)", None: "NULL"}
    table = pd.DataFrame(rows, columns=["exists_at_anchor", "references"])
    total = table["references"].sum()
    table["exists_at_anchor"] = table["exists_at_anchor"].map(labels)
    table["share (%)"] = (table["references"] / total * 100).round(2)
    return table.sort_values("references", ascending=False)


def taxonomy() -> pd.DataFrame:
    frame = pd.read_csv(TAX)
    counts = frame["level"].value_counts()
    table = counts.rename_axis("level").reset_index(name="references")
    table["share (%)"] = (table["references"] / table["references"].sum() * 100).round(1)
    return table


def accessibility() -> pd.DataFrame:
    frame = pd.read_csv(A11Y)
    grouped = (frame.groupby("spec_tool")["verifiable"]
               .agg(lines="size", verifiable_lines="sum").reset_index())
    grouped["verifiable (%)"] = (
        grouped["verifiable_lines"] / grouped["lines"] * 100).round(1)
    return (grouped.sort_values("verifiable (%)", ascending=False)
            [["spec_tool", "lines", "verifiable_lines", "verifiable (%)"]])


def m7_calibration() -> pd.DataFrame:
    from taxonomy import classify_path

    rows = _query(
        "SELECT code_path, resolved_path FROM " + _refs() +
        " WHERE task_done = 1 AND anchor_sha IS NOT NULL AND exists_at_anchor = 1 "
        "AND resolved_path IS NOT NULL AND resolved_path != ''"
    )
    records = []
    for code_path, resolved_path in rows:
        _prefix, shape = classify_path(code_path)
        records.append((shape, resolved_path != code_path))
    frame = pd.DataFrame(records, columns=["path shape", "differs"])
    table = (frame.groupby("path shape")
             .agg(resolved=("differs", "size"), differs=("differs", "sum"))
             .reset_index())
    table["differs (%)"] = (table["differs"] / table["resolved"] * 100).round(1)
    return table.sort_values("differs (%)", ascending=False)


def outcomes() -> pd.DataFrame:
    frame = pd.read_csv(RES)
    counts = frame["classification"].value_counts()
    table = counts.rename_axis("classification").reset_index(name="references")
    table["share (%)"] = (table["references"] / len(frame) * 100).round(1)
    table["classification"] = table["classification"].map(
        lambda key: cs.CLASS_LABEL.get(key, key))
    return table


def by_bucket() -> pd.DataFrame:
    frame = pd.read_csv(RES)
    cross = pd.crosstab(frame["star_bucket"], frame["classification"]).reindex(BUCKETS)
    cross["total"] = cross.sum(axis=1)
    return cross.reset_index()


def bridge() -> pd.DataFrame:
    frame = pd.read_csv(RES)
    frame["has_a11y"] = frame.repo_name.isin(_a11y_repos())
    rate = (frame.groupby(["star_bucket", "has_a11y"])["classification"]
            .apply(lambda s: (s == "never").mean() * 100).unstack())
    rate.columns = ["without accessibility (%)", "with accessibility (%)"]
    return rate.reindex(BUCKETS).round(1).reset_index()


def bridge_repo() -> pd.DataFrame:
    frame = pd.read_csv(RES)
    frame["has_a11y"] = frame.repo_name.isin(_a11y_repos())
    per_repo = (frame.groupby("repo_name")
                .agg(references=("classification", "size"),
                     never_rate=("classification", lambda s: (s == "never").mean() * 100),
                     has_a11y=("has_a11y", "first"))
                .reset_index())
    per_repo["accessibility requirements"] = per_repo["has_a11y"].map(
        {True: "with", False: "without"})
    per_repo["never rate (%)"] = per_repo["never_rate"].round(1)
    return (per_repo.sort_values(["accessibility requirements", "never_rate"],
                                 ascending=[False, False])
            [["repo_name", "accessibility requirements", "references", "never rate (%)"]])


LOADERS = {
    "chart_m0_sample.png": m0_sample,
    "chart_m0_tools.png": m0_tools,
    "chart_m1_sample_full.png": m1_sample_full,
    "chart_m1_tools.png": m1_tools,
    "chart_m2_pivot.png": m2_pivot,
    "chart_census.png": census,
    "chart_m4_discovery.png": m4_discovery,
    "chart_taxonomy.png": taxonomy,
    "chart_accessibility.png": accessibility,
    "chart_m7_calibration.png": m7_calibration,
    "chart_outcomes.png": outcomes,
    "chart_by_bucket.png": by_bucket,
    "chart_bridge.png": bridge,
    "chart_bridge_repo.png": bridge_repo,
}


def table_for(png_name: str) -> pd.DataFrame | None:
    """The table behind ``png_name``, or ``None`` when the dataset is absent."""
    loader = LOADERS.get(png_name)
    if loader is None:
        return None
    try:
        return loader()
    except Exception as exc:  # missing dataset, unreadable parquet, ...
        print(f"chart_tables: no table for {png_name}: {exc}")
        return None
