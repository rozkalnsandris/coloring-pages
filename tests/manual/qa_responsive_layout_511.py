#!/usr/bin/env python3
"""Chromium responsive boundary QA for UI/UX audit finding 15 (#511).

This is browser-layout evidence only. It checks the homepage category browser,
basket, topic-filter summary and hero search actions at exact CSS viewports
without production network or LIVE mutation.
"""
from __future__ import annotations

import contextlib
import http.server
import json
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (320, 360, 361, 390, 412, 540, 541, 768, 1440)
CATALOG_FIXTURE = [
    {"id": f"mobile-qa-{number}", "title": f"Mobile QA {number}",
     "category": "tiere", "age": "3-6", "difficulty": "easy",
     "topics": ["deutschland"] if number <= 2 else (["obst"] if number <= 4 else []),
     "thumb": "/assets/favicon.svg",
     "print": f"/media/mobile-qa-{number}/print.png"}
    for number in range(1, 6)
]
CATEGORIES_FIXTURE = {
    "schema": "rozkalns.coloring-pages.categories.v2", "revision": 1,
    "categories": [
        {"id": name, "label": label}
        for name, label in (
            ("tiere", "Tiere"), ("fahrzeuge", "Fahrzeuge"),
            ("alphabet", "Alphabet"), ("lernen", "Lernen"),
            ("figuren", "Figuren"), ("jahreszeiten", "Jahreszeiten & Feste"),
        )
    ],
}
TOPICS_FIXTURE = {
    "schema": "rozkalns.coloring-pages.topics.v2", "revision": 1,
    "topics": [
        {"id": "deutschland", "label": "Deutschland", "icon": "🇩🇪",
         "kind": "evergreen", "legacy_terms": []},
        {"id": "obst", "label": "Obst", "icon": "🍎",
         "kind": "evergreen", "legacy_terms": []},
    ],
}



class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_args):
        pass


@contextlib.contextmanager
def server():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()


def assert_inside_viewport(page, selector: str, width: int):
    values = page.eval_on_selector_all(
        selector,
        """nodes => nodes.filter(node => {
          const style = getComputedStyle(node);
          return style.display !== 'none' && style.visibility !== 'hidden';
        }).map(node => {
          const rect = node.getBoundingClientRect();
          return {left: rect.left, right: rect.right, width: rect.width};
        })""",
    )
    for index, rect in enumerate(values):
        if rect["left"] < -1 or rect["right"] > width + 1:
            raise AssertionError(
                f"{width}px {selector}[{index}] exceeds viewport: {rect}"
            )



def assert_reflow_after_basket(page, width: int, state: str):
    metrics = page.evaluate(
        """() => ({
          doc: document.documentElement.scrollWidth,
          body: document.body.scrollWidth,
          viewport: window.innerWidth,
        })"""
    )
    if metrics["doc"] > width + 1 or metrics["body"] > width + 1:
        raise AssertionError(f"{width}px basket={state} horizontal overflow: {metrics}")
    assert_inside_viewport(
        page, ".site-header, .header-inner, .brand, .header-actions, "
        ".menu-button, .basket-summary, .legal-footer-inner, "
        ".legal-footer-inner > a, .site-footer-social", width,
    )
    for selector in ("#neu .section-heading", ".discovery-picks .section-heading"):
        heading = page.locator(f"{selector} h2").first
        action = page.locator(f"{selector} .outline-link").first
        if not heading.count() or not action.count():
            continue
        a, b = heading.bounding_box(), action.bounding_box()
        if a and b and (
            min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"]) > 1
            and min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"]) > 1
        ):
            raise AssertionError(f"{width}px basket={state} heading/action overlap: {selector}")
    for link in page.locator(".legal-footer-inner > a").all():
        if (box := link.bounding_box()) and width <= 540 and box["height"] < 44:
            raise AssertionError(f"{width}px basket={state} footer link below 44px: {box}")


