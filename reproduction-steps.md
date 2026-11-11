# Reproduction Steps: Research Log

> Companion: `reasoning.md` explains the line of reasoning: the *why* behind each milestone (M0–M8), with the charts and the decisions. Each **M#** section below is the *how* (the recipe) of the same-numbered milestone in `reasoning.md`.

This document is written like a recipe: first the ingredients (the data sources, tools, and access I needed, and why each one was necessary), then the method (the concrete steps I performed, in order). Each step is told in prose and is followed by a bullet list of the data source, the commands, and the output, so that another person can reproduce the analysis and regenerate every result. The installation and configuration commands live in the README; the scripts live in this repository.

The MSR 2027 challenge offers two datasets: **GitSkills** (agent skills) and **SpecMine** (spec-driven development). I explored both, then scoped the study to SpecMine: its traceability question (does a spec task marked *done* actually ship as code?) was both the most novel and the most data-supported. GitSkills is out of scope here and appears only as the scoped-out alternative; every ingredient and step below concerns SpecMine.

## Reproduce the milestones (command checklist)

Each milestone is a standalone script that prints its number and, where relevant, the chart it uses. Run them in order; the expected result is the comment on each line:

```powershell
py m0_sample_stats.py   # skew 11.4
py m1_sample_full.py    # 6.1% specs / 89% PRs
py m2_pivot.py          # 5,992 merged / 0 rejected
py m3_census.py         # 34,227 = 10.3%; 17.7% change_proposal vs 9.0% archived
py m4_discovery.py      # 0 / 1 / 2 / NULL
py m5_taxonomy.py       # 91% real
py m6_accessibility.py  # 27.1%
py m7_calibration.py    # 15.2% vs 94.8%
py m8_bridge.py  # 54.5% never / inversion / a11y
py m9_discovery_summary.py  # the 14 charts, in M0 -> M8 order
```

Regenerate every chart (and the CSVs that feed them) with `make charts`; pre-clone the clone-classify sample with `make clone`; run the full clone-classify classification with `make classify`; re-check the figure rules (alt text, dpi, contrast, no frozen numbers) with `make check`. The README "Derivation pipeline & reproducibility" records which stages are deterministic and which are not (the git-clone stage is not reproducible across time).

## Ingredients

**SpecMine Parquet files** (`data/*.parquet`). The spec-driven-development dataset, with `spec_files`, `spec_content_features`, `spec_links`, `openspec_artifact_files`, `openspec_code_refs`, `pull_requests`, `pr_files`, and the Kiro tables. It was necessary as the source of the specs, the tasks they declare, and the code references that link them. Two releases are used: the **v1.1 sample** (`SAMPLE_SPECMINE_DATA`) for the M0/M1 steps, and the **v1.0 full** (Zenodo, 10 tables, `SPECMINE_DATA`) for everything from M2 onward.

**SpecMine raw spec text** (`specs.jsonl`). The Parquet tables store metadata but not the full Markdown body of each spec; the body lives in this JSONL file, keyed by `file_url_sha16`. It was necessary because the accessibility analysis could not rely on any pre-computed feature, so the text itself had to be mined.

**DuckDB.** A single query engine that reads the Parquet files directly, letting me write plain SQL over the dataset without a separate ETL step.

**Python 3.9+ with pandas, scipy, streamlit, and matplotlib.** pandas to manipulate tabular data, scipy for the descriptive statistics and the Shapiro-Wilk test, streamlit for the dashboard, and matplotlib for the charts. Each was necessary for a specific part of the analysis.

**git.** clone-classify clones each sampled repository and inspects its history locally (`git log`, `git ls-tree`) rather than through the GitHub API, so the classification does not depend on API rate limits.

## Method

### M0: Sample stats: strongly right-skewed data

To establish the shape of the data before any inference, I summarised the SpecMine v1.1 sample. I wrote `m0_sample_stats.py`, which reads `spec_content_features.n_lines` through DuckDB and writes `data/sample_stats.csv`. The spec length `n_lines` has a mean of 90.8 and a median of 56.0, and is strongly right-skewed (skew 11.4, computed on the full sample; the Shapiro-Wilk test is limited to n ≤ 5000), with a Shapiro-Wilk p-value near zero. The data is strongly right-skewed and far from normal, which is why every later test is non-parametric and why I never assumed normality.

