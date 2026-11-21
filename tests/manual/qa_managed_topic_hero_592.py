#!/usr/bin/env python3
"""#592: Chromium real-DOM Hero art/fallback transitions with managed Topics.

Uses only local source + fixed test fixtures; does not access LIVE or create routes.
"""
from __future__ import annotations

import json
from pathlib import Path

from qa_responsive_layout_511 import (  # same-directory, reviewed local QA utilities
    CATEGORIES_FIXTURE, assert_inside_viewport, server,
)

ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (320, 390, 412, 720, 721, 768, 1440, 1920)
ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["herbst"]
BAUERNHOF_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["bauernhof"]
WEIHNACHTEN_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["weihnachten"]
DINOSAURIER_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["dinosaurier"]
WELTRAUM_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["weltraum"]
BLUMEN_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["blumen"]
MEERESTIERE_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["meerestiere"]
SPORT_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["sport"]
EINHOERNER_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["einhoerner"]
WINTER_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["winter"]
ADVENT_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["advent"]
TOPICS = {
    "schema": "rozkalns.coloring-pages.topics.v2",
    "revision": 1,
    "topics": [
        {"id": "herbst", "label": "Herbst", "icon": "🍂",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "bauernhof", "label": "Bauernhof", "icon": "🚜",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "blumen", "label": "Blumen", "icon": "🌸",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "meerestiere", "label": "Meerestiere", "icon": "🐠",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "sport", "label": "Sport", "icon": "⚽",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "einhoerner", "label": "Einhörner", "icon": "🦄",
         "kind": "evergreen", "legacy_terms": ["einhorn", "einhörner", "einhoerner"]},
        {"id": "winter", "label": "Winter", "icon": "❄️",
         "kind": "seasonal", "active_from": "12-01", "active_to": "02-29",
         "legacy_terms": ["winter", "schnee", "schneemann", "schneeflocke"]},
        {"id": "advent", "label": "Advent", "icon": "🕯️",
         "kind": "seasonal", "active_from": "11-20", "active_to": "12-24",
         "legacy_terms": ["advent", "adventskranz", "kerze", "kerzen"]},
        {"id": "weltraum", "label": "Weltraum", "icon": "🚀",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "dinosaurier", "label": "Dinosaurier", "icon": "🦖",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "weihnachten", "label": "Weihnachten", "icon": "🎄",
         "kind": "seasonal", "active_from": "11-20", "active_to": "12-26",
         "legacy_terms": []},
        {"id": "tanzen", "label": "Tanzen", "icon": "🎶",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "maerchen-abenteuer", "label": "Märchen & Abenteuer",
         "icon": "📚", "kind": "evergreen", "legacy_terms": []},
    ],
}
CATALOG = [
    {"id": "hero-qa-herbst", "title": "Herbst-Motiv", "category": "jahreszeiten",
     "age": "3-6", "difficulty": "easy", "topics": ["herbst"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-herbst/print.png"},
    {"id": "hero-qa-bauernhof", "title": "Bauernhof-Motiv", "category": "tiere",
     "age": "3-6", "difficulty": "easy", "topics": ["bauernhof"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-bauernhof/print.png"},
    {"id": "hero-qa-blumen", "title": "Blumen-Motiv", "category": "natur",
     "age": "3-6", "difficulty": "easy", "topics": ["blumen"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-blumen/print.png"},
    {"id": "hero-qa-meerestiere", "title": "Meerestiere-Motiv", "category": "tiere",
     "age": "3-6", "difficulty": "easy", "topics": ["meerestiere"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-meerestiere/print.png"},
    {"id": "hero-qa-sport", "title": "Sport-Motiv", "category": "figuren",
     "age": "3-6", "difficulty": "easy", "topics": ["sport"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-sport/print.png"},
    {"id": "hero-qa-einhoerner", "title": "Einhörner-Motiv", "category": "figuren",
     "age": "3-6", "difficulty": "easy", "topics": ["einhoerner"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-einhoerner/print.png"},
    {"id": "hero-qa-winter", "title": "Winter-Motiv", "category": "jahreszeiten",
     "age": "3-6", "difficulty": "easy", "topics": ["winter"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-winter/print.png"},
    {"id": "hero-qa-advent", "title": "Advent-Motiv", "category": "jahreszeiten",
     "age": "3-6", "difficulty": "easy", "topics": ["advent"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-advent/print.png"},
    {"id": "hero-qa-weltraum", "title": "Weltraum-Motiv", "category": "figuren",
     "age": "3-6", "difficulty": "easy", "topics": ["weltraum"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-weltraum/print.png"},
    {"id": "hero-qa-dinosaurier", "title": "Dinosaurier-Motiv", "category": "tiere",
     "age": "3-6", "difficulty": "easy", "topics": ["dinosaurier"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-dinosaurier/print.png"},
    {"id": "hero-qa-weihnachten", "title": "Weihnachten-Motiv", "category": "jahreszeiten",
     "age": "3-6", "difficulty": "easy", "topics": ["weihnachten"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-weihnachten/print.png"},
    {"id": "hero-qa-tanzen", "title": "Tanzen-Motiv", "category": "figuren",
     "age": "3-6", "difficulty": "easy", "topics": ["tanzen"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-tanzen/print.png"},
    {"id": "hero-qa-maerchen", "title": "Märchen-Motiv", "category": "figuren",
     "age": "3-6", "difficulty": "easy", "topics": ["maerchen-abenteuer"],
     "thumb": "/assets/favicon.svg", "print": "/media/hero-qa-maerchen/print.png"},
]


def wait_title(page, expected: str) -> None:
    page.wait_for_function(
        "(expected) => document.querySelector('[data-focused-topic-title]')"
        "?.textContent.trim() === expected", arg=expected,
    )


def assert_layout(page, width: int, state: str) -> None:
    actual = page.evaluate(
        """() => ({
          width: innerWidth,
          html: document.documentElement.scrollWidth,
          body: document.body.scrollWidth,
        })"""
    )
    if (actual["width"] != width or actual["html"] > width + 1
            or actual["body"] > width + 1):
        raise AssertionError(f"{width}px {state}: horizontal overflow {actual}")
    assert_inside_viewport(page, "[data-focused-topic-hero]", width)
    if page.locator("main h1:visible").count() != 1:
        raise AssertionError(f"{width}px {state}: expected one visible main H1")
    if page.locator("[data-filter-topic]").count() != 1:
        raise AssertionError(f"{width}px {state}: duplicate Topic selector")


def assert_reviewed_herbst(page, width: int) -> None:
    wait_title(page, "Herbst Ausmalbilder")
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if not hero.is_visible() or page.locator("#hero").is_visible():
        raise AssertionError(f"{width}px approved Topic Hero missing/duplicated")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
        " && node.getAttribute('aria-labelledby') === 'focused-topic-title'"
    ):
        raise AssertionError(f"{width}px approved Hero semantics missing")
    if not image.is_visible() or image.count() != 1:
        raise AssertionError(f"{width}px approved art missing/duplicated")
    if (image.get_attribute("src") != ART["image"]
            or image.get_attribute("alt") != ART["alt"]
            or image.get_attribute("width") != str(ART["width"])
            or image.get_attribute("height") != str(ART["height"])):
        raise AssertionError(f"{width}px image attributes differ from approved art")
    intro = page.locator("[data-focused-topic-intro]")
    if not intro.is_visible() or intro.inner_text() != ART["intro"]:
        raise AssertionError(f"{width}px reviewed Herbst intro missing")
    if (page.locator("[data-focused-topic-breadcrumb]").inner_text()
            != "Herbst"):
        raise AssertionError(f"{width}px Herbst breadcrumb incorrect")
    if page.locator("[data-filter-topic]").input_value() != "herbst":
        raise AssertionError(f"{width}px selector lost managed Herbst state")
    if page.locator(".header-search").get_attribute("href") != "/#hero":
        raise AssertionError(f"{width}px header search must return to home")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art = image.bounding_box()
        if not title or not art or art["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px art overlaps mobile H1")
    assert_layout(page, width, "herbst")


def assert_reviewed_bauernhof(page, width: int) -> None:
    wait_title(page, "Bauernhof Ausmalbilder")
    art = BAUERNHOF_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Bauernhof art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Bauernhof missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Bauernhof {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Bauernhof"
            or page.locator("[data-filter-topic]").input_value() != "bauernhof"):
        raise AssertionError(f"{width}px Bauernhof intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Bauernhof art overlaps mobile heading")
    assert_layout(page, width, "bauernhof")


def assert_reviewed_weihnachten(page, width: int) -> None:
    wait_title(page, "Weihnachten Ausmalbilder")
    art = WEIHNACHTEN_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Weihnachten art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Weihnachten missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Weihnachten {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Weihnachten"
            or page.locator("[data-filter-topic]").input_value() != "weihnachten"):
        raise AssertionError(f"{width}px Weihnachten intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Weihnachten art overlaps mobile heading")
    assert_layout(page, width, "weihnachten")


def assert_reviewed_dinosaurier(page, width: int) -> None:
    wait_title(page, "Dinosaurier Ausmalbilder")
    art = DINOSAURIER_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Dinosaurier art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Dinosaurier missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Dinosaurier {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Dinosaurier"
            or page.locator("[data-filter-topic]").input_value() != "dinosaurier"):
        raise AssertionError(f"{width}px Dinosaurier intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Dinosaurier art overlaps mobile heading")
    assert_layout(page, width, "dinosaurier")


def assert_reviewed_weltraum(page, width: int) -> None:
    wait_title(page, "Weltraum Ausmalbilder")
    art = WELTRAUM_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Weltraum art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Weltraum missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Weltraum {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Weltraum"
            or page.locator("[data-filter-topic]").input_value() != "weltraum"):
        raise AssertionError(f"{width}px Weltraum intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Weltraum art overlaps mobile heading")
    assert_layout(page, width, "weltraum")


def assert_reviewed_blumen(page, width: int) -> None:
    wait_title(page, "Blumen Ausmalbilder")
    art = BLUMEN_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Blumen art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Blumen missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Blumen {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Blumen"
            or page.locator("[data-filter-topic]").input_value() != "blumen"):
        raise AssertionError(f"{width}px Blumen intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Blumen art overlaps mobile heading")
    assert_layout(page, width, "blumen")


def assert_reviewed_meerestiere(page, width: int) -> None:
    wait_title(page, "Meerestiere Ausmalbilder")
    art = MEERESTIERE_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Meerestiere art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Meerestiere missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Meerestiere {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Meerestiere"
            or page.locator("[data-filter-topic]").input_value() != "meerestiere"):
        raise AssertionError(f"{width}px Meerestiere intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Meerestiere art overlaps mobile heading")
    assert_layout(page, width, "meerestiere")


def assert_reviewed_sport(page, width: int) -> None:
    wait_title(page, "Sport Ausmalbilder")
    art = SPORT_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Sport art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Sport missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Sport {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Sport"
            or page.locator("[data-filter-topic]").input_value() != "sport"):
        raise AssertionError(f"{width}px Sport intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Sport art overlaps mobile heading")
    assert_layout(page, width, "sport")


def assert_reviewed_einhoerner(page, width: int) -> None:
    wait_title(page, "Einhörner Ausmalbilder")
    art = EINHOERNER_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Einhörner art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Einhörner missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Einhörner {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Einhörner"
            or page.locator("[data-filter-topic]").input_value() != "einhoerner"):
        raise AssertionError(f"{width}px Einhörner intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Einhörner art overlaps mobile heading")
    assert_layout(page, width, "einhoerner")


def assert_reviewed_winter(page, width: int) -> None:
    wait_title(page, "Winter Ausmalbilder")
    art = WINTER_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Winter art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Winter missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Winter {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Winter"
            or page.locator("[data-filter-topic]").input_value() != "winter"):
        raise AssertionError(f"{width}px Winter intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Winter art overlaps mobile heading")
    assert_layout(page, width, "winter")


def assert_reviewed_advent(page, width: int) -> None:
    wait_title(page, "Advent Ausmalbilder")
    art = ADVENT_ART
    image = page.locator("[data-focused-topic-art] img")
    page.wait_for_function(
        """() => {
          const img = document.querySelector('[data-focused-topic-art] img');
          return img && img.complete && img.naturalWidth === 1755
            && img.naturalHeight === 896;
        }"""
    )
    hero = page.locator("[data-focused-topic-hero]")
    if (not hero.is_visible() or page.locator("#hero").is_visible()
            or image.count() != 1 or not image.is_visible()):
        raise AssertionError(f"{width}px Advent art/hero missing")
    if not hero.evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px Advent missing approved art class")
    for key, expected in (("src", art["image"]), ("alt", art["alt"]),
                          ("width", str(art["width"])),
                          ("height", str(art["height"]))):
        if image.get_attribute(key) != expected:
            raise AssertionError(f"{width}px Advent {key} differs from manifest")
    if (not page.locator("[data-focused-topic-intro]").is_visible()
            or page.locator("[data-focused-topic-intro]").inner_text() != art["intro"]
            or page.locator("[data-focused-topic-breadcrumb]").inner_text() != "Advent"
            or page.locator("[data-filter-topic]").input_value() != "advent"):
        raise AssertionError(f"{width}px Advent intro/breadcrumb/selector mismatch")
    assert_inside_viewport(
        page, "[data-focused-topic-hero], [data-focused-topic-art], "
        "[data-focused-topic-art] img", width,
    )
    if width <= 720:
        title = page.locator("[data-focused-topic-title]").bounding_box()
        art_box = image.bounding_box()
        if not title or not art_box or art_box["y"] < title["y"] + title["height"] - 1:
            raise AssertionError(f"{width}px Advent art overlaps mobile heading")
    assert_layout(page, width, "advent")


def assert_label_only(page, width: int, slug: str, label: str) -> None:
    wait_title(page, label + " Ausmalbilder")
    if not page.locator("[data-focused-topic-hero]").is_visible():
        raise AssertionError(f"{width}px {slug}: managed label-only Hero hidden")
    if page.locator("#hero").is_visible():
        raise AssertionError(f"{width}px {slug}: duplicate home Hero")
    if page.locator("[data-focused-topic-breadcrumb]").inner_text() != label:
        raise AssertionError(f"{width}px {slug}: label breadcrumb mismatch")
    if page.locator("[data-focused-topic-intro]").is_visible():
        raise AssertionError(f"{width}px {slug}: invented editorial text")
    if page.locator("[data-focused-topic-art]").is_visible():
        raise AssertionError(f"{width}px {slug}: unrelated art container visible")
    if page.locator("[data-focused-topic-art] img").count():
        raise AssertionError(f"{width}px {slug}: stale approved image")
    if page.locator("[data-focused-topic-hero]").evaluate(
        "(node) => node.classList.contains('topic-landing-hero--with-art')"
    ):
        raise AssertionError(f"{width}px {slug}: stale art CSS modifier")
    if page.locator("[data-filter-topic]").input_value() != slug:
        raise AssertionError(f"{width}px {slug}: Topic selector not updated")
    if page.locator("[data-gallery-topic-actions]").is_hidden():
        raise AssertionError(f"{width}px {slug}: managed gallery controls missing")
    if page.locator(".header-search").get_attribute("href") != "/#hero":
        raise AssertionError(f"{width}px {slug}: header search link incorrect")
    assert_layout(page, width, slug)


def case(browser, origin: str, width: int) -> None:
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        for suffix, payload in (
            ("catalog.json", CATALOG),
            ("categories.json", CATEGORIES_FIXTURE),
            ("topics.json", TOPICS),
        ):
            page.route("**/" + suffix, lambda route, _request, data=payload: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps(data, ensure_ascii=False),
            ))
        page.goto(
            origin + "/index.html?topic=herbst&campaign=hero-qa",
            wait_until="domcontentloaded",
        )
        assert_reviewed_herbst(page, width)

        chooser = page.locator("[data-filter-topic]")
        chooser.select_option("bauernhof")
        assert_reviewed_bauernhof(page, width)
        chooser.select_option("dinosaurier")
        assert_reviewed_dinosaurier(page, width)
        chooser.select_option("weltraum")
        assert_reviewed_weltraum(page, width)
        chooser.select_option("blumen")
        assert_reviewed_blumen(page, width)
        chooser.select_option("meerestiere")
        assert_reviewed_meerestiere(page, width)
        chooser.select_option("weihnachten")
        assert_reviewed_weihnachten(page, width)
        # Selecting Herbst navigates to the separate canonical /herbst route.
        # Test the managed browse Hero using same-document history instead.
        page.go_back()
        assert_reviewed_meerestiere(page, width)
        page.go_back()
        assert_reviewed_blumen(page, width)
        page.go_back()
        assert_reviewed_weltraum(page, width)
        page.go_back()
        assert_reviewed_dinosaurier(page, width)
        page.go_back()
        assert_reviewed_bauernhof(page, width)
        page.go_back()
        assert_reviewed_herbst(page, width)
        page.go_forward()
        assert_reviewed_bauernhof(page, width)
        page.go_forward()
        assert_reviewed_dinosaurier(page, width)
        page.go_forward()
        assert_reviewed_weltraum(page, width)
        page.go_forward()
        assert_reviewed_blumen(page, width)
        page.go_forward()
        assert_reviewed_meerestiere(page, width)
        page.go_forward()
        assert_reviewed_weihnachten(page, width)
        chooser.select_option("tanzen")
        assert_label_only(page, width, "tanzen", "Tanzen")
        if "topic=tanzen" not in page.url or "campaign=hero-qa" not in page.url:
            raise AssertionError(f"{width}px Topic/campaign URL lost")
        chooser.select_option("maerchen-abenteuer")
        assert_label_only(page, width, "maerchen-abenteuer", "Märchen & Abenteuer")

        # Back/Forward are real popstate transitions, not synthetic DOM mocks.
        page.go_back()
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_weihnachten(page, width)
        page.go_back()
        assert_reviewed_meerestiere(page, width)
        page.go_back()
        assert_reviewed_blumen(page, width)
        page.go_back()
        assert_reviewed_weltraum(page, width)
        page.go_back()
        assert_reviewed_dinosaurier(page, width)
        page.go_back()
        assert_reviewed_bauernhof(page, width)
        page.go_back()
        assert_reviewed_herbst(page, width)
        page.go_forward()
        assert_reviewed_bauernhof(page, width)
        page.go_forward()
        assert_reviewed_dinosaurier(page, width)
        page.go_forward()
        assert_reviewed_weltraum(page, width)
        page.go_forward()
        assert_reviewed_blumen(page, width)
        page.go_forward()
        assert_reviewed_meerestiere(page, width)
        page.go_forward()
        assert_reviewed_weihnachten(page, width)
        page.go_forward()
        assert_label_only(page, width, "tanzen", "Tanzen")

        chooser.select_option("")
        page.wait_for_function(
            "() => !document.querySelector('[data-focused-topic-hero]')?.hidden"
            " === false && !document.querySelector('#hero')?.hidden"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px unfiltered home retained Topic art")

        page.goto(origin + "/index.html?topic=not-managed", wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if page.locator("[data-focused-topic-hero]").is_visible():
            raise AssertionError(f"{width}px unknown Topic fabricated Hero")
        if page.locator("[data-focused-topic-art] img").count():
            raise AssertionError(f"{width}px unknown Topic inherited approved artwork")
        if page.locator("[data-filter-topic]").input_value():
            raise AssertionError(f"{width}px unknown Topic accepted by chooser")
        if not page.locator("#hero").is_visible():
            raise AssertionError(f"{width}px unknown Topic did not fall back home")
        print(f"Topic Hero Chromium {width}px: approved/fallback/history/unknown PASS")
    finally:
        page.close()




def sport_case(browser, origin: str, width: int) -> None:
    """#613: verified Sport art, browsing and Back/Forward transitions."""
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        for suffix, payload in (
            ("catalog.json", CATALOG),
            ("categories.json", CATEGORIES_FIXTURE),
            ("topics.json", TOPICS),
        ):
            page.route("**/" + suffix, lambda route, _request, data=payload: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps(data, ensure_ascii=False),
            ))
        page.goto(origin + "/index.html?topic=sport&campaign=hero-qa",
                  wait_until="domcontentloaded")
        assert_reviewed_sport(page, width)
        chooser = page.locator("[data-filter-topic]")
        chooser.select_option("tanzen")
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_sport(page, width)
        page.go_forward()
        assert_label_only(page, width, "tanzen", "Tanzen")
        chooser.select_option("meerestiere")
        assert_reviewed_meerestiere(page, width)
        page.go_back()
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_sport(page, width)
        chooser.select_option("")
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px Sport art leaked into unfiltered home")
        page.goto(origin + "/index.html?topic=unknown-sport",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px invalid Sport topic fabricated a Hero")
        print(f"Sport Topic Hero {width}px: approved/history/fallback PASS")
    finally:
        page.close()

def einhoerner_case(browser, origin: str, width: int) -> None:
    """#615: verified Einhörner art, browsing and Back/Forward transitions."""
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        for suffix, payload in (
            ("catalog.json", CATALOG),
            ("categories.json", CATEGORIES_FIXTURE),
            ("topics.json", TOPICS),
        ):
            page.route("**/" + suffix, lambda route, _request, data=payload: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps(data, ensure_ascii=False),
            ))
        page.goto(origin + "/index.html?topic=einhoerner&campaign=hero-qa",
                  wait_until="domcontentloaded")
        assert_reviewed_einhoerner(page, width)
        chooser = page.locator("[data-filter-topic]")
        label = page.locator('label[for="filter-topic"]')
        if (not label.is_visible() or label.inner_text().strip() != "Thema"
                or chooser.evaluate("el => el.tagName") != "SELECT"):
            raise AssertionError(f"{width}px Einhörner native Thema selector missing")
        chooser.focus()
        if not chooser.evaluate("el => document.activeElement === el"):
            raise AssertionError(f"{width}px Einhörner keyboard focus missing")
        chooser.select_option("tanzen")
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_einhoerner(page, width)
        page.go_forward()
        assert_label_only(page, width, "tanzen", "Tanzen")
        chooser.select_option("meerestiere")
        assert_reviewed_meerestiere(page, width)
        page.go_back()
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_einhoerner(page, width)
        chooser.select_option("")
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px Einhörner art leaked into unfiltered home")
        page.goto(origin + "/index.html?topic=unknown-einhoerner",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px invalid Einhörner topic fabricated a Hero")
        # Source-approved art cannot register a Topic absent from runtime.
        page.unroute("**/topics.json")
        no_unicorns = dict(TOPICS)
        no_unicorns["topics"] = [
            item for item in TOPICS["topics"] if item["id"] != "einhoerner"
        ]
        page.route("**/topics.json", lambda route, _request: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(no_unicorns, ensure_ascii=False),
        ))
        page.goto(origin + "/index.html?topic=einhoerner",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()
                or page.locator("[data-filter-topic]").input_value()):
            raise AssertionError(f"{width}px unregistered Einhörner Topic created art")
        print(f"Einhörner Topic Hero {width}px: approved/history/fallback PASS")
    finally:
        page.close()

def winter_case(browser, origin: str, width: int) -> None:
    """#617: verified Winter art, browsing and Back/Forward transitions."""
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        for suffix, payload in (
            ("catalog.json", CATALOG),
            ("categories.json", CATEGORIES_FIXTURE),
            ("topics.json", TOPICS),
        ):
            page.route("**/" + suffix, lambda route, _request, data=payload: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps(data, ensure_ascii=False),
            ))
        page.goto(origin + "/index.html?topic=winter&campaign=hero-qa",
                  wait_until="domcontentloaded")
        assert_reviewed_winter(page, width)
        chooser = page.locator("[data-filter-topic]")
        label = page.locator('label[for="filter-topic"]')
        if (not label.is_visible() or label.inner_text().strip() != "Thema"
                or chooser.evaluate("el => el.tagName") != "SELECT"):
            raise AssertionError(f"{width}px Winter native Thema selector missing")
        chooser.focus()
        if not chooser.evaluate("el => document.activeElement === el"):
            raise AssertionError(f"{width}px Winter keyboard focus missing")
        chooser.select_option("tanzen")
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_winter(page, width)
        page.go_forward()
        assert_label_only(page, width, "tanzen", "Tanzen")
        chooser.select_option("meerestiere")
        assert_reviewed_meerestiere(page, width)
        page.go_back()
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_winter(page, width)
        chooser.select_option("")
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px Winter art leaked into unfiltered home")
        page.goto(origin + "/index.html?topic=unknown-winter",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px invalid Winter topic fabricated a Hero")
        # Source-approved art cannot register a Topic absent from runtime.
        page.unroute("**/topics.json")
        no_winter = dict(TOPICS)
        no_winter["topics"] = [
            item for item in TOPICS["topics"] if item["id"] != "winter"
        ]
        page.route("**/topics.json", lambda route, _request: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(no_winter, ensure_ascii=False),
        ))
        page.goto(origin + "/index.html?topic=winter",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()
                or page.locator("[data-filter-topic]").input_value()):
            raise AssertionError(f"{width}px unregistered Winter Topic created art")
        print(f"Winter Topic Hero {width}px: approved/history/fallback PASS")
    finally:
        page.close()

def advent_case(browser, origin: str, width: int) -> None:
    """#619: verified Advent art, browsing and Back/Forward transitions."""
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        for suffix, payload in (
            ("catalog.json", CATALOG),
            ("categories.json", CATEGORIES_FIXTURE),
            ("topics.json", TOPICS),
        ):
            page.route("**/" + suffix, lambda route, _request, data=payload: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps(data, ensure_ascii=False),
            ))
        page.goto(origin + "/index.html?topic=advent&campaign=hero-qa",
                  wait_until="domcontentloaded")
        assert_reviewed_advent(page, width)
        chooser = page.locator("[data-filter-topic]")
        label = page.locator('label[for="filter-topic"]')
        if (not label.is_visible() or label.inner_text().strip() != "Thema"
                or chooser.evaluate("el => el.tagName") != "SELECT"):
            raise AssertionError(f"{width}px Advent native Thema selector missing")
        chooser.focus()
        if not chooser.evaluate("el => document.activeElement === el"):
            raise AssertionError(f"{width}px Advent keyboard focus missing")
        chooser.select_option("tanzen")
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_advent(page, width)
        page.go_forward()
        assert_label_only(page, width, "tanzen", "Tanzen")
        chooser.select_option("meerestiere")
        assert_reviewed_meerestiere(page, width)
        page.go_back()
        assert_label_only(page, width, "tanzen", "Tanzen")
        page.go_back()
        assert_reviewed_advent(page, width)
        chooser.select_option("")
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px Advent art leaked into unfiltered home")
        page.goto(origin + "/index.html?topic=unknown-advent",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()):
            raise AssertionError(f"{width}px invalid Advent topic fabricated a Hero")
        # Source-approved art cannot register a Topic absent from runtime.
        page.unroute("**/topics.json")
        no_advent = dict(TOPICS)
        no_advent["topics"] = [
            item for item in TOPICS["topics"] if item["id"] != "advent"
        ]
        page.route("**/topics.json", lambda route, _request: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(no_advent, ensure_ascii=False),
        ))
        page.goto(origin + "/index.html?topic=advent",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-filter-topic]')?.disabled === false"
        )
        if (page.locator("[data-focused-topic-art] img").count()
                or page.locator("[data-focused-topic-hero]").is_visible()
                or not page.locator("#hero").is_visible()
                or page.locator("[data-filter-topic]").input_value()):
            raise AssertionError(f"{width}px unregistered Advent Topic created art")
        print(f"Advent Topic Hero {width}px: approved/history/fallback PASS")
    finally:
        page.close()

def assert_accessibility_context(browser, origin: str, width: int,
                                 dpr: int, forced: bool) -> None:
    """#610: independent DPR/forced-color coverage, not native browser zoom."""
    context = browser.new_context(
        viewport={"width": width, "height": 1000},
        device_scale_factor=dpr,
        forced_colors="active" if forced else "none",
    )
    page = context.new_page()
    mode = f"{width}px DPR={dpr} forced-colors={forced}"
    try:
        for suffix, payload in (
            ("catalog.json", CATALOG),
            ("categories.json", CATEGORIES_FIXTURE),
            ("topics.json", TOPICS),
        ):
            page.route("**/" + suffix, lambda route, _request, data=payload: route.fulfill(
                status=200, content_type="application/json",
                body=json.dumps(data, ensure_ascii=False),
            ))

        def check_page(expected_image: str) -> None:
            metrics = page.evaluate("""() => ({
                width: innerWidth,
                dpr: devicePixelRatio,
                forced: matchMedia('(forced-colors: active)').matches,
                doc: document.documentElement.scrollWidth,
                body: document.body.scrollWidth,
            })""")
            if (metrics["width"] != width or metrics["dpr"] != dpr
                    or metrics["forced"] != forced
                    or metrics["doc"] > width + 1 or metrics["body"] > width + 1):
                raise AssertionError(f"{mode}: viewport/mode/overflow drift {metrics}")
            hero = page.locator(".page-hero:visible").first
            image = page.locator(expected_image)
            if not hero.is_visible() or image.count() != 1 or not image.is_visible():
                raise AssertionError(f"{mode}: approved Hero/image missing")
            page.wait_for_function(
                """selector => {
                  const img = document.querySelector(selector);
                  return img && img.complete && img.naturalWidth > 0;
                }""", arg=expected_image,
            )
            if not (image.get_attribute("alt") or "").strip():
                raise AssertionError(f"{mode}: approved Hero image lost alt text")
            assert_inside_viewport(page, ".page-hero:visible", width)
            assert_inside_viewport(page, expected_image, width)
            if forced:
                appearance = hero.evaluate(
                    """el => {
                      const style = getComputedStyle(el);
                      return {color: style.color, background: style.backgroundColor};
                    }"""
                )
                mask = image.evaluate("el => getComputedStyle(el).maskImage")
                if (appearance["color"] == appearance["background"]
                        or appearance["background"] == "rgba(0, 0, 0, 0)"
                        or mask != "none"):
                    raise AssertionError(
                        f"{mode}: unreadable forced colors/masked artwork "
                        f"{appearance}, mask={mask}"
                    )

        for route, selector in (
            ("/index.html", "#hero .page-hero-art img"),
            ("/herbst.html", ".page-hero--static .page-hero-art img"),
            ("/fahrzeuge.html", ".page-hero--category .page-hero-art img"),
        ):
            page.goto(origin + route, wait_until="domcontentloaded")
            check_page(selector)
            if page.locator("main h1:visible").count() != 1:
                raise AssertionError(f"{mode}: static/home H1 count on {route}")

        page.goto(origin + "/index.html?topic=bauernhof&campaign=hero-qa",
                  wait_until="domcontentloaded")
        assert_reviewed_bauernhof(page, width)
        check_page("[data-focused-topic-art] img")
        selector = page.locator("[data-filter-topic]")
        label = page.locator('label[for="filter-topic"]')
        if (not selector.is_visible() or not label.is_visible()
                or label.inner_text().strip() != "Thema"
                or selector.evaluate("el => el.tagName") != "SELECT"):
            raise AssertionError(f"{mode}: native Thema control/label missing")
        bounds = selector.bounding_box()
        if not bounds or bounds["height"] < 44:
            raise AssertionError(f"{mode}: Thema touch target below 44px")
        selector.focus()
        if not selector.evaluate("el => document.activeElement === el"):
            raise AssertionError(f"{mode}: Thema keyboard focus missing")
        selector.select_option("tanzen")
        assert_label_only(page, width, "tanzen", "Tanzen")
        if page.locator("[data-focused-topic-art] img").count():
            raise AssertionError(f"{mode}: stale image in label-only fallback")
        print(f"PASS Hero context {mode}: home/static/managed/fallback")
    finally:
        context.close()


def main() -> None:
    from playwright.sync_api import sync_playwright

    with server() as port, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            origin = f"http://127.0.0.1:{port}"
            for width in WIDTHS:
                case(browser, origin, width)
            for width in (320, 390, 412, 768, 1440):
                sport_case(browser, origin, width)
            for width in (320, 390, 412, 768, 1440):
                einhoerner_case(browser, origin, width)
            for width in (320, 390, 412, 768, 1440):
                winter_case(browser, origin, width)
            for width in (320, 390, 412, 768, 1440):
                advent_case(browser, origin, width)
            # Representative mode checks are deliberately separate from the full matrix.
            for width in (390, 721, 1440):
                assert_accessibility_context(browser, origin, width, dpr=2, forced=False)
            for width in (390, 721):
                assert_accessibility_context(browser, origin, width, dpr=1, forced=True)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
