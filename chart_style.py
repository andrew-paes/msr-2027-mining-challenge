"""Shared matplotlib style + accessibility helpers for the chart_*.py scripts.

One module instead of a ``.mplstyle`` file because the checker
(``check_charts.py``) imports these same constants, so the visual rules cannot
drift from the figures.

Design constraints, measured with the WCAG 2.x relative-luminance formula:

* body text is ``INK`` (#1a1a1a, 17.4:1 on white) and notes are ``MUTED``
  (#5f5f5f, 6.0:1) — both past the 4.5:1 AA threshold for normal text;
* every filled shape that encodes a category carries a dark outline (``INK``,
  0.8 pt), so a segment boundary is always >= 3:1 against the fill *and* the
  white background (WCAG 1.4.11) even when two adjacent fills look alike; the
  histogram, which is a single series, uses hairlines between bins instead;
* six saturated fills can never reach 3:1 *between adjacent segments* (3:1 per
  step over six steps would require a 243:1 range), so the two dominant
  classes additionally carry a distinct hatch texture and every segment wide
  enough is labelled with its value: colour is never the only channel
  (WCAG 1.4.1).
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend, no display needed

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
ALT_TEXT_JSON = DATA_DIR / "chart_alttext.json"

# --- palette ---------------------------------------------------------------
# Contrast against white measured by contrast(): ink 17.4, slate 8.5, navy 7.8,
# brown 4.6, blue 5.2, vermillion 3.9, green 3.4, purple 3.1, muted 6.0.
INK = "#1a1a1a"
MUTED = "#5f5f5f"
GRID = "#d9d9d9"
BLUE = "#0072b2"
VERMILLION = "#d55e00"
GREEN = "#009e73"
PURPLE = "#cc79a7"
SLATE = "#4d4d4d"
NAVY = "#0b5394"
BROWN = "#a6611a"

#: every colour that carries meaning, for the contrast check (the grid,
#: #d9d9d9, is decorative and deliberately absent: 1.4:1 would fail the rule)
PALETTE = {
    "ink": INK,
    "muted": MUTED,
    "blue": BLUE,
    "vermillion": VERMILLION,
    "green": GREEN,
    "purple": PURPLE,
    "slate": SLATE,
    "navy": NAVY,
    "brown": BROWN,
}

#: classification -> (colour, hatch, human label). Shared by every chart that
#: shows a classification so the same class is the same colour everywhere.
CLASSES = [
    ("never", VERMILLION, "///", "never (never committed)"),
    ("deleted_before_anchor", BROWN, "...", "deleted before anchor"),
    ("created_later", BLUE, "", "created later"),
    ("renamed", GREEN, "", "renamed"),
    ("alternative_path", PURPLE, "", "alternative path"),
    ("other", SLATE, "", "other"),
]
CLASS_COLOR = {key: color for key, color, _h, _l in CLASSES}
CLASS_HATCH = {key: hatch for key, _c, hatch, _l in CLASSES}
CLASS_LABEL = {key: label for key, _c, _h, label in CLASSES}

#: identifiers that leak into axis ticks -> reader-facing wording
WORDS = {
    "change_proposal": "change proposal",
    "archived": "archived",
    "spec_files": "spec files",
    "openspec_code_refs": "code references",
    "spec_links": "spec links",
    "pull_requests": "pull requests",
    "relative_ext": "relative path",
    "bare_ext": "bare filename",
    "glob": "glob pattern",
    "absolute": "absolute path",
    "exists_at_anchor": "exists at anchor",
    "star_bucket": "star bucket",
}


def apply_style() -> None:
    """Install the shared rcParams. Call once at the top of ``main()``."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelsize": 11,
            "axes.labelcolor": INK,
            "axes.edgecolor": MUTED,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "legend.fontsize": 10,
            "legend.frameon": False,
            "figure.dpi": 100,
            "savefig.dpi": 200,
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.15,
            "hatch.linewidth": 0.7,
        }
    )