**Data and commands:**

- **Data source:** the SpecMine v1.1 sample (`spec_content_features`).
- `py m0_sample_stats.py`: prints the summary and writes `data/sample_stats.csv`.
- Output: `data/sample_stats.csv`; chart `data/chart_m0_sample.png`.

### M1: Sample vs full: the sample is a thin slice

Before running the census, I checked whether the v1.1 sample is representative of the full v1.0 release. I wrote `m1_sample_full.py`, which counts rows in four tables in both releases through DuckDB. The sample holds 28,583 specs (6.1% of the full 470,795) and 7.0% of the code references (30,435 vs 435,401) and 10.8% of the traceability links (261,032 vs 2,421,323); but its pull-request layer is nearly complete at 5,335 (89.0% of the full 5,992). The sample is a thin, star-curated slice of specs yet almost complete for pull requests, so the census and every later population-level claim had to run on the full release, not the sample. The composition also diverges: 51.5% of the sample's specs are `archived` versus 33.3% of the full's, so the star-curated slice over-represents archived specs.

**Data and commands:**

- **Data source:** the v1.1 sample and the v1.0 full (`spec_files`, `openspec_code_refs`, `spec_links`, `pull_requests`).
- `py m1_sample_full.py`: prints sample, full, and the percentage for each table.
- Output: chart `data/chart_m1_sample_full.png`.

### M2: The pivot: scope to the traceability question

With three candidate questions on the table: Q1 (does a checked-off task actually ship as code?), Q2 (what accessibility requirements do specs state, and how verifiable are they?), and Q3 (do humans reject spec changes in review?). I checked which one the data could actually answer. I wrote `m2_pivot.py`, which reads `pull_requests.is_merged`: all 5,992 spec-touching pull requests are merged (`is_merged = 1`), so there are no rejected or closed pull requests to observe, and the review question (Q3) cannot be answered from this corpus. Q1, traceability, is the one the data supports, and it became the study.

**Data and commands:**

- **Data source:** `pull_requests` (SpecMine v1.0).
- `py m2_pivot.py`: prints the `is_merged` distribution.
- Output: chart `data/chart_m2_pivot.png`.

### M3: Census: the gap exists at scale

To measure the traceability gap at population level, I wrote `m3_census.py`, which groups `openspec_code_refs` by `exists_at_anchor` among the references marked done with a resolvable anchor (`task_done = 1 AND anchor_sha IS NOT NULL`). Of the 332,168 such references, 34,227 (10.3%) are marked done but have no code at the anchor commit (`exists_at_anchor = 0`); 297,822 (89.7%) are present, and 119 (0.0%) are ambiguous (`exists_at_anchor = 2`). The gap is a population-level phenomenon, not a sample artifact.

I also asked where the gap concentrates, by recovering each reference's spec lifecycle role from the directory of its tasks.md (spec_role is a pure function of the path: spec_files stores only spec.md, never tasks.md). The missing rate is 17.7% for active changes (9,062 of 51,174) versus 9.0% for archived changes (25,159 of 280,869); living has no references because tasks.md exists only under openspec/changes/. So the gap is a property of the change-proposal workflow: it is largest while a change is still open and smaller once it is archived.

**Data and commands:**

- **Data source:** `openspec_code_refs` (SpecMine v1.0).
- `py m3_census.py`: prints the `exists_at_anchor` distribution.
- Output: chart `data/chart_census.png`.

### M4: Discovery: `exists_at_anchor` is not binary

While running the census I noticed the outcome column is not the binary it is documented to be. I wrote `m4_discovery.py`, which groups `openspec_code_refs` by `exists_at_anchor` over the whole table: it takes 0 (51,979), 1 (361,083), 2 (130, in five repositories), and NULL (22,209); NULL occurs exactly when `anchor_sha` is NULL (all 22,209 NULL rows have a NULL anchor). The data dictionary describes the column only as "1 if existed", so documenting its actual 0/1/2/NULL semantics is itself a data-quality contribution.

**Data and commands:**

- **Data source:** `openspec_code_refs` (SpecMine v1.0).
- `py m4_discovery.py`: prints the `exists_at_anchor` distribution and the NULL/anchor correlation.
- Output: chart `data/chart_m4_discovery.png`.

