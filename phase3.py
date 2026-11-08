"""Phase 3 — classify "done but missing" references (renames / timing).

Single script: materialize frame -> stratified sample -> clone -> classify.

Classification buckets:
    renamed                 path renamed (git --follow detects R)
    created_later           first commit after the anchor
    never                   never committed on any branch (ALL_BRANCHES=True)
    deleted_before_anchor   committed then removed before the anchor
    alternative_path        same basename at a different path in the anchor tree
    other                   unresolvable (anchor missing / ambiguous)

Decision (documented): ALL_BRANCHES=True — "never" means never committed on
ANY branch; unmerged feature branches count as "implemented" (conservative).

Note: the taxonomy column is ``shape``, accessed as ``df["shape"]`` (bracket
notation), because ``df.shape`` is the DataFrame's (rows, cols) attribute.

Usage:
    python phase3.py --draw-only          # materialize frame + draw sample
    python phase3.py --repos a,b,c        # pilot: classify only these repos
    python phase3.py                      # full run over the sample
"""
import argparse
import posixpath
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

import db

HERE = Path(__file__).resolve().parent
TAXONOMY = HERE / "data" / "taxonomy_e0.csv"
SPEC_FILES = Path(db.SPECMINE_DATA) / "spec_files.parquet"
FRAME_CSV = HERE / "data" / "frame_phase3.csv"
SAMPLE_CSV = HERE / "data" / "phase3_sample.csv"
OUT_CSV = HERE / "data" / "phase3_results.csv"
CLONE_DIR = HERE / "clones"
SEED = 42

ALL_BRANCHES = True
TARGETS = {"0-9": 50, "10-99": 45, "100+": 57}  # 100+ = census


def materialize_frame():
    conn = duckdb.connect()
    frame = conn.execute(f"""
        SELECT t.repo_name,
               COUNT(*)                                   AS n_missing_refs,
               COUNT(DISTINCT t.artifact_path)            AS n_tasks_md,
               COUNT(DISTINCT t.code_path)                AS n_distinct_files,
               COALESCE(MAX(s.repo_stars), 0)             AS repo_stars,
               COALESCE(MAX(s.repo_language), 'unknown')  AS repo_language,
               COALESCE(MAX(s.repo_is_template), 0)       AS is_template,
               COALESCE(MAX(s.repo_fork), 0)              AS is_fork
        FROM read_csv_auto('{TAXONOMY.as_posix()}') t
        LEFT JOIN read_parquet('{SPEC_FILES.as_posix()}') s ON s.repo_name = t.repo_name
        WHERE t.shape = 'relative_ext'
        GROUP BY t.repo_name
    """).df()
    conn.close()
    frame["star_bucket"] = pd.cut(
        frame["repo_stars"], bins=[-1, 9, 99, float("inf")],
        labels=["0-9", "10-99", "100+"], right=True,
    )
    frame.to_csv(FRAME_CSV, index=False)
    print(f"frame materialized: {len(frame)} repos")
    print(frame.groupby("star_bucket")["repo_name"].count().to_string())
    return frame


def allocate_proportional(counts, n):
    """Largest-remainder allocation -> sums exactly to n."""
    total = counts.sum()
    if total == 0 or n <= 0:
        return pd.Series(dtype=int)
    raw = counts * n / total
    seats = raw.astype(int).copy()
    remaining = int(n - seats.sum())
    if remaining > 0:
        order = (raw - seats).sort_values(ascending=False)
        for lang in order.index[:remaining]:
            seats[lang] += 1
    return seats[seats > 0]


def draw_sample(frame):
    parts = []
    for bucket, n in TARGETS.items():
        pool = frame[frame.star_bucket == bucket]
        n = min(n, len(pool))
        alloc = allocate_proportional(pool.repo_language.value_counts(), n)
        for lang, k in alloc.items():
            parts.append(pool[pool.repo_language == lang].sample(k, random_state=SEED))
    sample = pd.concat(parts).drop_duplicates("repo_name")
    sample.to_csv(SAMPLE_CSV, index=False)
    print(f"sample drawn: {len(sample)} repos")
    print(sample.groupby("star_bucket")["repo_name"].count().to_string())
    return sample


def clone_repo(repo_name, timeout=600, retries=2):
    dest = CLONE_DIR / repo_name.replace("/", "__")
    # already cloned and complete?
    check = subprocess.run(["git", "-C", str(dest), "rev-parse", "--verify", "HEAD"],
                           capture_output=True, text=True)
    if check.returncode == 0:
        return str(dest)
    # clean any partial clone before (re)cloning
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    for attempt in range(retries + 1):
        try:
            subprocess.run(
                ["git", "clone", "--quiet",
                 f"https://github.com/{repo_name}.git", str(dest)],
                capture_output=True, text=True, timeout=timeout, check=True,
            )
            return str(dest)
        except Exception as e:
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            if attempt == retries:
                print(f"CLONE FAIL {repo_name}: {type(e).__name__}")
                return None
            time.sleep(5)
    return None


def git(repo_dir, *args):
    r = subprocess.run(["git", "-C", repo_dir, *args],
                       capture_output=True, text=True)
    return r.stdout.strip()


def resolve_code_path(code_path, artifact_path):
    p = code_path.strip()
    if p.startswith("./") or p.startswith("../"):
        base = posixpath.dirname(artifact_path)
        return posixpath.normpath(posixpath.join(base, p))
    return p


