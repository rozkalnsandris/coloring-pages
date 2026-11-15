#!/usr/bin/env python3
"""Render two reviewed initial-HTML Hero sections, without generating routes (#590).

Editorial H1/intro/ancestors are source-reviewed separately from approved art.
Only the two existing indexed pages are in scope. All other page HTML is kept.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import sys

from render_landing_hero_static import image_fragment, marker
from validate_landing_hero_manifest import (
    ManifestValidationError, ROOT, exact_keys, parse_manifest,
    validate_manifest_text,
)

SOURCE = "metadata/landing-hero-sections.v1.json"
SCHEMA = "rozkalns.ausmalwiese.landing-hero-sections.v1"
ROUTES = {
    "fahrzeuge": {
        "namespace": "categories",
        "ancestors": (("/", "Startseite"),),
        "final": "Fahrzeuge",
        "section": "category-hero page-hero page-hero--category page-hero--with-art",
        "grid": "container page-hero-grid",
        "copy": "category-hero-copy page-hero-copy",
        "nav": "breadcrumbs category-breadcrumbs page-hero-breadcrumbs",
        "nav_indent": "        ",
        "art": 'class="page-hero-art"',
    },
    "herbst": {
        "namespace": "topics",
        "ancestors": (("/", "Startseite"), ("/jahreszeiten", "Jahreszeiten & Feste")),
        "final": "Herbst",
        "section": ("category-hero topic-landing-hero topic-landing-hero--static "
                    "topic-landing-hero--with-art page-hero page-hero--static "
                    "page-hero--with-art"),
        "grid": "container topic-landing-grid page-hero-grid",
        "copy": "category-hero-copy topic-landing-copy page-hero-copy",
        "nav": ("breadcrumbs category-breadcrumbs topic-landing-breadcrumbs "
                "page-hero-breadcrumbs"),
        "nav_indent": "          ",
        "art": 'class="topic-landing-art page-hero-art" data-topic-landing-art',
    },
}


def plain_text(text: object, label: str, max_chars: int) -> None:
    if (type(text) is not str or not (1 <= len(text) <= max_chars)
            or text.strip() != text
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in text)
            or any(ch in text for ch in "<>\"")):
        raise ManifestValidationError(label + ": unsafe or invalid editorial text")


def validate_sections_data(data: object) -> dict:
    exact_keys(data, {"schema", "pages"}, "static Hero editorial")
    if data["schema"] != SCHEMA:
        raise ManifestValidationError("unsupported static Hero editorial schema")
    pages = data["pages"]
    exact_keys(pages, set(ROUTES), "static Hero routes")
    for slug, variant in ROUTES.items():
        entry = pages[slug]
        exact_keys(entry, {"namespace", "heading", "intro", "breadcrumbs"}, slug)
        if entry["namespace"] != variant["namespace"]:
            raise ManifestValidationError(slug + ": unsupported namespace")
        plain_text(entry["heading"], slug + ".heading", 130)
        plain_text(entry["intro"], slug + ".intro", 420)
        crumbs = entry["breadcrumbs"]
        if type(crumbs) is not list or len(crumbs) != len(variant["ancestors"]) + 1:
            raise ManifestValidationError(slug + ": invalid breadcrumbs")
        for crumb, (href, label) in zip(crumbs[:-1], variant["ancestors"]):
            exact_keys(crumb, {"href", "label"}, slug + ".ancestor")
            if crumb["href"] != href or crumb["label"] != label:
                raise ManifestValidationError(slug + ": unreviewed breadcrumb ancestor")
        current = crumbs[-1]
        exact_keys(current, {"label"}, slug + ".current")
        if current["label"] != variant["final"]:
            raise ManifestValidationError(slug + ": unreviewed current breadcrumb")
    return data


def render_section(slug: str, editorial: dict, art: dict) -> str:
    variant = ROUTES[slug]
    indent = variant["nav_indent"]
    crumbs = []
    for crumb in editorial["breadcrumbs"][:-1]:
        crumbs.append('<li><a href="' + escape(crumb["href"], quote=True)
                     + '">' + escape(crumb["label"]) + '</a></li>')
    crumbs.append('<li><span aria-current="page">'
                 + escape(editorial["breadcrumbs"][-1]["label"]) + '</span></li>')
    lines = [
        f'    <section class="{variant["section"]}" aria-labelledby="category-title">',
        f'      <div class="{variant["grid"]}">',
        f'        <div class="{variant["copy"]}">',
        f'{indent}<nav class="{variant["nav"]}" aria-label="Breadcrumb">',
        f'{indent}  <ol>{"".join(crumbs)}</ol>',
        f'{indent}</nav>',
        f'{indent}<h1 id="category-title">{escape(editorial["heading"])}</h1>',
        f'{indent}<p>{escape(editorial["intro"])}</p>',
        '        </div>',
        f'        <div {variant["art"]}>',
        marker(variant["namespace"], slug, "start").rstrip("\n"),
        image_fragment(art).rstrip("\n"),
        marker(variant["namespace"], slug, "end").rstrip("\n"),
        '        </div>',
        '      </div>',
        '    </section>',
    ]
    return "\n".join(lines)


def replace_section(markup: str, slug: str, section: str) -> str:
    # Only the source-visible first Hero section may be replaced. Never
    # reconstruct head, editorial seed cards, catalogue, or other sections.
    prefix = '    <section class="category-hero'
    if markup.count(prefix) != 1 or markup.count('<h1 id="category-title">') != 1:
        raise ManifestValidationError(slug + ": missing or duplicate static Hero")
    start = markup.index(prefix)
    end = markup.find("    </section>", start)
    if end < 0:
        raise ManifestValidationError(slug + ": unterminated static Hero")
    end += len("    </section>")
    old = markup[start:end]
    if old.count("<section") != 1 or old.count("</section>") != 1:
        raise ManifestValidationError(slug + ": invalid Hero section boundary")
    return markup[:start] + section + markup[end:]


def build_pages(root: Path = ROOT) -> dict[str, str]:
    root = Path(root)
    source = validate_sections_data(
        parse_manifest((root / SOURCE).read_text(encoding="utf-8"))
    )
    approved_art = validate_manifest_text(
        (root / "metadata/landing-hero.v1.json").read_text(encoding="utf-8"),
        root,
    )
    output = {}
    for slug, variant in ROUTES.items():
        art = approved_art[variant["namespace"]][slug]
        path = root / (slug + ".html")
        if path.is_symlink() or not path.is_file():
            raise ManifestValidationError(slug + ": invalid static Hero route")
        markup = path.read_text(encoding="utf-8")
        output[path.name] = replace_section(
            markup, slug, render_section(slug, source["pages"][slug], art)
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Only compare reviewed generated sections, never write")
    args = parser.parse_args()
    try:
        output = build_pages()
        stale = [name for name, content in output.items()
                 if (ROOT / name).read_text(encoding="utf-8") != content]
        if args.check:
            if stale:
                print("Static Hero sections stale: " + ", ".join(stale), file=sys.stderr)
                return 1
            print("Static Hero sections match reviewed source")
            return 0
        for name in stale:
            (ROOT / name).write_text(output[name], encoding="utf-8")
        print("Reviewed static Hero sections; updated: "
              + (", ".join(stale) or "none"))
        return 0
    except (ManifestValidationError, OSError, UnicodeError, KeyError) as exc:
        print("Static Hero section generation failed: " + str(exc),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