# --- contrast ---------------------------------------------------------------
def _luminance(hex_color: str) -> float:
    raw = hex_color.lstrip("#")
    channels = [int(raw[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two ``#rrggbb`` colours."""
    la, lb = _luminance(a), _luminance(b)
    high, low = max(la, lb), min(la, lb)
    return (high + 0.05) / (low + 0.05)


# --- formatting -------------------------------------------------------------
def fmt_int(value: float) -> str:
    """1200 -> '1,200' (thousands separators everywhere)."""
    return f"{int(round(value)):,}"


def fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def word(key: str) -> str:
    """Map a dataset identifier to reader-facing text (falls back to itself)."""
    return WORDS.get(key, key.replace("_", " "))


# --- text blocks ------------------------------------------------------------
def title(ax, finding: str, sub: str | None = None, width: int = 62) -> None:
    """Register a left-aligned finding title, optionally with a muted sub-line.

    The text is not drawn here: ``save`` places every title at the same height
    per panel row, so a two-panel figure cannot end up with one title lower
    than the other (``tight_layout`` gives each axes its own decorations).

    Findings never carry hardcoded numbers: anything that comes from the data
    is written by ``source_note`` / bar labels, so a stale number cannot hide
    in a title after the dataset changes. ``width`` sets the wrap column, which
    has to shrink for panels that share a figure side by side.
    """
    sub_wrapped = textwrap.fill(sub, width) if sub else ""
    lines = sub_wrapped.count("\n") + 1 if sub_wrapped else 0
    ax._chart_title = (textwrap.fill(finding, width), sub_wrapped)
    # an empty title reserves the vertical room that tight_layout needs
    ax.set_title(" ", loc="left", pad=6 + 12 * lines)


def _place_titles(fig) -> None:
    """Draw the registered titles, aligned per row, after the layout is final."""
    fig.canvas.draw()
    height = fig.get_figheight()
    rows: dict[float, list] = {}
    for ax in fig.axes:
        if getattr(ax, "_chart_title", None) is None:
            continue
        position = ax.get_position()
        rows.setdefault(round((position.y0 + position.y1) / 2, 1), []).append(ax)

    for group in rows.values():
        top = max(ax.get_position().y1 for ax in group)
        # every panel in a row uses the tallest sub-block, so the titles align
        # even when one panel's subtitle needs fewer lines
        tallest = max((ax._chart_title[1].count("\n") + 1
                       if ax._chart_title[1] else 0) for ax in group)
        for ax in group:
            finding, sub = ax._chart_title
            x = ax.get_position().x0
            y_sub = top + 0.06 / height
            if sub:
                lines = sub.count("\n") + 1
                # top-align the sub-block with the tallest in the row, so the
                # extra air lands above the plot rather than under the title
                y_sub += (tallest - lines) * 0.145 / height
                fig.text(x, y_sub, sub, ha="left", va="bottom", fontsize=9.5,
                         color=MUTED)
            y_title = top + (tallest * 0.145 + 0.11) / height if tallest else y_sub
            fig.text(x, y_title, finding, ha="left", va="bottom", fontsize=13,
                     fontweight="bold", color=INK)


def source_note(fig, text: str, y: float = -0.02) -> None:
    """Figure-level footnote sitting below the axes (never over an axis label)."""
    fig.text(0.0, y, textwrap.fill(text, 112), ha="left", va="top",
             fontsize=9, color=MUTED)


def legend(ax, entries, **kwargs) -> None:
    """Legend from ``[(label, color, hatch), ...]`` — colour *and* texture."""
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor=color, edgecolor=INK, linewidth=0.8,
              hatch=hatch or None, label=label)
        for label, color, hatch in entries
    ]
    kwargs.setdefault("loc", "upper right")
    kwargs.setdefault("labelcolor", INK)
    ax.legend(handles=handles, **kwargs)


# --- annotations ------------------------------------------------------------
def _grow(ax, axis: str, pad_frac: float = 0.04) -> None:
    """Grow an axis limit until every annotation drawn inside it fits."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inverse = ax.transData.inverted()
    if axis == "x":
        low, high = ax.get_xlim()
        need = high
        for child in ax.texts:
            box = child.get_window_extent(renderer=renderer)
            need = max(need, inverse.transform((box.x1, box.y0))[0])
        if need > high:
            ax.set_xlim(low, need + (need - low) * pad_frac)
    else:
        low, high = ax.get_ylim()
        need = high
        for child in ax.texts:
            box = child.get_window_extent(renderer=renderer)
            need = max(need, inverse.transform((box.x0, box.y1))[1])
        if need > high:
            ax.set_ylim(low, need + (need - low) * pad_frac)


def hlabel(ax, bars, texts, *, pad: float = 0.01, fontsize: float = 10,
           color: str = INK, backdrop: bool = False) -> None:
    """Value labels after horizontal bar ends, with room reserved for them.

    ``backdrop`` puts a translucent white chip behind each label, for the cases
    where a reference line crosses the label column.
    """
    span = ax.get_xlim()[1] - ax.get_xlim()[0]
    box = (dict(facecolor="white", edgecolor="none", pad=1.2, alpha=0.85)
           if backdrop else None)
    for bar, text in zip(bars, texts):
        ax.text(bar.get_width() + span * pad,
                bar.get_y() + bar.get_height() / 2,
                text, va="center", ha="left", fontsize=fontsize, color=color,
                bbox=box)
    _grow(ax, "x")


def vlabel(ax, bars, texts, *, pad: float = 0.01, fontsize: float = 10,
           color: str = INK) -> None:
    """Value labels above vertical bars, with room reserved for them."""
    span = ax.get_ylim()[1] - ax.get_ylim()[0]
    for bar, text in zip(bars, texts):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + span * pad,
                text, va="bottom", ha="center", fontsize=fontsize, color=color)
    _grow(ax, "y")


def pct_axis(ax, axis: str = "y", digits: int = 0) -> None:
    """Format an axis as a percentage."""
    formatter = PercentFormatter(xmax=100, decimals=digits, symbol="%")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(formatter)


def hgrid(ax) -> None:
    """Grid on the value axis of a horizontal bar chart (vertical guides only)."""
    ax.grid(False, axis="y")
    ax.grid(True, axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def int_axis(ax, axis: str = "x") -> None:
    """Thousands separators on a count axis."""
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(
        FuncFormatter(lambda value, _pos: f"{value:,.0f}")
    )


# --- output -----------------------------------------------------------------
def alt_text(png_name: str) -> str:
    """Accessible description for a chart, from ``data/chart_alttext.json``."""
    try:
        entries = json.loads(ALT_TEXT_JSON.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ""
    return entries.get(png_name, "")


def save(fig, path: Path) -> None:
    """Save a figure with its alt text embedded, then release it."""
    alt = alt_text(path.name)
    if not alt:
        print(f"WARNING: no alt text for {path.name} in {ALT_TEXT_JSON.name}")
    _place_titles(fig)
    metadata = {"Software": "msr-2027 chart_style.py"}
    if alt:
        metadata["Description"] = alt
    fig.savefig(path, metadata=metadata)
    plt.close(fig)
    print(f"saved {path}")
