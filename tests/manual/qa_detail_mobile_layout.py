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
    "id": "mobile-detail-1", "title": "Junge und Mädchen malen zusammen",
    "category": "figuren", "topics": ["blumen"],
    "character": "Junge und Mädchen", "age": "3-6",
    "difficulty": "easy", "thumb": "/assets/favicon.svg",
    "preview": "/assets/favicon.svg", "print": "/assets/favicon.svg",
}
RELATED = {
    "id": "mobile-detail-2", "title": "Blumenwiese",
    "category": "figuren", "topics": ["blumen"],
    "age": "3-6", "difficulty": "easy",
    "thumb": "/assets/favicon.svg", "preview": "/assets/favicon.svg",
    "print": "/assets/favicon.svg",
}
TOPICS = {
    "schema": "rozkalns.coloring-pages.topics.v2", "revision": 1,
    "topics": [{"id": "blumen", "label": "Blumen", "icon": "🌸"}],
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
        if topic.count() != 1 or topic.inner_text() != "🌸 Blumen":
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
            page.locator("[data-basket-toggle]"),
            page.locator("[data-action-like]"),
        ]
        if [node.evaluate("(e) => e.outerHTML.slice(0, 25)")
            for node in order].count(None):
            raise AssertionError("missing action")
        dom_order = page.evaluate(
            """() => {
              const selectors = ['[data-action-print]', '[data-action-png]',
                '[data-basket-toggle]', '[data-action-like]'];
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
            p, png, basket, like = [bbox(node) for node in order]
            if not (p["y"] + p["height"] <= png["y"] + 2
                    and abs(png["y"] - basket["y"]) <= 3
                    and max(png["y"] + png["height"],
                            basket["y"] + basket["height"]) <= like["y"] + 2):
                raise AssertionError(
                    f"{width}px detail action layout incorrect: {p}, {png}, "
                    f"{basket}, {like}"
                )
            if min(node["height"] for node in (p, png, basket, like)) < 44:
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
