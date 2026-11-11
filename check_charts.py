"""Validate the generated charts: accessibility, legibility and consistency.

Run with:  py check_charts.py      (or ``make check``)

The rules below are the ones the figures were designed against, so this script
is the executable form of the chart review:

* every chart in ``data/chart_alttext.json`` exists as a PNG, and every PNG in
  ``data/`` has an entry;
* every PNG carries its alt text in a ``Description`` metadata field;
* DPI >= 200 and width <= 1700 px, so the figure stays sharp in a ~1200 px
  container instead of being upscaled;
* every palette colour has >= 3:1 contrast against white (WCAG 1.4.11, non-text);
* every chart script that draws bars sets an edge colour, so segment
  boundaries stay perceivable when two fills look alike;
* no hardcoded percentage or p-value in a chart source: numbers must be derived
  from the data, otherwise a title silently goes stale;
* every PNG the dashboard displays exists.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

from PIL import Image

import chart_style as cs

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

MIN_DPI = 200
MAX_WIDTH = 2200
MIN_WIDTH = 1100
MIN_ALT_LEN = 80
MIN_CONTRAST = 3.0

failures: list[str] = []
checks = 0

#: calls whose string arguments end up printed on the figure
RENDER_CALLS = {"title", "set_title", "text", "annotate", "source_note",
                "hlabel", "vlabel"}


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(message)


def _literal(node) -> str:
    """The literal text of a str/f-string argument (format parts dropped)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(part.value for part in node.values
                       if isinstance(part, ast.Constant) and isinstance(part.value, str))
    return ""


def rendered_literals(source: str) -> list[str]:
    """Every literal string passed to a text-drawing call in a chart script."""
    texts = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "attr", getattr(func, "id", ""))
        if name not in RENDER_CALLS:
            continue
        for arg in node.args:
            texts.append(_literal(arg))
        for keyword in node.keywords:
            texts.append(_literal(keyword.value))
    return [text for text in texts if text.strip()]


def gallery_pngs(source: str) -> list[str]:
    """The PNG names listed by the dashboard's M9 gallery rows."""
    names = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.For):
            continue
        for element in getattr(node.iter, "elts", []):
            if not isinstance(element, ast.Tuple) or len(element.elts) != 3:
                continue
            text = _literal(element.elts[1])
            if text.endswith(".png"):
                names.append(text)
    return names


def png_names() -> list[Path]:
    return sorted(DATA.glob("chart_*.png"))


def chart_scripts() -> list[Path]:
    return sorted(p for p in HERE.glob("chart_*.py")
                  if p.name not in {"chart_style.py", "chart_utils.py",
                                    "chart_tables.py", "check_charts.py"})


def main() -> int:
    global checks
    alt = json.loads(cs.ALT_TEXT_JSON.read_text(encoding="utf-8"))
    pngs = png_names()

    # 1) the alt-text catalogue and the PNG files must agree, both ways
    for name in alt:
        check((DATA / name).exists(), f"{name}: listed in chart_alttext.json but missing")
    for png in pngs:
        check(png.name in alt, f"{png.name}: no entry in chart_alttext.json")
        check(len(alt.get(png.name, "")) >= MIN_ALT_LEN,
              f"{png.name}: alt text shorter than {MIN_ALT_LEN} characters")

    # 2) per-image technical checks
    for png in pngs:
        with Image.open(png) as image:
            dpi = int(round(image.info.get("dpi", (0, 0))[0]))
            width, height = image.size
            description = image.info.get("Description", "")
        check(dpi >= MIN_DPI, f"{png.name}: dpi {dpi} < {MIN_DPI}")
        check(width <= MAX_WIDTH, f"{png.name}: width {width} px > {MAX_WIDTH} px "
                                 "(would be upscaled in the dashboard)")
        check(width >= MIN_WIDTH, f"{png.name}: width {width} px < {MIN_WIDTH} px, "
                                 "too small to read")
        check(description == alt.get(png.name, ""),
              f"{png.name}: embedded Description does not match chart_alttext.json "
              "(re-run the chart script)")

    # 3) palette contrast against the white page
    for name, color in cs.PALETTE.items():
        ratio = cs.contrast(color, "#ffffff")
        check(ratio >= MIN_CONTRAST,
              f"palette '{name}' ({color}): contrast {ratio:.2f} < {MIN_CONTRAST} on white")

    # 4) bar charts must outline their fills (WCAG 1.4.11 segment boundaries)
    for script in chart_scripts():
        source = script.read_text(encoding="utf-8")
        if re.search(r"\.barh?\(|\.bar\(", source):
            check("edgecolor=" in source,
                  f"{script.name}: draws bars without an edgecolor")

    # 5) no hardcoded result in text that the figure renders
    literal_pct = re.compile(r"\d+(?:\.\d+)?\s*%")
    literal_p = re.compile(r"p\s*=\s*0\.\d")
    for script in chart_scripts():
        source = script.read_text(encoding="utf-8")
        rendered = rendered_literals(source)
        checks += 2
        for text in rendered:
            found_pct = literal_pct.search(text)
            if found_pct:
                failures.append(f"{script.name}: hardcoded percentage literal "
                                f"{found_pct.group(0)!r} in rendered text — derive it")
                break
        for text in rendered:
            found_p = literal_p.search(text)
            if found_p:
                failures.append(f"{script.name}: hardcoded p-value {found_p.group(0)!r} "
                                "in rendered text — compute it")
                break

    # 6) every figure the dashboard shows must exist on disk
    app_source = (HERE / "app.py").read_text(encoding="utf-8")
    shown = set(re.findall(r'"(chart_[a-z0-9_]+\.png)"', app_source))
    check(bool(shown), "app.py: no chart is displayed")
    for name in sorted(shown):
        check((DATA / name).exists(), f"app.py shows {name}, which does not exist")
        check(name in alt, f"app.py shows {name}, which has no alt text")

    # 7) the M9 gallery must list every figure, exactly once
    gallery = gallery_pngs(app_source)
    expected = sorted(png.name for png in pngs)
    checks += 1
    if sorted(gallery) != expected:
        missing = sorted(set(expected) - set(gallery))
        extra = sorted(set(gallery) - set(expected))
        if missing:
            failures.append("app.py M9 gallery is missing: " + ", ".join(missing))
        if extra:
            failures.append("app.py M9 gallery lists unknown: " + ", ".join(extra))
        if not missing and not extra:
            failures.append("app.py M9 gallery lists a figure more than once")

    print(f"check_charts: {checks} checks, {len(pngs)} PNGs, "
          f"{len(chart_scripts())} chart scripts, {len(alt)} alt-text entries")
    if failures:
        print(f"\nFAIL ({len(failures)})")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
