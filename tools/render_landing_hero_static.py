#!/usr/bin/env python3
"""Generate the two source-visible static Hero image fragments from approved art.

This is not a route generator. The reviewed HTML owns editorial copy, SEO,
breadcrumbs and gallery content. The validated source manifest owns art (#584).
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re
import sys

from validate_landing_hero_manifest import (
    ManifestValidationError, ROOT, validate_manifest_text,
)

TARGETS = (
    ("categories", "fahrzeuge", "fahrzeuge.html",
     '        <div class="page-hero-art">\n'),
    ("topics", "herbst", "herbst.html",
     '        <div class="topic-landing-art page-hero-art" data-topic-landing-art>\n'),
)


def marker(namespace: str, slug: str, edge: str) -> str:
    return f"        <!-- landing-hero:{namespace}.{slug}:{edge} -->\n"


def image_fragment(record: dict) -> str:
    return (
        f'          <img src="{escape(record["image"], quote=True)}"\n'
        f'               alt="{escape(record["alt"], quote=True)}"\n'
        f'               width="{record["width"]}" height="{record["height"]}" '
        'decoding="async" fetchpriority="high">\n'
    )


def render_page(markup: str, namespace: str, slug: str,
                record: dict, wrapper: str) -> str:
    """Change only the marked img fragment, with exact marker/wrapper guards."""
    start, end = marker(namespace, slug, "start"), marker(namespace, slug, "end")
    if markup.count(start) != 1 or markup.count(end) != 1:
        raise ManifestValidationError(slug + ": missing or duplicate Hero markers")
    existing_markers = re.findall(
        r"(?m)^        <!-- landing-hero:[^\n]+ -->\n", markup
    )
    if existing_markers != [start, end]:
        raise ManifestValidationError(slug + ": unrelated or reordered Hero markers")
    if markup.count(wrapper) != 1:
        raise ManifestValidationError(slug + ": missing or duplicate art wrapper")
    start_at = markup.index(start)
    if start_at != markup.index(wrapper) + len(wrapper):
        raise ManifestValidationError(slug + ": Hero marker is outside art wrapper")
    content_at = start_at + len(start)
    end_at = markup.index(end)
    if end_at < content_at or not markup[end_at + len(end):].startswith("        </div>\n"):
        raise ManifestValidationError(slug + ": malformed Hero fragment boundary")
    old_fragment = markup[content_at:end_at]
    if old_fragment.count("<img ") != 1 or "</" in old_fragment:
        raise ManifestValidationError(slug + ": unexpected existing art markup")
    return markup[:content_at] + image_fragment(record) + markup[end_at:]


def build_pages(root: Path = ROOT) -> dict[str, str]:
    """Validate complete reviewed metadata and both existing static pages."""
    root = Path(root)
    data = validate_manifest_text(
        (root / "metadata/landing-hero.v1.json").read_text(encoding="utf-8"),
        root,
    )
    if (set(data["categories"]) != {"fahrzeuge"}
            or set(data["topics"]) != {"herbst"}):
        raise ManifestValidationError("unexpected static Hero records; review new scope")
    output = {}
    for namespace, slug, name, wrapper in TARGETS:
        source = (root / name).read_text(encoding="utf-8")
        output[name] = render_page(source, namespace, slug,
                                   data[namespace][slug], wrapper)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Read-only check against committed source-visible HTML")
    args = parser.parse_args()
    try:
        expected = build_pages()
        stale = [name for name, result in expected.items()
                 if (ROOT / name).read_text(encoding="utf-8") != result]
        if args.check:
            if stale:
                print("Stale static Hero art: " + ", ".join(stale), file=sys.stderr)
                return 1
            print("Static Hero art matches reviewed manifest")
            return 0
        for name in stale:
            (ROOT / name).write_text(expected[name], encoding="utf-8")
        print("Validated static Hero art; updated: " + (", ".join(stale) or "none"))
        return 0
    except (ManifestValidationError, OSError, UnicodeError) as exc:
        print("Static Hero generation failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