### M5: Taxonomy: real file or path noise

Before treating "done but missing" as genuine absence, I had to rule out malformed paths. I wrote `taxonomy.py`, whose `classify_path()` labels each `task_done = 1 AND anchor_sha IS NOT NULL AND exists_at_anchor = 0` code path by shape (clean relative path (`relative_ext`), bare filename (`bare_ext`), or non-file (`glob`, `absolute`, `relative_noext`, `bare_noext`, `empty`)) writing `data/taxonomy_e0.csv`. Of the 34,227 references, 17,799 are clean relative paths and 13,326 are bare filenames (91% are genuine file references) while 3,102 are non-file (2,041 globs, 807 extension-less, 254 absolute). The "missing" is real absence, not path noise.

**Data and commands:**

- **Data source:** `openspec_code_refs` (SpecMine v1.0).
- `py m5_taxonomy.py`: prints the three-level split (regenerates `taxonomy_e0.csv` via `taxonomy.py` if missing).
- Output: `data/taxonomy_e0.csv`; chart `data/chart_taxonomy.png`.

### M6: Accessibility: verifiable requirements

Because none of the 39 structural features is an accessibility flag, I mined the raw spec text. I created `extract_accessibility.py`, whose `main()` function streams `specs.jsonl` and whose `extract_lines()` helper splits each spec into non-empty lines, checking every line against an `ACCESSIBILITY_PATTERNS` list: a vocabulary of high-precision terms grouped into categories (WCAG, Section 508, and ADA for compliance; screen reader, assistive technology, alt text, and ARIA for assistive technology; keyboard navigation and focus management for interaction; contrast ratio and colorblind for visual; a11y and accessibility for general), each written as a word-boundary regular expression. I matched `aria-` and the uppercase `ARIA` instead of the bare substring aria, to avoid matching words like variables and criteria. The spec text is read from a path resolved relative to the repository root, overridable with the `SPECMINE_SPECS_JSONL` environment variable. I ran it with the command `py extract_accessibility.py`, which wrote each match to `data/accessibility_requirements.csv` with the repository, path, tool, category, matched term, and requirement text. This produced 97,883 requirement lines across 10,717 repositories at full scale, each annotated with a per-line "verifiable" flag (an imperative `shall`/`must` or a measurable threshold such as a contrast ratio, a WCAG level, or a number with a unit); 27.1% (26,529) are verifiable. Formal spec tools state verifiable accessibility requirements far more often: openspec 37.0% and speckit 35.6% versus docs_embedded 8.9% and root_bare 12.9%. To keep precision, "ADA" is matched only as the full phrase "Americans with Disabilities Act" (a bare `ADA` collides with the Cardano token), and bare "caption"/"transcript" were dropped (they are dominated by UI labels and AI-session transcripts).

**Data and commands:**

- **Data source:** the raw spec text in `specs.jsonl`; the full version is `specs.jsonl.gz` on Zenodo, not on Hugging Face.
- `py extract_accessibility.py`: mined the text and wrote the matches.
- `py m6_accessibility.py`: prints the verifiable share by tool.
- Output: `data/accessibility_requirements.csv`; chart `data/chart_accessibility.png`.
- To regenerate from the full dataset: decompress the full `specs.jsonl.gz`, set `SPECMINE_SPECS_JSONL` to its path, and re-run the command.

### M7: Calibration: how much is rename

Before attributing absence to non-implementation, I measured how much of the "missing" could simply be a path written differently from where the code actually lives. I wrote `m7_calibration.py`, which reuses `classify_path()` from `taxonomy.py` on the references that DO resolve (`exists_at_anchor = 1`) and compares each `resolved_path` to its written `code_path`. Among clean relative paths, 15.2% resolve at a different path than written: the rename/normalization burden the next layer must recover. The 94.8% for bare filenames is tautological (a bare name always gains a directory when resolved), so it is reported only as a caution, never as a finding.

**Data and commands:**

- **Data source:** `openspec_code_refs` (SpecMine v1.0), `resolved_path` vs `code_path` for `exists_at_anchor = 1`.
- `py m7_calibration.py`: prints the mismatch rate by path shape.
- Output: chart `data/chart_m7_calibration.png`.

### M8: Design the clone-classify sample (never / deleted / renamed)

