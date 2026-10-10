"""DuckDB connection layer.

Attaches the GitSkills SQLite database and registers each SpecMine Parquet
file as a DuckDB view, so both datasets are queryable with plain SQL.
"""
import os
from pathlib import Path

import duckdb

# Dataset paths are resolved relative to the repository root (the parent of
# this project folder), so the project runs on any machine with the same
# layout. Override with the GITSKILLS_DB / SPECMINE_DATA environment variables.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent

GITSKILLS_DB = os.environ.get(
    "GITSKILLS_DB",
    str(_REPO_ROOT / "gitskills-sample" / "agent_skills_sample" / "agent_skills_sample.db"),
)
SPECMINE_DATA = os.environ.get(
    "SPECMINE_DATA",
    str(_REPO_ROOT / "specmine-official" / "data"),
)

SPECMINE_TABLES = [
    "spec_files",
    "spec_file_commits",
    "spec_content_features",
    "spec_links",
    "kiro_files",
    "kiro_repos",
    "kiro_file_commits",
    "kiro_content_features",
    "openspec_artifact_files",
    "openspec_code_refs",
    "repo_trees",
    "pull_requests",
    "pr_files",
]


def get_conn() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection with both datasets attached."""
    conn = duckdb.connect(database=":memory:")

    # Attach GitSkills SQLite (DuckDB's sqlite extension).
    try:
        conn.execute(f"ATTACH '{GITSKILLS_DB}' AS gitskills (TYPE sqlite)")
    except Exception:
        conn.execute("INSTALL sqlite; LOAD sqlite;")
        conn.execute(f"ATTACH '{GITSKILLS_DB}' AS gitskills (TYPE sqlite)")

    # Register each SpecMine Parquet file as a view.
    for table in SPECMINE_TABLES:
        path = os.path.join(SPECMINE_DATA, f"{table}.parquet")
        if os.path.exists(path):
            conn.execute(
                f"CREATE OR REPLACE VIEW {table} AS "
                f"SELECT * FROM read_parquet('{path}')"
            )

    return conn
