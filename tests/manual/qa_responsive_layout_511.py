#!/usr/bin/env python3
"""Chromium responsive boundary QA for UI/UX audit finding 15 (#511).

This is layout evidence only. It checks the public homepage category browser at
exact CSS viewport widths requested by the audit and verifies the 360/361 and
540/541 mobile-row boundaries without production network or LIVE mutation.
"""
from __future__ import annotations

import contextlib
import http.server
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (320, 360, 361, 390, 412, 540, 541, 768, 1440)


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


def run_case(browser, origin: str, width: int):
    page = browser.new_page(viewport={"width": width, "height": 1000})
    try:
        page.goto(origin + "/index.html", wait_until="domcontentloaded")
        page.wait_for_selector(".category-browser")

        # Let category-mobile-rows.js apply its matchMedia branch.
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