class Classifier:
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir
        self._tree = {}

    def tree_at(self, anchor_sha):
        if anchor_sha not in self._tree:
            self._tree[anchor_sha] = git(
                self.repo_dir, "ls-tree", "-r", "--name-only", anchor_sha)
        return self._tree[anchor_sha]

    def basename_match(self, code_path, anchor_sha):
        base = posixpath.basename(code_path)
        if not base:
            return None
        for line in self.tree_at(anchor_sha).splitlines():
            if posixpath.basename(line) == base and line != code_path:
                return line
        return None

    def classify(self, code_path, artifact_path, anchor_sha):
        cp = resolve_code_path(code_path, artifact_path)
        refs = ["--all"] if ALL_BRANCHES else []

        anchor_ts = git(self.repo_dir, "show", "-s", "--format=%cI", anchor_sha)
        anchor_t = datetime.fromisoformat(anchor_ts) if anchor_ts else None

        adds = git(self.repo_dir, "log", *refs, "--diff-filter=A",
                   "--format=%H %cI", "--", cp)
        follow = git(self.repo_dir, "log", *refs, "--follow", "--name-status",
                     "--format=%H %cI", "--", cp)

        if re.search(r"^R\d+\s+", follow, re.M):
            return "renamed"

        if not adds:
            return "never"

        first = adds.splitlines()[-1].split()
        first_ts = first[1] if len(first) > 1 else None
        if anchor_t and first_ts and datetime.fromisoformat(first_ts) > anchor_t:
            return "created_later"

        dels = git(self.repo_dir, "log", *refs, "--diff-filter=D",
                   "--format=%H %cI", "--", cp)
        if dels and anchor_t:
            for line in dels.splitlines():
                parts = line.split()
                if len(parts) >= 2 and datetime.fromisoformat(parts[1]) <= anchor_t:
                    return "deleted_before_anchor"

        return "other"  # anchor missing, or added-before-anchor without deletion/rename


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", help="comma-separated repos (pilot)")
    ap.add_argument("--draw-only", action="store_true",
                    help="materialize frame + draw sample, then stop")
    ap.add_argument("--clone-only", action="store_true",
                    help="materialize frame + draw sample + clone all sample repos, then stop")
    args = ap.parse_args()

    if not FRAME_CSV.exists():
        frame = materialize_frame()
    else:
        frame = pd.read_csv(FRAME_CSV)
        print(f"frame loaded: {len(frame)} repos")

    if args.draw_only:
        if not SAMPLE_CSV.exists():
            draw_sample(frame)
        return

    if args.repos:
        sample = pd.DataFrame({"repo_name": [r.strip() for r in args.repos.split(",")]})
        print(f"pilot repos: {list(sample.repo_name)}")
    elif not SAMPLE_CSV.exists():
        sample = draw_sample(frame)
    else:
        sample = pd.read_csv(SAMPLE_CSV)
        print(f"sample loaded: {len(sample)} repos")

    if args.clone_only:
        CLONE_DIR.mkdir(parents=True, exist_ok=True)
        ok, failed = 0, []
        for i, repo in enumerate(sample.repo_name, 1):
            if clone_repo(repo):
                ok += 1
            else:
                failed.append(repo)
            if i % 10 == 0 or i == len(sample):
                print(f"cloned {i}/{len(sample)} repos; {len(failed)} failures", flush=True)
        print(f"\nclone-only done: {ok} ok, {len(failed)} failures")
        for f in failed:
            print(f"  - {f}")
        return

    tax = pd.read_csv(TAXONOMY)
    e0 = tax[tax["shape"] == "relative_ext"]

    CLONE_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    failed = []
    for i, repo in enumerate(sample.repo_name, 1):
        repo_dir = clone_repo(repo)
        if not repo_dir:
            failed.append(repo)
            continue
        clf = Classifier(repo_dir)
        for _, r in e0[e0.repo_name == repo].iterrows():
            cls = clf.classify(r.code_path, r.artifact_path, r.anchor_sha)
            alt = None
            if cls in ("never", "deleted_before_anchor", "other"):
                alt = clf.basename_match(r.code_path, r.anchor_sha)
                if alt:
                    cls = "alternative_path"
            rows.append({
                "repo_name": repo,
                "code_path": r.code_path,
                "artifact_path": r.artifact_path,
                "anchor_sha": r.anchor_sha,
                "classification": cls,
                "alt_path": alt or "",
            })
        if i % 10 == 0 or i == len(sample):
            print(f"processed {i}/{len(sample)} repos; {len(rows)} refs; {len(failed)} failures", flush=True)

    out = pd.DataFrame(rows, columns=["repo_name", "code_path", "artifact_path",
                                      "anchor_sha", "classification", "alt_path"])
    meta = frame[["repo_name", "star_bucket"]].drop_duplicates("repo_name")
    out = out.merge(meta, on="repo_name", how="left")
    out["star_bucket"] = out["star_bucket"].fillna("unknown")
    out.to_csv(OUT_CSV, index=False)

    print(f"\nresults: {len(out)} refs -> {OUT_CSV}")
    print(f"clone failures: {len(failed)}")
    for f in failed:
        print(f"  - {f}")
    print("\n=== Classification distribution (refs) ===")
    print(out.classification.value_counts().to_string())
    print("\n=== class x star_bucket: refs ===")
    print(pd.crosstab(out.classification, out.star_bucket).to_string())
    print("\n=== class x star_bucket: repos ===")
    print(pd.crosstab(out.classification, out.star_bucket,
                      values=out.repo_name, aggfunc="nunique").to_string())


if __name__ == "__main__":
    main()

