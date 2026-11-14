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
     "thumb": "/assets/favicon.svg",
     "print": f"/media/mobile-qa-{number}/print.png"}
    for number in range(1, 6)
]



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

    # Add via the real delegated click handler; the observer inserts this control.
    page.evaluate("""() => {
      const card = document.createElement('article');
      card.className = 'coloring-card';
      card.innerHTML = '<a href="detail.html?id=mobile-qa-1">Mobile QA 1</a>'
        + '<h3>Mobile QA 1</h3><div class="badges"></div>';
      document.querySelector('[data-gallery]').append(card);
    }""")
    page.locator('[data-basket-toggle="mobile-qa-1"]').click()
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
    # Reproduce the exact chip markup from app.js without requiring LIVE
    # taxonomy and catalogue feeds. The real filter-summary.js handles it.
    page.evaluate("""() => {
      const chip = document.createElement('button');
      chip.dataset.topicChip = 'obst';
      chip.className = 'topic-chip';
      chip.setAttribute('aria-pressed', 'true');
      const icon = document.createElement('span');
      icon.className = 'topic-chip-icon';
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = '🍎';
      chip.append(icon, document.createTextNode('Obst'));
      document.querySelector('[data-topic-list]').replaceChildren(chip);
      document.querySelector('[data-result-count]').textContent = '17 Malvorlagen';
    }""")
    page.wait_for_function(
        """() => {
          const output = document.querySelector('[data-active-filters]');
          return output && !output.hidden && output.textContent.includes('Thema: Obst');
        }"""
    )
    summary = page.locator("[data-active-filters]").inner_text()
    if "🍎" in summary or "Thema: Obst" not in summary:
        raise AssertionError(f"{width}px topic summary contains decorative icon: {summary!r}")
    if not page.locator("[data-reset-all-filters]").is_visible():
        raise AssertionError(f"{width}px active filter reset is not available")
    page.evaluate("""() => {
      document.querySelector('[data-topic-list]').replaceChildren();
      document.querySelector('[data-result-count]').textContent = '480 Malvorlagen';
    }""")
    page.wait_for_function(
        "() => document.querySelector('[data-active-filters]').hidden"
    )


def run_case(browser, origin: str, width: int):
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        page.route("**/catalog.json", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps(CATALOG_FIXTURE),
        ))
        page.goto(origin + "/index.html", wait_until="domcontentloaded")
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
