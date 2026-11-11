"""Shared helper for the walkthrough files: chart freshness.

A chart PNG is "stale" when any file it was drawn from is newer than it — i.e.
the dataset changed after the chart was generated. The m* files and the
dashboard use this to point at ``make charts`` instead of silently showing a
stale image. ``CHART_SOURCES`` is the single list of what each PNG depends on.
"""
from pathlib import Path

from db import SAMPLE_SPECMINE_DATA, SPECMINE_DATA

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SAMPLE = Path(SAMPLE_SPECMINE_DATA)
FULL = Path(SPECMINE_DATA)

CHART_SOURCES = {
    "chart_m0_sample.png": (SAMPLE / "spec_content_features.parquet",
                            SAMPLE / "spec_files.parquet"),
    "chart_m0_tools.png": (SAMPLE / "spec_files.parquet",),
    "chart_m1_sample_full.png": (SAMPLE / "spec_files.parquet",
                                 SAMPLE / "openspec_code_refs.parquet",
                                 SAMPLE / "spec_links.parquet",
                                 SAMPLE / "pull_requests.parquet",
                                 FULL / "spec_files.parquet",
                                 FULL / "openspec_code_refs.parquet",
                                 FULL / "spec_links.parquet",
                                 FULL / "pull_requests.parquet"),
    "chart_m1_tools.png": (FULL / "spec_files.parquet",),
    "chart_m2_pivot.png": (FULL / "pull_requests.parquet",),
    "chart_census.png": (FULL / "openspec_code_refs.parquet",),
    "chart_m4_discovery.png": (FULL / "openspec_code_refs.parquet",),
    "chart_taxonomy.png": (DATA / "taxonomy_e0.csv",
                           FULL / "openspec_code_refs.parquet"),
    "chart_accessibility.png": (DATA / "accessibility_requirements.csv",
                                FULL / "spec_files.parquet"),
    "chart_m7_calibration.png": (FULL / "openspec_code_refs.parquet",),
    "chart_outcomes.png": (DATA / "classification_results.csv",),
    "chart_by_bucket.png": (DATA / "classification_results.csv",),
    "chart_bridge.png": (DATA / "classification_results.csv",
                         DATA / "accessibility_requirements.csv"),
    "chart_bridge_repo.png": (DATA / "classification_results.csv",
                              DATA / "accessibility_requirements.csv"),
}


def chart_sources(png_name):
    """Input files the chart ``png_name`` was drawn from."""
    return CHART_SOURCES.get(png_name, ())


def chart_status(png, *sources):
    """Return (exists: bool, stale: bool) for a chart PNG.

    ``sources`` are the input files the chart depends on (parquet / CSV). If
    any source exists and is newer than the PNG, the chart is stale.
    """
    png = Path(png)
    if not png.exists():
        return False, False
    png_mtime = png.stat().st_mtime
    for src in sources:
        src = Path(src)
        if src.exists() and src.stat().st_mtime > png_mtime:
            return True, True
    return True, False
