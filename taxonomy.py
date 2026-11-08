"""Classify OpenSpec code refs marked done but absent at the anchor (Fase 1).

Reads ``openspec_code_refs`` (task_done=1, anchor_sha not null,
exists_at_anchor=0) and labels each code_path by shape using a three-level
taxonomy:

    level         shapes
    clean_path    relative_ext
    bare_filename bare_ext
    non_file      glob, absolute, relative_noext, bare_noext, empty

Writes ``data/taxonomy_e0.csv`` (one row per ref) and prints the census.

Usage:
    python taxonomy.py
"""

import csv
import os
import re
from pathlib import Path

import duckdb

import db

HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "data"
OUTPUT_CSV = OUTPUT_DIR / "taxonomy_e0.csv"
REF_PARQUET = os.path.join(db.SPECMINE_DATA, "openspec_code_refs.parquet")

GLOB = re.compile(r"[\*\?\[\]\{\}]")
ABS = re.compile(r"^(/|[A-Za-z]:[\\/]|~)")


def classify_path(code_path):
    """Return (level, shape) for a code_path string."""
    if not code_path or not str(code_path).strip():
        return "non_file", "empty"
    s = str(code_path).strip()
    if ABS.match(s):
        return "non_file", "absolute"
    if GLOB.search(s):
        return "non_file", "glob"
    norm = s.lstrip("./").rstrip("/")
    parts = norm.split("/")
    last = parts[-1]
    has_dir = len(parts) > 1
    has_ext = "." in last
    if has_dir and has_ext:
        return "clean_path", "relative_ext"
    if has_dir and not has_ext:
        return "non_file", "relative_noext"
    if not has_dir and has_ext:
        return "bare_filename", "bare_ext"
    return "non_file", "bare_noext"


def main():
    conn = duckdb.connect()
    rows = conn.execute(f"""
        SELECT repo_name, code_path, artifact_path, anchor_sha
        FROM read_parquet('{REF_PARQUET}')
        WHERE task_done = 1 AND anchor_sha IS NOT NULL AND exists_at_anchor = 0
        ORDER BY repo_name, code_path
    """).fetchall()
    conn.close()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    level_counts = {}
    shape_counts = {}
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["repo_name", "code_path", "artifact_path", "anchor_sha",
                         "level", "shape"])
        for repo, code_path, artifact, anchor in rows:
            level, shape = classify_path(code_path)
            writer.writerow([repo, code_path, artifact, anchor, level, shape])
            level_counts[level] = level_counts.get(level, 0) + 1
            shape_counts[shape] = shape_counts.get(shape, 0) + 1

    print(f"Refs classified (exists_at_anchor=0): {len(rows):,}")
    print("\nBy level:")
    for level, n in sorted(level_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {level:14} {n:,}")
    print("\nBy shape:")
    for shape, n in sorted(shape_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {shape:14} {n:,}")
    print(f"\nWritten to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
