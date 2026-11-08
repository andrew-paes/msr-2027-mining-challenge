"""Shared helper for the walkthrough files: chart freshness.

A chart PNG is "stale" when any file it was drawn from is newer than it — i.e.
the dataset changed after the chart was generated. The m* files use this to
point at ``make charts`` instead of silently showing a stale image.
"""
from pathlib import Path


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
