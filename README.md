# MSR 2027 Mining Challenge — SpecMine discovery walkthrough

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![MSR 2027](https://img.shields.io/badge/MSR-2027-red.svg)](https://2027.msrconf.org/track/msr-2027-mining-challenge)

A reproduction-ready walkthrough of a discovery on the
[**SpecMine**](https://huggingface.co/datasets/ShyAgarwal/specmine) dataset
(spec-driven development), one of the two datasets offered in the **MSR 2027
Mining Challenge**. The other dataset, **GitSkills** (agent skills), was explored
and then scoped out: the traceability question that SpecMine supports was both
the most novel and the most data-supported, so this repository is SpecMine-only
(GitSkills appears below only as the scoped-out alternative).

**The central result.** Of the 332,168 spec tasks marked *done* with a resolvable
anchor commit, **10.3%** (34,227) have no code at that commit, concentrated in active change proposals (17.7% vs 9.0% archived). Of those, **91%**
are genuine file references (not path noise), and **84.0%** are genuinely absent
— **54.5% never written on any branch**, 29.5% written then removed — with the
never/deleted composition inverting with repository maturity, and accessibility
requirements correlating with more "never".

## The discovery, step by step (M0–M9)

The analysis is a chain of ten milestones. Each is a short script that prints one
number (and, where relevant, one chart), so any result can be checked in
isolation:

| # | Script | Question | Result |
|---|---|---|---|
| M0 | `m0_sample_stats.py` | Is the sample strongly right-skewed? | `n_lines` skew 11.4 |
| M1 | `m1_sample_full.py` | Is the sample representative? | 28,583 specs = 6.1% of the full |
| M2 | `m2_pivot.py` | Which question does the data support? | all 5,992 PRs merged → traceability |
| M3 | `m3_census.py` | Does the gap exist at scale, and where? | 34,227 = 10.3%; 17.7% change_proposal vs 9.0% archived |
| M4 | `m4_discovery.py` | Is `exists_at_anchor` binary? | 0 / 1 / 2 / NULL — under-documented |
| M5 | `m5_taxonomy.py` | Real file or path noise? | 91% real files |
| M6 | `m6_accessibility.py` | Are accessibility reqs verifiable? | 27.1% |
| M7 | `m7_calibration.py` | How much is path normalization? | 15.2% |
| M8 | `m8_bridge.py` | How many are truly "never"? | 54.5% never; inverts with maturity |
| M9 | `m9_discovery_summary.py` | The whole arc | — |

Run any milestone to reproduce its number:

```bash
py m0_sample_stats.py
py m1_sample_full.py
# … through …
py m9_discovery_summary.py
```

Each milestone follows the same three-tier bootstrap: (1) a **committed CSV**
fast path, (2) **regeneration** from the raw data if the CSV is missing, and (3)
a **friendly message** pointing at the missing dataset if neither is available.
Milestones that produce a chart also report whether that chart is *stale*
(drawn before the data changed) and, if so, point at `make charts`.

## Datasets

The two datasets offered by the challenge (both mined from public GitHub
repositories in July 2026):

| Dataset | Artifact | Scale | Paper |
|---|---|---|---|
| **SpecMine** (used) | `spec.md` (spec-driven development) | 471k specs / 73k repos | [arXiv:2608.25202](https://arxiv.org/abs/2608.25202) |
| **GitSkills** (scoped out) | `SKILL.md` (agent skills) | 3.8M files / 282k repos | [arXiv:2608.10906](https://arxiv.org/abs/2608.10906) |

SpecMine is used in two releases:

- **v1.1 sample** (`SAMPLE_SPECMINE_DATA`) — a small star-curated slice used by M0/M1.
- **v1.0 full** (`SPECMINE_DATA`) — the 10-table Zenodo release used by M2–M8.

The raw spec text (`specs.jsonl`) is a separate JSONL that the accessibility
extraction reads (the Parquet stores metadata, not the Markdown bodies).

See the challenge call at <https://2027.msrconf.org/track/msr-2027-mining-challenge>.

## Configuration

The datasets are **not** shipped in this repository. `db.py` resolves their
locations relative to the repository root (sibling folders) and can be
overridden with environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `SAMPLE_SPECMINE_DATA` | v1.1 sample (13 tables) | `../specmine-official/data` |
| `SPECMINE_DATA` | v1.0 full (10 tables) | `../specmine-official/data/specmine/specmine-zenodo/data` |
| `SPECMINE_SPECS_JSONL` | decompressed `specs.jsonl` | `../specmine-official/data/specmine/specmine-zenodo/specs.jsonl/specs.jsonl` |

The doubled `specs.jsonl/specs.jsonl` is not a typo: the `specs.jsonl.gz` archive
decompresses into a `specs.jsonl/` folder holding the uncompressed `specs.jsonl`.
`SPECMINE_SPECS_JSONL` must point to the **full v1.0** file (≈3.2 GB, 470,795
specs) — the file that produced the committed `data/accessibility_requirements.csv` —
*not* the smaller v1.1 sample (28,583 specs) that also lives under
`specmine-official/specs.jsonl/`.

On Windows (PowerShell):

```powershell
$env:SPECMINE_DATA = "C:\path\to\specmine\v1.0\data"
$env:SAMPLE_SPECMINE_DATA = "C:\path\to\specmine\v1.1\data"
```

On Linux/macOS (bash):

```bash
export SPECMINE_DATA=/path/to/specmine/v1.0/data
export SAMPLE_SPECMINE_DATA=/path/to/specmine/v1.1/data
```

## Installation

Requires **Python 3.9+** and **git** (for the clone-classify clone step).

```bash
pip install -r requirements.txt
```

or `make install`.

## Usage

```bash
make run       # start the Streamlit walkthrough (M0–M8 + Discovery)
make test      # validate the app headlessly
make charts    # regenerate all derived CSVs + charts from the dataset
make clone     # pre-clone the clone-classify sample (network-bound)
make classify    # run clone-classify (clone-if-needed + classify)
make clean     # remove __pycache__ caches
```

or `streamlit run app.py`.

## Derivation pipeline & reproducibility

Every number and chart is *derived* from the raw SpecMine files (Parquet +
`specs.jsonl`) through a three-stage pipeline; the intermediate artifacts are
committed so results can be checked without re-running the expensive stages.

| Stage | Input → Output | Script | Deterministic? |
|---|---|---|---|
| extract | `openspec_code_refs.parquet` → `data/taxonomy_e0.csv` | `taxonomy.py` | yes |
| extract | `specs.jsonl` + `spec_files.parquet` → `data/accessibility_requirements.csv` | `extract_accessibility.py` | yes |
| extract | `taxonomy_e0.csv` + `spec_files.parquet` + git clones → `data/classification_results.csv` | `clone_classify.py` | **no (git is mutable)** |
| chart | the CSVs / parquet → `data/*.png` | `chart_*.py` | yes (given its CSV) |

### The commands

`make charts` re-runs the whole chain in dependency order — `taxonomy.py`,
`extract_accessibility.py`, `clone_classify.py`, then the five `chart_*.py` — so every
CSV and every PNG is regenerated from the current dataset. It is the canonical
answer to "the data changed; make the pictures match."

`make clone` (≡ `py clone_classify.py --clone-only`) materializes the clone-classify frame and
sample if their CSVs are missing, then clones every sampled repository without
classifying. It exists because cloning ~150 repositories is slow and
network-bound and is best done separately (e.g. in the background). It is
idempotent — repositories already under `clones/` are reused, not re-cloned.

`make classify` (≡ `py clone_classify.py`) is the full clone-classify run: it clones the missing
repositories and classifies every sampled reference into one of six buckets
(`never`, `deleted_before_anchor`, `created_later`, `renamed`,
`alternative_path`, `other`), writing `data/classification_results.csv`.

### What is and is not deterministic

The two text-extraction stages are **fully deterministic**: given the same input
files they reproduce the same CSV. `taxonomy.py` is a pure function of each path
string (its `classify_path` is reused verbatim by M5 and M7 so the definition
cannot drift), and `extract_accessibility.py` applies a fixed vocabulary plus a
fixed "verifiable" rule (a `shall|must` imperative OR a measurable threshold) to
every non-empty line.

The **git-clone stage is not reproducible across time.** `clone_classify.py` clones each
sampled repository from `https://github.com/<owner>/<repo>.git`, and GitHub
repositories are *mutable*: commits are added, history is rewritten (force-push),
and repositories are deleted or renamed. Two runs that re-clone from scratch on
different dates can therefore classify the same `anchor_sha` differently — a
commit that is "created later" today can be "never" tomorrow if the branch was
deleted. This is the single non-deterministic step, and it is isolated from the
deterministic ones for exactly that reason. To bound the effect:

- **Frozen clones.** `clone_repo()` is idempotent: it reuses any repository
  already under `clones/` (verified with `git rev-parse --verify HEAD`) and only
  clones the missing ones. Re-running `make classify` (or `make charts`) on the
  same checkout reproduces `classification_results.csv` exactly; the non-determinism
  appears only if you delete `clones/` and re-clone.
- **`ALL_BRANCHES = True`.** "never" is the conservative reading — the path was
  never committed on *any* ref, so an unmerged feature branch counts as
  implemented, not missing.
- **A fixed, seeded sample.** Classification runs on a stratified sample (below),
  so re-runs target the same repositories.
- **Failures are recorded, not guessed.** A repository that cannot be cloned
  (deleted, renamed, made private, network error) is listed at the end of the run
  and excluded from the denominators.
- **The committed CSV records outcomes, not raw evidence.** `data/classification_results.csv`
  stores each reference's bucket and its `anchor_sha`, but not the commit SHAs that
  first added, deleted, or renamed the path (`classify()` discards them). The
  aggregate rates therefore reproduce from the committed CSV alone; auditing an
  individual classification — especially `never` (the dominant class), which is
  *negative* evidence (no commit adds the path) — requires re-running `clone_classify.py`
  with the clones.

### The clone-classify sample

`clone_classify.py` does not classify all 17,799 clean-path references — it classifies a
**stratified sample of repositories**. The frame joins `taxonomy_e0.csv` to
`spec_files` (for `repo_stars` / `repo_language`), buckets by stars (`0–9`,
`10–99`, `100+`), and draws a fixed number of repositories per bucket —
`TARGETS = {"0-9": 50, "10-99": 45, "100+": 57}` — allocated proportionally to
the dominant language within each bucket (largest-remainder). The draw uses a
fixed seed (`SEED = 42`), so `data/classification_sample.csv` is reproducible; the `100+`
bucket is a census (57 = every qualifying repository), not a sample. In the run
committed here the sample is 152 repositories (50/45/57); 15 failed to clone and
were excluded, leaving 137 classified repositories and 1,298 references. All
"never / deleted / …" rates are therefore sample estimates, with the `100+`
bucket exhaustive.

## Project structure

```
.
├── app.py                     # Streamlit walkthrough (M0–M8 + Discovery)
├── m0_sample_stats.py … m9_discovery_summary.py   # the ten milestones
├── taxonomy.py                # path classifier → taxonomy_e0.csv
├── extract_accessibility.py   # accessibility scan → accessibility_requirements.csv
├── clone_classify.py                  # git-clone + classify → classification_results.csv
├── chart_census.py … chart_bridge.py   # CSV → PNG
├── chart_utils.py             # chart staleness helper (make charts hints)
├── db.py                      # dataset paths
├── reasoning.md               # the line of reasoning (why each step)
├── reproduction-steps.md      # the research log (how to reproduce)
├── Makefile                   # install / run / test / charts / clone / classify / clean
├── requirements.txt
└── data/                      # committed CSVs + chart PNGs
```

## Documentation

- [**reasoning.md**](reasoning.md) — the *why*: the line of reasoning, each
  milestone's question / data / criterion / result / meaning.
- [**reproduction-steps.md**](reproduction-steps.md) — the *how*: the research
  log written as a recipe.

## References

Challenge track: <https://2027.msrconf.org/track/msr-2027-mining-challenge>

**SpecMine** (Agarwal et al., MSR 2027):

```bibtex
@inproceedings{specmine2027,
  author    = {Agarwal, Shyam and Singhal, Anmol and Breaux, Travis and Vasilescu, Bogdan},
  title     = {SpecMine: A Large-Scale Corpus of Spec-Driven Development Artifacts},
  year      = {2027},
  publisher = {IEEE},
  url       = {https://arxiv.org/abs/2608.25202},
  booktitle = {Proceedings of the 24th International Conference on Mining Software Repositories},
  location  = {Dublin, Ireland},
  series    = {MSR '27}
}
```

**GitSkills** (Destefanis et al., MSR 2027) — the scoped-out dataset:

```bibtex
@inproceedings{gitskills2027,
  author    = {Destefanis, Giuseppe and Graziotin, Daniel and Vaccargiu, Matteo and Ortu, Marco},
  title     = {GitSkills: A Dataset of Agent Skills on GitHub},
  year      = {2027},
  publisher = {IEEE},
  url       = {https://arxiv.org/abs/2608.10906},
  booktitle = {Proceedings of the 24th International Conference on Mining Software Repositories},
  location  = {Dublin, Ireland},
  series    = {MSR '27}
}
```

## License

[Apache License 2.0](LICENSE).

The underlying datasets are released under their own licenses (SpecMine: CC BY 4.0,
with file contents under each source repository's license).
