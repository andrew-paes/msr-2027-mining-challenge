"""SQL queries over the GitSkills and SpecMine tables (see tables.md)."""

GITSKILLS = {
    "copy_distribution": """
        SELECT copies, COUNT(*) AS n_contents
        FROM (
            SELECT file_sha, COUNT(*) AS copies
            FROM gitskills.artifacts
            GROUP BY file_sha
        )
        GROUP BY copies
        ORDER BY copies
    """,
    "location_class": """
        SELECT location_class, COUNT(*) AS n
        FROM gitskills.artifacts
        GROUP BY location_class
        ORDER BY n DESC
    """,
    "body_chars": """
        SELECT body_chars
        FROM gitskills.artifacts
        WHERE dedup_primary = 1 AND body_chars IS NOT NULL
    """,
    "skills_per_repo": """
        SELECT repo_full_name, COUNT(*) AS n
        FROM gitskills.artifacts
        GROUP BY repo_full_name
    """,
    "stars": """
        SELECT stars FROM gitskills.repos WHERE stars IS NOT NULL
    """,
    "languages": """
        SELECT language, COUNT(*) AS n
        FROM gitskills.repos
        GROUP BY language
        ORDER BY n DESC
    """,
    "scripts_refs": """
        SELECT has_scripts, has_references, COUNT(*) AS n
        FROM gitskills.artifacts
        WHERE dedup_primary = 1
        GROUP BY has_scripts, has_references
    """,
    "frontmatter": """
        SELECT frontmatter_valid, COUNT(*) AS n
        FROM gitskills.artifacts
        WHERE dedup_primary = 1
        GROUP BY frontmatter_valid
    """,
    "adoption_time": """
        SELECT DATE(first_commit_at) AS d, COUNT(*) AS n
        FROM gitskills.artifacts
        WHERE first_commit_at IS NOT NULL
        GROUP BY d
        ORDER BY d
    """,
}

SPECMINE = {
    "spec_role": """
        SELECT spec_role, COUNT(*) AS n
        FROM spec_files
        GROUP BY spec_role
        ORDER BY n DESC
    """,
    "spec_tool": """
        SELECT spec_tool, COUNT(*) AS n
        FROM spec_files
        GROUP BY spec_tool
        ORDER BY n DESC
    """,
    "n_lines": """
        SELECT n_lines, n_words
        FROM spec_content_features
        WHERE n_lines IS NOT NULL
    """,
    "spec_links_rel": """
        SELECT rel, COUNT(*) AS n
        FROM spec_links
        GROUP BY rel
        ORDER BY n DESC
    """,
    "touches_code": """
        SELECT touches_code, COUNT(*) AS n
        FROM pull_requests
        GROUP BY touches_code
    """,
    "repo_stars": """
        SELECT repo_stars FROM spec_files WHERE repo_stars IS NOT NULL
    """,
    "adoption_time": """
        SELECT DATE(file_first_commit_at) AS d, COUNT(*) AS n
        FROM spec_files
        WHERE file_first_commit_at IS NOT NULL AND file_first_commit_at != ''
        GROUP BY d
        ORDER BY d
    """,
    "commits_per_spec": """
        SELECT file_total_commits FROM spec_files WHERE file_total_commits IS NOT NULL
    """,
}