def exercise_real_basket_reflow(page, width: int):
    summary = page.locator("[data-basket-summary]")
    page.wait_for_function(
        "() => { const s = document.querySelector('[data-basket-summary]'); "
        "return Boolean(s && !s.disabled); }", timeout=15000,
    )
    if "0/5" not in summary.inner_text():
        raise AssertionError(f"{width}px basket did not initialize at 0/5")
    assert_reflow_after_basket(page, width, "0/5")

    # Use the real hydrated catalogue card. Injecting a duplicate ID would
    # make the selector ambiguous and would not test normal visitor behavior.
    page.locator('[data-gallery] [data-basket-toggle="mobile-qa-1"]').click()
    if "1/5" not in summary.inner_text():
        raise AssertionError(f"{width}px real add did not update basket to 1/5")
    assert_reflow_after_basket(page, width, "1/5")

    # The public Kita package event uses the same basket reconciler for 5 sheets.
    page.evaluate(
        """ids => document.dispatchEvent(new CustomEvent(
          'ausmalwiese:print-basket-replace',
          {detail: {ids, expectedSheets: ids.length, open: false}}
        ))""",
        [item["id"] for item in CATALOG_FIXTURE],
    )
    if "5/5" not in summary.inner_text():
        raise AssertionError(f"{width}px curated add did not update basket to 5/5")
    assert_reflow_after_basket(page, width, "5/5")
    if width <= 540:
        label = summary.locator(".basket-summary-short")
        if label.is_visible():
            raise AssertionError(f"{width}px basket short label must be visually hidden")
        if "Meine Drucksammlung" not in (summary.get_attribute("aria-label") or ""):
            raise AssertionError(f"{width}px basket lost its accessible label")



def assert_search_and_surprise_group(page, width: int):
    # #567: selected-topic views replace the generic dog/search hero with
    # a compact semantic Topic hero; search stays reachable via header.
    if page.locator("[data-focused-topic-hero]").is_visible():
        if page.locator("#hero").is_visible():
            raise AssertionError(f"{width}px generic hero duplicated with Topic hero")
        if not page.locator("[data-focused-topic-title]").is_visible():
            raise AssertionError(f"{width}px Topic H1 is missing")
        if page.locator(".header-search").get_attribute("href") != "/#hero":
            raise AssertionError(f"{width}px search link does not return to homepage")
        return
    if width > 720:
        return
    search = page.locator(".hero-search-tools .search")
    action = page.locator("[data-surprise-button]")
    search_box, action_box = search.bounding_box(), action.bounding_box()
    if not search_box or not action_box:
        raise AssertionError(f"{width}px hero search or surprise button not visible")
    gap = action_box["y"] - (search_box["y"] + search_box["height"])
    if abs(search_box["x"] - action_box["x"]) > 2 or not 0 <= gap <= 16:
        raise AssertionError(
            f"{width}px surprise action separated from search: "
            f"search={search_box}, surprise={action_box}, gap={gap}"
        )
    if action_box["height"] < 44 or action_box["x"] + action_box["width"] > width + 1:
        raise AssertionError(f"{width}px surprise action touch target/overflow: {action_box}")
    style = page.eval_on_selector(
        "[data-surprise-button]",
        "(button) => ({border: getComputedStyle(button).borderTopWidth, "
        "background: getComputedStyle(button).backgroundColor})",
    )
    if style["border"] == "0px" or style["background"] == "rgba(0, 0, 0, 0)":
        raise AssertionError(f"{width}px surprise action lost button styling: {style}")
    assert_inside_viewport(page, ".hero-search-tools, .search, .surprise-action", width)


