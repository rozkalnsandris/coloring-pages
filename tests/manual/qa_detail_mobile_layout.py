#!/usr/bin/env python3
"""Chromium regression for mobile detail topic, actions and related cards.

Uses synthetic catalog/topics and local static assets only: no LIVE access,
real-media download, printing, analytics mutation or production writes.
"""
from __future__ import annotations

import json

from qa_responsive_layout_511 import assert_inside_viewport, server

WIDTHS = (320, 360, 390, 412, 540, 720, 768, 1440)
CURRENT = {
    "id": "mobile-detail-1", "title": "Junge im Bagger",
    "category": "fahrzeuge", "topics": ["baufahrzeuge"],
    "character": "Junge", "age": "3-6",
    "difficulty": "easy", "thumb": "/assets/favicon.svg",
    "preview": "/assets/favicon.svg", "print": "/assets/favicon.svg",
}
RELATED = {
    "id": "mobile-detail-2", "title": "Bagger auf der Baustelle",
    "category": "fahrzeuge", "topics": ["baufahrzeuge"],
    "age": "3-6", "difficulty": "easy",
    "thumb": "/assets/favicon.svg", "preview": "/assets/favicon.svg",
    "print": "/assets/favicon.svg",
}
TOPICS = {
    "schema": "rozkalns.coloring-pages.topics.v2", "revision": 1,
    "topics": [{"id": "baufahrzeuge", "label": "Baufahrzeuge", "icon": "🚜"}],
}


def bbox(locator):
    rect = locator.bounding_box()
    if rect is None:
        raise AssertionError(f"missing bounding box: {locator}")
    return rect


def check_case(browser, origin: str, width: int):
    page = browser.new_page(viewport={"width": width, "height": 900})
    try:
        page.route("**/catalog.json", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps([CURRENT, RELATED]),
        ))
        page.route("**/topics.json", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(TOPICS),
        ))
        page.goto(origin + "/detail.html?id=mobile-detail-1",
                  wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('[data-detail-root]')"
            "?.dataset.loadedId === 'mobile-detail-1'"
        )
        page.locator(".detail-topic-link").wait_for()
        page.locator('[data-basket-toggle="mobile-detail-1"]').wait_for()
        page.locator(".detail-related-card").first.wait_for()

        topic = page.locator(".detail-topic-link")
        if topic.count() != 1 or topic.inner_text() != "🚜 Baufahrzeuge":
            raise AssertionError(f"{width}px duplicate or incorrect topic navigation")
        if not page.locator("[data-detail-topic-nav]").is_visible():
            raise AssertionError(f"{width}px topic navigation is hidden")
        if page.locator("[data-detail-character]").is_visible():
            raise AssertionError(f"{width}px repeats character already in the title")
        if not page.locator("[data-action-print]").get_attribute("href"):
            raise AssertionError("print action lost its destination")
        if not page.locator("[data-action-png]").get_attribute("href"):
            raise AssertionError("PNG action lost its destination")

        scroll = page.evaluate(
            "() => ({doc: document.documentElement.scrollWidth,"
            " body: document.body.scrollWidth, viewport: innerWidth})"
        )
        if scroll["doc"] > width + 1 or scroll["body"] > width + 1:
            raise AssertionError(f"{width}px horizontal detail overflow: {scroll}")
        assert_inside_viewport(
            page, ".detail-grid, .detail-summary, .detail-media, "
            ".detail-controls, .detail-badges, .detail-topic-nav, "
            ".detail-actions, .basket-toggle-detail, "
            ".detail-related-grid, .detail-related-card", width,
        )
        order = [
            page.locator("[data-action-print]"),
            page.locator("[data-action-png]"),
            page.locator("[data-action-like]"),
            page.locator("[data-basket-toggle]"),
        ]
        if [node.evaluate("(e) => e.outerHTML.slice(0, 25)")
            for node in order].count(None):
            raise AssertionError("missing action")
        dom_order = page.evaluate(
            """() => {
              const selectors = ['[data-action-print]', '[data-action-png]',
                '[data-action-like]', '[data-basket-toggle]'];
              const nodes = selectors.map(s => document.querySelector(s));
              return nodes.every(Boolean) && nodes.every((node, i) =>
                i === 0 || Boolean(nodes[i-1].compareDocumentPosition(node) & 4));
            }"""
        )
        if not dom_order:
            raise AssertionError(f"{width}px action keyboard/DOM order incorrect")
        if width <= 720:
            if page.locator("[data-detail-category]").is_visible():
                raise AssertionError(f"{width}px redundant category when topic exists")
            summary, media, controls = [bbox(page.locator(s)) for s in
                                        (".detail-summary", ".detail-media",
                                         ".detail-controls")]
            if not (summary["y"] + summary["height"] <= media["y"] + 2
                    and media["y"] + media["height"] <= controls["y"] + 2):
                raise AssertionError(f"{width}px detail reading order overlap")
            age, difficulty, topic_rect = [
                bbox(page.locator(selector)) for selector in (
                    "[data-detail-age]", "[data-detail-difficulty]",
                    "[data-detail-topic-nav]"
                )
            ]
            if max(age["y"], difficulty["y"], topic_rect["y"]) - min(
                age["y"], difficulty["y"], topic_rect["y"]
            ) > 3:
                raise AssertionError(
                    f"{width}px age/difficulty/topic are not on one row: "
                    f"{age}, {difficulty}, {topic_rect}"
                )
            badge_widths = page.eval_on_selector(
                ".detail-summary .detail-badges",
                "(node) => ({scroll: node.scrollWidth, client: node.clientWidth})"
            )
            if badge_widths["scroll"] > badge_widths["client"] + 1:
                raise AssertionError(
                    f"{width}px Baufahrzeuge badges require scrolling: {badge_widths}"
                )
            p, png, like, basket = [bbox(node) for node in order]
            if not (p["y"] + p["height"] <= png["y"] + 2
                    and abs(png["y"] - like["y"]) <= 3
                    and max(png["y"] + png["height"],
                            like["y"] + like["height"]) <= basket["y"] + 2):
                raise AssertionError(
                    f"{width}px detail action layout incorrect: {p}, {png}, "
                    f"{like}, {basket}"
                )
            if min(node["height"] for node in (p, png, like, basket)) < 44:
                raise AssertionError(f"{width}px action below 44px touch target")
        if page.locator(".detail-related-card").count() != 1:
            raise AssertionError(f"{width}px related cards missing or duplicated")
        print(f"PASS detail {width}px: one topic, no overflow, actions ordered")
    finally:
        page.close()


def main():
    from playwright.sync_api import sync_playwright

    with server() as port, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            origin = f"http://127.0.0.1:{port}"
            for width in WIDTHS:
                check_case(browser, origin, width)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
