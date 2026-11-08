"""Dataset paths for the SpecMine analysis (sample v1.1 and full v1.0).

Resolved relative to the repository root (the parent of this project folder),
so the project runs on any machine with the same layout. Override with the
SAMPLE_SPECMINE_DATA / SPECMINE_DATA environment variables.
"""
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent

# SpecMine sample (v1.1, 13 tables) — used by the m0/m1 walkthrough steps.
SAMPLE_SPECMINE_DATA = os.environ.get(
    "SAMPLE_SPECMINE_DATA",
    str(_REPO_ROOT / "specmine-official" / "data"),
)
# SpecMine full (v1.0, 10 tables) — used by m2+.
SPECMINE_DATA = os.environ.get(
    "SPECMINE_DATA",
    str(_REPO_ROOT / "specmine-official" / "data" / "specmine" / "specmine-zenodo" / "data"),
)