def assert_topic_filter_summary(page, width: int):
    page.wait_for_function(
        """() => {
          const filter = document.querySelector('[data-filter-topic]');
          const count = document.querySelector('[data-result-count]');
          return filter && !filter.disabled && filter.options.length === 3 &&
            filter.value === 'deutschland' &&
            count?.textContent.trim() === '2 Malvorlagen';
        }"""
    )
    if page.locator("[data-topic-explorer], [data-topic-chip]").count():
        raise AssertionError(f"{width}px duplicate topic UI remains")
    if page.locator("[data-filter-topic]").count() != 1:
        raise AssertionError(f"{width}px duplicate topic selectors")
    if page.locator("[data-reset-all-filters]").count() != 1:
        raise AssertionError(f"{width}px duplicate reset")
    if page.locator("#gallery-title").inner_text() != "Deutschland Ausmalbilder":
        raise AssertionError(f"{width}px selected Topic heading incorrect")
    if not page.locator("[data-filter-topic]").is_visible():
        raise AssertionError(f"{width}px Topic selector must remain visible")
    if page.locator("[data-show-categories]").get_attribute("aria-expanded") != "true":
        raise AssertionError(f"{width}px Category reveal state incorrect")
    if page.locator("[data-clear-active-topic]").count():
        raise AssertionError(f"{width}px duplicate Topic chip must not exist")
    if not page.locator("[data-gallery-filter-panel]").is_visible():
        raise AssertionError(f"{width}px filter panel not visible")
    if page.locator("[data-active-filters]").is_visible():
        raise AssertionError(f"{width}px topic repeated in summary")
    if not page.locator("[data-reset-all-filters]").is_visible():
        raise AssertionError(f"{width}px reset missing for active topic")
    assert_inside_viewport(
        page, "[data-gallery-filter-panel], .gallery-filter-fields, "
        ".gallery-filter-fields select, .gallery-filter-footer, "
        "[data-reset-all-filters]", width,
    )
    controls = [page.locator(selector) for selector in (
        "[data-filter-topic]", "[data-filter-age]", "[data-filter-difficulty]"
    )]
    bounds = [control.bounding_box() for control in controls]
    if any(not box or box["height"] < 44 for box in bounds):
        raise AssertionError(f"{width}px inaccessible filter targets: {bounds}")
    if width <= 720:
        for prior, following in zip(bounds, bounds[1:]):
            if following["y"] < prior["y"] + prior["height"] - 1:
                raise AssertionError(f"{width}px overlapping filter controls: {bounds}")

    page.locator("[data-filter-topic]").select_option("")
    page.wait_for_function(
        "() => !new URL(location.href).searchParams.has('topic') && "
        "document.querySelector('[data-filter-topic]').value === ''"
    )
    if not page.locator("[data-filter-topic]").is_visible():
        raise AssertionError(f"{width}px Topic selector not available when cleared")
    page.locator("[data-filter-topic]").select_option("obst")
    page.wait_for_function(
        "() => new URL(location.href).searchParams.get('topic') === 'obst'"
        " && document.querySelector('[data-result-count]')"
        "?.textContent.trim() === '2 Malvorlagen'"
    )
    if page.locator("[data-active-filters]").is_visible():
        raise AssertionError(f"{width}px duplicated topic after change")
    if page.locator("#gallery-title").inner_text() != "Obst Ausmalbilder":
        raise AssertionError(f"{width}px changed Topic heading incorrect")
    if not page.locator("[data-filter-topic]").is_visible():
        raise AssertionError(f"{width}px Topic selector hidden after Topic change")
    page.locator("[data-filter-age]").select_option("4-8")
    page.wait_for_function(
        "() => document.querySelector('[data-result-count]')"
        "?.textContent.trim() === '0 Malvorlagen'"
    )
    page.locator("[data-reset-all-filters]").click()
    page.wait_for_function(
        """() => {
          const url = new URL(location.href);
          return !url.searchParams.has('topic') &&
            !url.searchParams.has('age') &&
            document.querySelector('[data-filter-topic]').value === '' &&
            document.querySelector('[data-filter-age]').value === '' &&
            document.querySelector('[data-result-count]').textContent.trim() === '5 Malvorlagen';
        }"""
    )
    if "campaign=dortmund-01" not in page.url:
        raise AssertionError(f"{width}px unrelated URL parameter lost")
    if page.locator("[data-reset-all-filters]").is_visible():
        raise AssertionError(f"{width}px redundant reset when unfiltered")
    if page.locator("[data-active-filters]").is_visible():
        raise AssertionError(f"{width}px stale filter summary after reset")



