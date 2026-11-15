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
WIDTHS = (320, 390, 412, 768, 1440)
ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["herbst"]
BAUERNHOF_ART = json.loads(
    (ROOT / "metadata/landing-hero.v1.json").read_text(encoding="utf-8")
)["topics"]["bauernhof"]
TOPICS = {
    "schema": "rozkalns.coloring-pages.topics.v2",
    "revision": 1,
    "topics": [
        {"id": "herbst", "label": "Herbst", "icon": "🍂",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "bauernhof", "label": "Bauernhof", "icon": "🚜",
         "kind": "evergreen", "legacy_terms": []},
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
        # Selecting Herbst navigates to the separate canonical /herbst route.
        # Test the managed browse Hero using same-document history instead.
        page.go_back()
        assert_reviewed_herbst(page, width)
        page.go_forward()
        assert_reviewed_bauernhof(page, width)
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
        assert_reviewed_bauernhof(page, width)
        page.go_back()
        assert_reviewed_herbst(page, width)
        page.go_forward()
        assert_reviewed_bauernhof(page, width)
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


def main() -> None:
    from playwright.sync_api import sync_playwright

    with server() as port, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            origin = f"http://127.0.0.1:{port}"
            for width in WIDTHS:
                case(browser, origin, width)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
