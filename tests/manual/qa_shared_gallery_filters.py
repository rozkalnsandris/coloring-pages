#!/usr/bin/env python3
"""Source-only Chromium regression: one accessible filter panel on nine routes."""
import contextlib
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (320, 390, 768, 1440)
ROUTES = ("index.html", "tiere.html", "fahrzeuge.html", "alphabet.html",
          "lernen.html", "figuren.html", "jahreszeiten.html",
          "essen-natur.html", "herbst.html")
CATALOG = [
    {"id": "3000001", "title": "Alphabet Obst", "category": "alphabet",
     "thumb": "/assets/favicon.svg", "age": "3-6", "difficulty": "easy",
     "topics": ["obst"]},
    {"id": "3000002", "title": "Alphabet Deutschland", "category": "alphabet",
     "thumb": "/assets/favicon.svg", "age": "3-6", "difficulty": "easy",
     "topics": ["deutschland"]},
    {"id": "3000003", "title": "Herbst Blatt", "category": "jahreszeiten",
     "thumb": "/assets/favicon.svg", "age": "3-6", "difficulty": "easy",
     "topics": ["herbst"]},
    {"id": "3000004", "title": "Hund", "category": "tiere",
     "thumb": "/assets/favicon.svg", "age": "3-6", "difficulty": "easy",
     "topics": ["obst"]},
]
TOPICS = {"schema": "rozkalns.coloring-pages.topics.v2", "revision": 1,
          "topics": [
              {"id": "obst", "label": "Obst", "icon": "🍎",
               "kind": "evergreen", "legacy_terms": []},
              {"id": "deutschland", "label": "Deutschland", "icon": "🇩🇪",
               "kind": "evergreen", "legacy_terms": []},
              {"id": "herbst", "label": "Herbst", "icon": "🍂",
               "kind": "seasonal", "active_from": "09-01", "active_to": "11-30",
               "legacy_terms": []},
          ]}
CATEGORIES = {"schema": "rozkalns.coloring-pages.categories.v2", "revision": 1,
              "categories": [
                  {"id": key, "label": label}
                  for key, label in (("tiere", "Tiere"), ("fahrzeuge", "Fahrzeuge"),
                                     ("alphabet", "Alphabet"), ("lernen", "Lernen"),
                                     ("figuren", "Figuren"),
                                     ("jahreszeiten", "Jahreszeiten & Feste"))
              ]}
EXPECTED = {"index.html": 4, "tiere.html": 1, "fahrzeuge.html": 0,
            "alphabet.html": 2, "lernen.html": 0, "figuren.html": 0,
            "jahreszeiten.html": 1, "essen-natur.html": 2, "herbst.html": 1}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_args):
        pass


@contextlib.contextmanager
def serve():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(httpd.server_address[1])
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()


def check(browser, origin, path, width):
    page = browser.new_page(viewport={"width": width, "height": 850})
    try:
        for name, payload in (("catalog.json", CATALOG),
                              ("topics.json", TOPICS), ("categories.json", CATEGORIES)):
            page.route("**/" + name, lambda route, value=payload: route.fulfill(
                status=200, content_type="application/json", body=json.dumps(value)))
        page.goto(origin + "/" + path + "?campaign=dortmund-01",
                  wait_until="domcontentloaded")
        expected = EXPECTED[path]
        count_text = str(expected) + (" Malvorlage" if expected == 1 else " Malvorlagen")
        page.wait_for_function(
            """text => document.querySelector('.gallery-filter-panel [data-result-count]')
                ?.textContent.trim() === text""",
            arg=count_text, timeout=15000)
        state = page.evaluate("""() => {
          const panels = [...document.querySelectorAll('.gallery-filter-panel')];
          const p = panels[0];
          const fields = p ? [...p.querySelectorAll('select')] : [];
          return {
            panels: panels.length, selects: fields.length,
            labels: fields.map(f => !!f.labels?.length),
            count: p?.querySelectorAll('[data-result-count]').length,
            reset: p?.querySelectorAll('[data-reset-all-filters]').length,
            oldTopics: document.querySelectorAll('.category-topic-strip').length,
            oldMetadata: document.querySelectorAll('[data-category-metadata-filters]').length,
            oldCounts: document.querySelectorAll('.section-heading .catalog-total').length,
            viewport: innerWidth, docWidth: document.documentElement.scrollWidth,
            bodyWidth: document.body.scrollWidth,
          };
        }""")
        assert (state["panels"], state["selects"], state["labels"],
                state["count"], state["reset"], state["oldTopics"],
                state["oldMetadata"], state["oldCounts"]) == (
                    1, 3, [True, True, True], 1, 1, 0, 0, 0), (path, width, state)
        assert state["viewport"] == width, (path, width, state)
        assert max(state["docWidth"], state["bodyWidth"]) <= width + 1, (path, width, state)
        for select in page.locator(".gallery-filter-panel select").all():
            box = select.bounding_box()
            assert box and box["height"] >= 44 and box["x"] >= -1 and (
                box["x"] + box["width"] <= width + 1), (path, width, box)
        if path == "alphabet.html":
            page.locator("[data-filter-topic]").select_option("obst")
            page.wait_for_function(
                "() => document.querySelector('[data-result-count]').textContent === '1 Malvorlage'")
            page.locator("[data-filter-age]").select_option("4-8")
            page.wait_for_function(
                "() => document.querySelector('[data-result-count]').textContent === '0 Malvorlagen'")
            page.locator("[data-reset-all-filters]").click()
            page.wait_for_function(
                "() => document.querySelector('[data-result-count]').textContent === '2 Malvorlagen'")
            assert "campaign=dortmund-01" in page.url, page.url
        if path == "herbst.html":
            assert page.locator("[data-filter-topic]").is_disabled()
            page.locator("[data-filter-age]").select_option("4-8")
            page.wait_for_function(
                "() => document.querySelector('[data-result-count]').textContent === '0 Malvorlagen'")
            page.locator("[data-reset-all-filters]").click()
            page.wait_for_function(
                "() => document.querySelector('[data-result-count]').textContent === '1 Malvorlage'")
        print("PASS shared filters", path, str(width) + "px")
    finally:
        page.close()


def main():
    with serve() as origin, sync_playwright() as driver:
        browser = driver.chromium.launch()
        try:
            for width in WIDTHS:
                for path in ROUTES:
                    check(browser, origin, path, width)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