def assert_herbst_illustration(page, origin: str, width: int):
    # Real local HTML + approved WebP; no LIVE/protected media required.
    page.goto(origin + "/herbst.html", wait_until="domcontentloaded")
    page.wait_for_function(
        "() => {const img = document.querySelector('[data-topic-landing-art] img');"
        "return img && img.complete && img.naturalWidth === 1755 && img.naturalHeight === 896;}"
    )
    hero = page.locator(".topic-landing-hero--with-art")
    image = page.locator("[data-topic-landing-art] img")
    if not hero.is_visible() or not image.is_visible():
        raise AssertionError(f"{width}px approved Herbst illustration hidden")
    if page.locator(".page-hero-breadcrumbs ol li").count() != 3:
        raise AssertionError(f"{width}px Herbst breadcrumb ancestry is not semantic")
    if page.locator(".page-hero-breadcrumbs [aria-current='page']").inner_text() != "Herbst":
        raise AssertionError(f"{width}px Herbst breadcrumb current page incorrect")
    if image.get_attribute("alt") != "Ausmalwiese-Hund mit Kürbissen und buntem Herbstlaub":
        raise AssertionError(f"{width}px Herbst illustration alt missing")
    if image.get_attribute("src") != "/assets/herbst-topic-hero.webp":
        raise AssertionError(f"{width}px unexpected Herbst illustration source")
    metrics = page.evaluate(
        "() => ({width: innerWidth, html: document.documentElement.scrollWidth,"
        "body: document.body.scrollWidth})"
    )
    if metrics["width"] != width or metrics["html"] > width + 1 or metrics["body"] > width + 1:
        raise AssertionError(f"{width}px illustrated Herbst overflow: {metrics}")
    assert_inside_viewport(page, ".topic-landing-hero, .topic-landing-art, .topic-landing-art img", width)
    heading = page.locator(".topic-landing-hero h1").bounding_box()
    art = image.bounding_box()
    if not heading or not art:
        raise AssertionError(f"{width}px hero artwork/heading bounds missing")
    if width <= 720 and art["y"] < heading["y"] + heading["height"] - 1:
        raise AssertionError(f"{width}px artwork overlaps topic heading")


