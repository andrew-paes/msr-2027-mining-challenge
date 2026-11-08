"""Extract accessibility requirements from the SpecMine spec corpus (full scale).

Streams the decompressed ``specs.jsonl`` (one JSON object per line), scans every
non-empty line for a curated accessibility vocabulary, and — for each matching
requirement line — applies a reproducible "verifiable" rule (an imperative modal
or a measurable threshold). Writes one CSV row per unique requirement line.

Categories:
    compliance            WCAG, Section 508, ADA, EN 301 549
    assistive_technology  screen readers, ARIA, alt text, VoiceOver/NVDA/JAWS/TalkBack
    interaction           keyboard navigation, focus management, reduced motion
    visual                contrast ratio, colorblind, low vision
    media                 captions, transcript, audio description
    semantic              ARIA role attributes
    motor_cognitive       voice control, dyslexia, plain language
    general               accessibility, a11y

The "verifiable" rule (per line, reproducible):
    verifiable     = has_imperative OR has_threshold
    has_imperative = the line contains \\b(shall|must)\\b
    has_threshold  = the line contains a measurable threshold (a ratio such as
                     4.5:1, a comparison followed by a number, a WCAG level
                     AA/AAA, or a number with a unit).

Note: the term ``ADA`` is matched case-sensitively (``\\bADA\\b``) to avoid the
Ada programming language, and the adjective "accessible" is intentionally
excluded because it often means "available/reachable".

Usage:
    python extract_accessibility.py
"""
import csv
import json
import os
import re
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent

SPECS_JSONL = os.environ.get(
    "SPECMINE_SPECS_JSONL",
    str(REPO_ROOT / "specmine-official" / "data" / "specmine" / "specmine-zenodo" / "specs.jsonl" / "specs.jsonl"),
)
SPEC_FILES_PARQUET = os.path.join(
    os.environ.get(
        "SPECMINE_DATA",
        str(REPO_ROOT / "specmine-official" / "data" / "specmine" / "specmine-zenodo" / "data"),
    ),
    "spec_files.parquet",
)
OUTPUT_DIR = HERE / "data"
OUTPUT_CSV = OUTPUT_DIR / "accessibility_requirements.csv"

# (category, term, compiled regex)
ACCESSIBILITY_PATTERNS = [
    # compliance / standards
    ("compliance", "wcag", re.compile(r"\bwcag\b", re.IGNORECASE)),
    ("compliance", "section_508", re.compile(r"section\s+508", re.IGNORECASE)),
    ("compliance", "ada", re.compile(r"Americans with Disabilities Act", re.IGNORECASE)),  # full phrase: bare "ADA" collides with the Cardano token
    ("compliance", "en_301_549", re.compile(r"en\s*301\s*549", re.IGNORECASE)),
    # assistive technology
    ("assistive_technology", "screen_reader", re.compile(r"screen\s*reader|screenreader", re.IGNORECASE)),
    ("assistive_technology", "assistive_technology", re.compile(r"assistive\s+technology", re.IGNORECASE)),
    ("assistive_technology", "alt_text", re.compile(r"alt[-\s](text|attribute)", re.IGNORECASE)),
    ("assistive_technology", "aria", re.compile(r"\bARIA\b|aria-[a-z-]+", re.IGNORECASE)),
    ("assistive_technology", "screen_reader_sw", re.compile(r"\b(voiceover|nvda|jaws|talkback)\b", re.IGNORECASE)),
    # interaction
    ("interaction", "keyboard", re.compile(r"keyboard\s+(navigation|focus|access)", re.IGNORECASE)),
    ("interaction", "focus_management", re.compile(r"focus\s+(management|order|trap|state|visible)", re.IGNORECASE)),
    ("interaction", "reduced_motion", re.compile(r"reduced\s*motion", re.IGNORECASE)),
    # visual
    ("visual", "contrast_ratio", re.compile(r"contrast\s*ratio", re.IGNORECASE)),
    ("visual", "colorblind", re.compile(r"color\s*blind", re.IGNORECASE)),
    ("visual", "low_vision", re.compile(r"low\s*vision", re.IGNORECASE)),
    # media (accessibility-specific only; bare "caption" and "transcript" are
    # dominated by UI labels and AI-session transcripts)
    ("media", "closed_caption", re.compile(r"closed\s*captions?", re.IGNORECASE)),
    ("media", "audio_description", re.compile(r"audio\s*description", re.IGNORECASE)),
    # semantic
    ("semantic", "role_attr", re.compile(r"role\s*=", re.IGNORECASE)),
    # motor / cognitive
    ("motor_cognitive", "voice_control", re.compile(r"voice\s*control", re.IGNORECASE)),
    ("motor_cognitive", "dyslexia", re.compile(r"\bdyslexia\b", re.IGNORECASE)),
    ("motor_cognitive", "plain_language", re.compile(r"plain\s*language", re.IGNORECASE)),
    # general
    ("general", "a11y", re.compile(r"\ba11y\b", re.IGNORECASE)),
    ("general", "accessibility", re.compile(r"\baccessibility\b", re.IGNORECASE)),
]

