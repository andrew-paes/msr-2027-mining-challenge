# MSR 2027 Mining Challenge — GitSkills + SpecMine

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![MSR 2027](https://img.shields.io/badge/MSR-2027-red.svg)](https://2027.msrconf.org/track/msr-2027-mining-challenge)

Exploratory analysis of the two datasets from the **MSR 2027 Mining Challenge**:
[**GitSkills**](https://huggingface.co/datasets/mvaccargiu/gitskills) (agent skills) and
[**SpecMine**](https://huggingface.co/datasets/ShyAgarwal/specmine) (spec-driven development),
queried together through a single **DuckDB** database and visualized with **Streamlit**.

Both datasets capture natural-language artifacts that AI coding agents produce and
consume — agent skills (`SKILL.md`) and specifications (`spec.md`) — mined from public
GitHub repositories in July 2026.

## Datasets

| Dataset | Artifact | Scale | Hugging Face | Paper |
|---|---|---|---|---|
| **GitSkills** | `SKILL.md` (agent skills) | 3.8M files / 282k repos | [mvaccargiu/gitskills](https://huggingface.co/datasets/mvaccargiu/gitskills) | [arXiv:2608.10906](https://arxiv.org/abs/2608.10906) |
| **SpecMine** | `spec.md` (spec-driven development) | 471k specs / 73k repos | [ShyAgarwal/specmine](https://huggingface.co/datasets/ShyAgarwal/specmine) | [arXiv:2608.25202](https://arxiv.org/abs/2608.25202) |

See the challenge call at
<https://2027.msrconf.org/track/msr-2027-mining-challenge>.

## What the dashboard shows

- **GitSkills** — reuse/long-tail of verbatim copies, location class, body length with
  normal curve, skills-per-repo concentration, stars, languages, adoption over time.
- **SpecMine** — lifecycle (`spec_role`, ~51% archived), tools (`spec_tool`),
  spec length, traceability (`spec_links.rel`), co-change (`touches_code`), adoption over time.
- **Statistics** — descriptive stats (mean/median/mode/std/skew/kurtosis/normality test)
  and inferential tests (e.g. Mann-Whitney U).

## Project structure

```
.
├── app.py              # Streamlit dashboard (entry point)
├── db.py               # DuckDB connection (SQLite + Parquet)
├── queries.py          # SQL queries over GitSkills and SpecMine
├── charts.py           # matplotlib/seaborn chart helpers
├── stats.py            # descriptive + inferential statistics
├── test_app.py         # headless validation (AppTest)
├── Makefile            # task runner (install / run / test / clean)
├── requirements.txt    # Python dependencies
└── tables.md           # data model, ERD and star-schema documentation
```

## Installation

Requires **Python 3.9+**.

```bash
pip install -r requirements.txt
```

or, with `make`:

```bash
make install
```

## Configuration

The datasets are **not** shipped in this repository. `db.py` resolves their locations
relative to the repository root (sibling folders `gitskills-sample/` and
`specmine-official/`), and can be overridden with environment variables:

| Variable | Default |
|---|---|
| `GITSKILLS_DB` | `../gitskills-sample/agent_skills_sample/agent_skills_sample.db` |
| `SPECMINE_DATA` | `../specmine-official/data` |

On Windows (PowerShell):

```powershell
$env:GITSKILLS_DB = "C:\path\to\agent_skills_sample.db"
$env:SPECMINE_DATA = "C:\path\to\specmine\data"
```

On Linux/macOS (bash):

```bash
export GITSKILLS_DB=/path/to/agent_skills_sample.db
export SPECMINE_DATA=/path/to/specmine/data
```

## Usage

```bash
make run      # start the Streamlit app in the browser
make test     # validate the app headlessly
make install  # install dependencies
make clean    # remove __pycache__ caches
```

Or run Streamlit directly:

```bash
streamlit run app.py
```

## Documentation

- [**tables.md**](tables.md) — full inventory of every table and column in both
  datasets, the entity-relationship diagram (ERD), the join keys, and the DuckDB
  star-schema design.

## References

Challenge track: <https://2027.msrconf.org/track/msr-2027-mining-challenge>

**GitSkills** (Destefanis et al., MSR 2027):

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

## License

[Apache License 2.0](LICENSE).

The underlying datasets are released under their own licenses (GitSkills: CC BY 4.0;
SpecMine: CC BY 4.0, with file contents under each source repository's license).