def run_case(browser, origin: str, width: int):
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        page.route("**/catalog.json", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(CATALOG_FIXTURE),
        ))
        page.route("**/categories.json", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(CATEGORIES_FIXTURE),
        ))
        page.route("**/topics.json", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(TOPICS_FIXTURE),
        ))
        page.goto(
            origin + "/index.html?topic=deutschland&campaign=dortmund-01#neu",
            wait_until="domcontentloaded",
        )
        page.wait_for_function(
            "() => document.querySelector('#gallery-title')?.textContent.trim() === 'Deutschland Ausmalbilder'"
        )
        if page.locator(".category-browser").is_visible():
            raise AssertionError(f"{width}px selected Topic must initially collapse Category browser")
        if page.locator("#hero").is_visible():
            raise AssertionError(f"{width}px generic home hero visible for selected Topic")
        hero = page.locator("[data-focused-topic-hero]")
        if not hero.is_visible():
            raise AssertionError(f"{width}px selected Topic hero is missing")
        if not page.locator("main > [data-focused-topic-hero]").count():
            raise AssertionError(f"{width}px Topic hero must be a top-level main child")
        if page.locator("[data-focused-topic-hero] .page-hero-breadcrumbs ol li").count() != 2:
            raise AssertionError(f"{width}px focused Topic breadcrumb incorrect")
        if page.locator("[data-focused-topic-title]").inner_text() != "Deutschland Ausmalbilder":
            raise AssertionError(f"{width}px Topic hero H1 incorrect")
        if page.locator(".page-hero--home .hero-search-tools").is_visible():
            raise AssertionError(f"{width}px homepage search duplicated in Topic state")
        # The URL deliberately ends in #neu, so the browser scrolls the hero
        # above the sticky header. Test DOM placement, not viewport Y.
        if not hero.evaluate(
            "(node) => node.parentElement?.id === 'main' "
            "&& node.previousElementSibling?.id === 'hero'"
        ):
            raise AssertionError(f"{width}px Topic hero not adjacent to home hero in main")
        if not page.locator("[data-filter-topic]").is_visible():
            raise AssertionError(f"{width}px selected Topic has no navigation selector")
        page.locator("[data-show-categories]").click()
        page.wait_for_selector(".category-browser")
        page.wait_for_timeout(100)

        metrics = page.evaluate(
            """() => ({
              innerWidth: window.innerWidth,
              doc: document.documentElement.scrollWidth,
              body: document.body.scrollWidth,
              mobileRows: document.querySelector('.category-browser')
                ?.hasAttribute('data-category-mobile-rows') ?? false,
            })"""
        )
        if metrics["innerWidth"] != width:
            raise AssertionError(f"viewport drift: requested {width}, got {metrics}")
        if metrics["doc"] > width + 1 or metrics["body"] > width + 1:
            offenders = page.evaluate(
                """() => [...document.querySelectorAll('body *')].map(node => {
                  const style = getComputedStyle(node);
                  const rect = node.getBoundingClientRect();
                  return {
                    tag: node.tagName.toLowerCase(),
                    cls: typeof node.className === 'string' ? node.className : '',
                    id: node.id || '',
                    left: Math.round(rect.left),
                    right: Math.round(rect.right),
                    width: Math.round(rect.width),
                    display: style.display,
                    visibility: style.visibility,
                    text: (node.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 80),
                  };
                }).filter(item =>
                  item.display !== 'none' && item.visibility !== 'hidden' &&
                  (item.left < -1 || item.right > window.innerWidth + 1)
                ).slice(0, 20)"""
            )
            raise AssertionError(
                f"{width}px horizontal overflow: {metrics}; offenders={offenders}"
            )

        expected_mobile_rows = 361 <= width <= 540
        if metrics["mobileRows"] != expected_mobile_rows:
            raise AssertionError(
                f"{width}px mobile-row boundary mismatch: {metrics['mobileRows']}"
            )

        for selector in (
            ".site-header",
            ".header-inner",
            ".hero-grid",
            ".category-browser",
            ".category-group",
            ".legal-footer-inner",
        ):
            assert_inside_viewport(page, selector, width)

        first_summary = page.locator(".category-browser details > summary").first
        if first_summary.count():
            first_summary.click()
            page.wait_for_timeout(50)
            post = page.evaluate(
                """() => ({
                  doc: document.documentElement.scrollWidth,
                  body: document.body.scrollWidth,
                })"""
            )
            if post["doc"] > width + 1 or post["body"] > width + 1:
                raise AssertionError(
                    f"{width}px overflow after category disclosure: {post}"
                )
            assert_inside_viewport(
                page,
                ".category-browser, .category-group, "
                ".category-row-topics:not([hidden]), .category-subtopics",
                width,
            )

        exercise_real_basket_reflow(page, width)
        assert_search_and_surprise_group(page, width)
        assert_topic_filter_summary(page, width)
        assert_herbst_illustration(page, origin, width)
        print(
            f"PASS responsive {width}px: mobileRows={expected_mobile_rows}, "
            "no horizontal overflow"
        )
    finally:
        page.close()


def main():
    from playwright.sync_api import sync_playwright

    with server() as port, sync_playwright() as driver:
        browser = driver.chromium.launch()
        try:
            origin = f"http://127.0.0.1:{port}"
            for width in WIDTHS:
                run_case(browser, origin, width)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