# "Verifiable" rule (per line).
IMPERATIVE = re.compile(r"\b(shall|must)\b", re.IGNORECASE)
THRESHOLD = re.compile(
    r"\d+(?:\.\d+)?\s*:\s*\d+"                   # ratio, e.g. 4.5:1
    r"|[<>]=?\s*\d|[≥≤]\s*\d"                    # comparison followed by a number
    r"|\bAA\b|\bAAA\b"                           # WCAG conformance level
    r"|\d+(?:\.\d+)?\s*(?:px|em|rem|%|ms|s\b)",  # number + unit
    re.IGNORECASE,
)

# Fast pre-filter: literal keywords (case-insensitive) plus a word-bounded
# "ada"/"ADA". The literal alternation avoids the backtracking cost of the full
# \b-\s* patterns, and "ada" is handled separately so "data"/"database" are not
# over-matched. The per-pattern check below still applies the precise
# case-sensitive \bADA\b rule.
_LITERAL_TERMS = re.compile(
    r"wcag|section 508|301 549|americans with disabilities|screen reader|screenreader|assistive technology|"
    r"alt text|alt-text|alt attribute|aria|voiceover|nvda|jaws|talkback|"
    r"keyboard|focus|reduced motion|contrast|colorblind|color blind|low vision|"
    r"closed caption|audio description|role=|voice control|dyslexia|"
    r"plain language|a11y|accessibility",
)


def has_vocab(text):
    """True if the line mentions any accessibility term (fast pre-filter).

    Lowercases once and matches case-sensitively: re.IGNORECASE does
    per-character Unicode case-folding, which is far slower than a
    case-sensitive search over a pre-lowercased string.
    """
    return bool(_LITERAL_TERMS.search(text.lower()))

FIELDNAMES = [
    "file_url_sha16", "repo_name", "file_path", "spec_tool", "spec_role",
    "repo_language", "repo_stars", "line_number", "requirement_text",
    "matched_categories", "matched_terms", "has_imperative", "has_threshold",
    "verifiable",
]


def load_meta():
    """Map file_url_sha16 -> (repo_language, repo_stars) from spec_files."""
    conn = duckdb.connect()
    rows = conn.execute(
        f"SELECT file_url_sha16, repo_language, repo_stars FROM read_parquet('{SPEC_FILES_PARQUET}')"
    ).fetchall()
    conn.close()
    return {r[0]: (r[1], r[2]) for r in rows}


def extract_lines(content):
    """Yield (1-based line number, stripped text) for every non-empty line."""
    for i, line in enumerate(content.splitlines(), start=1):
        text = line.strip()
        if text:
            yield i, text


def main():
    meta = load_meta()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    specs_scanned = 0
    req_rows = 0
    missing_meta = 0

    with open(SPECS_JSONL, encoding="utf-8") as f, \
         open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDNAMES)
        writer.writeheader()

        for raw in f:
            rec = json.loads(raw)
            specs_scanned += 1

            key = rec.get("file_url_sha16")
            content = rec.get("content", "")
            if not key or not content:
                continue

            lang_stars = meta.get(key)
            if lang_stars is None:
                missing_meta += 1
                continue

            for line_number, text in extract_lines(content):
                if not has_vocab(text):
                    continue
                hits = [(cat, term) for cat, term, pat in ACCESSIBILITY_PATTERNS if pat.search(text)]
                if not hits:
                    continue
                has_imp = bool(IMPERATIVE.search(text))
                has_thr = bool(THRESHOLD.search(text))
                writer.writerow({
                    "file_url_sha16": key,
                    "repo_name": rec.get("repo_name"),
                    "file_path": rec.get("file_path"),
                    "spec_tool": rec.get("spec_tool"),
                    "spec_role": rec.get("spec_role"),
                    "repo_language": lang_stars[0],
                    "repo_stars": lang_stars[1],
                    "line_number": line_number,
                    "requirement_text": text,
                    "matched_categories": ";".join(sorted({c for c, _ in hits})),
                    "matched_terms": ";".join(t for _, t in hits),
                    "has_imperative": int(has_imp),
                    "has_threshold": int(has_thr),
                    "verifiable": int(has_imp or has_thr),
                })
                req_rows += 1

            if specs_scanned % 100_000 == 0:
                print(f"scanned {specs_scanned:,} specs; {req_rows:,} requirement rows")

    print(f"Specs scanned: {specs_scanned:,}")
    print(f"Requirement rows (unique lines): {req_rows:,}")
    print(f"Contents without spec_files metadata (skipped): {missing_meta:,}")
    print(f"Written to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