To estimate how many of the "done but missing" references are truly never implemented (after accounting for renames, alternative paths, and code that landed later) I scoped the population to the cleanest candidates and designed a stratified sample. The population is the 17,799 references whose `code_path` is a clean relative path with a file extension (`relative_ext`) and whose `exists_at_anchor` is 0, spanning 2,536 repositories, 6,834 `tasks.md` files, and 15,984 distinct paths. I left the 13,326 bare filenames (`bare_ext`) out of this layer because a bare name does not say where the file should live, so an absent match carries uncertainty about whether the resolver searched the whole tree; they are reported as a limitation. I chose the repository as the sampling unit rather than the reference, because the expensive work (reconstructing the `tasks.md` history and finding each path's first commit) is per repository and per artifact: the same `tasks.md` serves several references, so sampling references would spread the cost across repositories and repeat work, while sampling repositories and analysing all their missing references is cheaper and respects the nesting of references inside repositories that already motivates the hierarchical model. I stratified by maturity and language. Maturity (repository stars, bucketed 0–9, 10–99, and 100+) separates serious projects from tutorials and abandoned repositories: 92% of repositories sit in the 0–9 bucket, so without stratification the sample would be dominated by throwaway repositories where "never implemented" is the expected outcome of abandonment rather than a real gap. Language controls ecosystem bias, since path conventions differ by ecosystem (for example `.ts` versus `.tsx`, `src/` versus `lib/`) and could confound the rate. I did not stratify by `spec_tool`, because `openspec_code_refs` is OpenSpec-only, so the tool is constant. I also counted forks and templates: there are no forks and only 18 templates (0.7%), so they can be reported separately or excluded with little effect. For execution I cloned each repository once and used local git rather than the GitHub API (`git log -p -- <tasks.md>` reconstructs when each checkbox changed, and `git log --all --diff-filter=A -- <code_path>` finds the first commit of a path, with `git log --follow` for renames), which avoids the API rate limit (only the clone uses the network) and provides rename detection the API does not offer cheaply. I ran a feasibility test on three repositories, one per star bucket, to measure clone time and per-reference analysis time, then drew a stratified sample of 152 repositories (a census of the 57 repositories with 100+ stars, 45 of the 147 with 10–99, and 50 of the 2,332 with 0–9), oversampling the serious tier so the paper can report the "never implemented" rate by maturity. The draw is random but reproducible. Each stratum is a star bucket crossed with a language. The bucket quotas are fixed by design (TARGETS: 50, 45, and 57 repositories, 152 in total); within each bucket, `allocate_proportional()` splits the quota among languages in proportion to the number of repositories per language, using a largest-remainder rule so the seats sum exactly to the quota; and within each (bucket, language) stratum, `draw_sample()` picks repositories at random without replacement with `DataFrame.sample(k, random_state=SEED)` (`SEED = 42`). The 100+ bucket is a census (57 of 57), while the 10–99 and 0–9 buckets are sampled (45 of 147, about 30.6%; 50 of 2,332, about 2.1%). Because the seed is fixed, the same `taxonomy_e0.csv` frame always yields the same 152 repositories, and the drawn sample is cached in `data/classification_sample.csv` and reloaded on later runs instead of being redrawn. The only time-dependent step is the clone, not the sampling: GitHub is mutable (repositories get deleted, renamed, or force-pushed), so re-cloning from scratch at a later date can differ, while re-running `make classify` on the frozen clones under `clones/` reproduces the classification exactly.

**Data and commands:**

- **Data source:** `data/taxonomy_e0.csv` joined to `spec_files` (`repo_stars`, `repo_language`, `repo_is_template`, `repo_fork`).
- Stratification frame: 17,799 refs / 2,536 repos; by stars 0–9 (2,332 repos, 15,945 refs), 10–99 (147 repos, 1,162 refs), 100+ (57 repos, 692 refs); top languages TypeScript (1,021 repos), Python (464), Go (196), Rust (169), JavaScript (148).
- Feasibility test (done): `git clone` of three repositories (one per star bucket) took 4.6–50 seconds each; `git log -p -- <tasks.md>` reconstructs the tasks.md history, and `git log --all --diff-filter=A -- <code_path>` returns empty when the file was never committed. 113 of the 17,799 relative paths (0.6%) carry a `./` or `../` prefix (artifact-relative rather than root-relative) and need resolving against the tasks.md directory.
- Pilot classification (done, 3 repos / 423 refs): created_later 186 (44%), never 171 (40%), deleted_before_anchor 53 (13%), renamed 10 (2%), other 3 (0.7%), alternative_path 0. "created_later" dominating suggests implementation lag more than abandonment: a finding worth foregrounding. Fix: a file deleted in the anchor commit itself (same timestamp) is "deleted_before_anchor" (the check uses `<=`), not "other".
- Full sample (done, 152 repos / 1,298 refs across 137 successfully cloned repos): never 707 (54%), deleted_before_anchor 383 (30%), created_later 120 (9%), renamed 53 (4%), other 35 (3%), alternative_path 0. The pilot's "created_later 44%" was an outlier of three dense repositories; at full scale "never" dominates, so 84% (never + deleted) are genuinely absent from the final code at the anchor, and "created_later" is a minority (implementation lag, not the main story). 15 repositories failed to clone (deleted/private since the July 2026 snapshot: a survivorship bias, concentrated in large repos); "other" (35) is concentrated in the 100+ bucket (30), consistent with force-pushed anchors; "alternative_path" stayed 0, so the ~15% path-normalization seen among resolving references (exists=1) does not carry over to non-resolving ones (exists=0).
- Chart (done): `python chart_by_bucket.py` writes `data/chart_by_bucket.png`, a stacked bar of the classes by star bucket with `never` (red) and `deleted_before_anchor` (orange) highlighted, making the maturity inversion (R3) visible.
- Commands: `py clone_classify.py --clone-only` (pre-clone), `py clone_classify.py` (classify), or `make clone` / `make classify`.
- Reproducibility: the classification is consolidated in the committed `data/classification_results.csv` (repo_name, code_path, anchor_sha, classification, alt_path, star_bucket), so the aggregate numbers reproduce without re-cloning; the clones under `clones/` (gitignored, regenerable via `make clone`) are only needed to regenerate that CSV from scratch. The sample draw is seeded (`SEED = 42`); the clone is the only time-dependent step. The CSV records each reference's classification **outcome**, not the raw git evidence behind it: the commit SHAs that first added, deleted, or renamed a path are discarded by `classify()`, so auditing an individual classification (especially `never`, which is negative evidence: no commit adds the path) requires re-running `clone_classify.py` with the clones.

## M8: Results (clone-classify outcomes)

**R1: Overall distribution.** Of the 1,298 classified "done but missing" references (137 repositories cloned successfully), the outcomes are: never 54.5% (the task was checked off but the referenced code file was never committed on any branch), deleted_before_anchor 29.5% (the file was written and then removed before the anchor commit), created_later 9.2% (the file appeared in a commit after the anchor), renamed 4.1%, other 2.7% (anchor missing due to force-push), and alternative_path 0%. The central result: 84% of "done but missing" references are genuinely absent at the anchor commit: either never written (54.5%) or written then removed (29.5%). Implementation lag (created_later) accounts for only 9.2%.

**R2: Robustness to nesting.** References are nested in repositories, so a few dense repositories could skew the aggregate. The median per-repository never rate is 66.7% (mean 55.7%), above the raw 54.5%, and never appears in 102 of 137 repositories (74%). Both metrics are reported as complementary: 54.5% estimates the reference population, 66.7% describes the typical repository and confirms the result is not driven by dense outliers.

**R3: The composition inverts with maturity.** By star bucket:

| Bucket | never | deleted | created_later | renamed | other |
|---|---|---|---|---|---|
| 0–9 | 40.9% | 46.2% | 8.1% | 4.9% | 0.0% |
| 10–99 | 56.4% | 29.8% | 11.7% | 1.0% | 1.0% |
| 100+ | 58.8% | 21.9% | 7.6% | 6.4% | 5.3% |

never vs deleted inverts with maturity: in 0-star repositories (abandoned/experimental), deleted_before_anchor (46.2%) dominates never (40.9%), consistent with high churn; in 10+ repositories, never (~57%) dominates deleted (~22–30%), i.e., genuine non-implementation. other rises to 5.3% in the 100+ bucket, consistent with more force-push activity in mature repositories.

**R4: Alternative-path asymmetry.** Calibration showed ~15% of clean relative-path references (exists_at_anchor=1) resolve to a path different from the written one. Among unresolved references (exists_at_anchor=0), alternative_path is 0% across the entire sample. Path normalization explains part of the resolved cases but none of the unresolved ones: absence at the anchor is not a path artifact.

**R5: Measurement threats.** 15 clone failures (repositories deleted/private since the July 2026 collection), concentrated in larger repositories: a survivorship bias that likely underestimates never in mature projects. git log --follow is conservative for renames (a D+A refactor of foo.ts→foo.tsx is not reported as R), so renamed is a lower bound. other (2.7%) is reported separately and not summed into the other classes.

## M8: Accessibility × implementation (exploratory bridge)

To ask whether repositories with accessibility requirements tend to leave more of their "done but missing" references genuinely unimplemented, I joined `data/accessibility_requirements.csv` (repositories with accessibility requirements in their specs) to `data/classification_results.csv` (the classified references). The intersection is substantial (56 of the 137 cloned repositories (41%) carry accessibility requirements), so the bridge is viable as a descriptive comparison. At the reference level, the never rate is 60.4% for repositories with accessibility requirements versus 41.5% for those without; the full distribution shows the gap is driven by never (60.4% vs 41.5%) at the expense of created_later (4.5% vs 19.7%), with deleted_before_anchor similar (27.8% vs 33.2%). Because accessibility correlates with maturity and maturity correlates with never (R3), I checked the effect within each star bucket, and it persists everywhere: +22.9 percentage points in 0–9 stars, +23.1 in 10–99, and +6.7 in 100+, so maturity does not explain the difference. This is descriptive and repository-level (accessibility is detected in the specs while never is measured on the tasks, so it is not a task-level or causal claim), and the smaller gap in the 100+ bucket (6.7 points) suggests mature projects take accessibility more seriously, itself a small finding.

**Data and commands:**

- **Data source:** `data/accessibility_requirements.csv` joined to `data/classification_results.csv` on `repo_name`.
- `py m8_bridge.py`: prints the classification, the maturity inversion, and the bridge.
- Read-only aggregation (no new file); charts `data/chart_by_bucket.png`, `data/chart_bridge.png`, and `data/chart_bridge_repo.png`.

## Key findings

The full SpecMine v1.0 dataset reframes the earlier sample numbers. 435,401 OpenSpec task-to-code references span 7,076 repositories and 61,295 tasks.md files; 34,227 references (10.3% of the 332,168 with a resolvable anchor) are marked done but have no code at the anchor commit, and 91% of those are genuine file references (17,799 clean relative paths and 13,326 bare filenames) rather than non-file noise (3,102). The accessibility census over all 470,795 specs found 97,883 requirement lines across 10,717 repositories, of which 27.1% (26,529) carry a verifiable criterion; formal spec tools (openspec 37.0%, speckit 35.6%) state verifiable accessibility requirements far more often than informal specs (docs_embedded 8.9%, root_bare 12.9%). The gap concentrates in active changes: the missing rate is 17.7% among change_proposal references versus 9.0% among archived ones (and tasks.md exists only under openspec/changes/, so living specs contribute none).

Of "done but missing" references, 54.5% are genuinely never implemented (code never committed on any branch; median per-repository rate 66.7%), 29.5% were written then deleted before the anchor, and only 9.2% are late implementations. The never/deleted composition inverts with repository maturity: churn dominates in 0-star repositories, while non-implementation dominates in serious repositories. Repositories whose specs carry accessibility requirements leave more of their missing references genuinely never implemented (60.4% vs 41.5%), and the gap persists within every star bucket.

## Open questions

It is still unclear whether accessibility requirements are concentrated in UI frameworks or spread across domains.

- **Resolved:** whether the messy code paths hide a different ratio: **no.** `never` dominates even after removing non-file references: 84% are genuinely absent at the anchor (54.5% never + 29.5% deleted), and only 9.2% are late implementations.
- **New:** why the composition inverts with maturity: why do 0-star repositories show write-then-delete (churn) while serious repositories show genuine non-implementation?
- **New:** whether the spec_role effect survives within maturity buckets: is the change_proposal gap (17.7% vs 9.0% archived) a lifecycle effect, or does it confound with the star-bucket inversion from R3?
