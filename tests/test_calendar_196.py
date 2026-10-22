"""Source-only Ausmal-Kalender #196 checks."""
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class MonthParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.months = []
    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag == "section" and "data-calendar-month" in props:
            self.months.append(int(props["data-calendar-month"]))

class CalendarTests(unittest.TestCase):
    def test_twelve_months_and_no_invented_links(self):
        html = (ROOT / "kalender.html").read_text(encoding="utf-8")
        parser = MonthParser()
        parser.feed(html)
        self.assertEqual(parser.months, list(range(1, 13)))
        self.assertEqual(html.count('data-calendar-topic='), 20)
        self.assertIn("<noscript>", html)
        self.assertNotIn("detail.html?id=", html)

    def test_navigation_every_public_page(self):
        pages = ["index.html", "detail.html", "kita.html", "kalender.html",
                 "tiere.html", "fahrzeuge.html", "alphabet.html",
                 "lernen.html", "figuren.html", "jahreszeiten.html"]
        for page in pages:
            with self.subTest(page=page):
                html = (ROOT / page).read_text(encoding="utf-8")
                self.assertEqual(html.count(">Kalender</a>"), 2)

    def test_calendar_is_packaged_in_public_image(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        copy_lines = [line for line in dockerfile.splitlines() if line.startswith("COPY ") and "/usr/share/nginx/html/" in line]
        self.assertTrue(any("kalender.html" in line.split() for line in copy_lines))

    def test_timezone_calendar_and_read_only_catalog(self):
        js = (ROOT / "js/calendar.js").read_text(encoding="utf-8")
        for needle in ['timeZone: "Europe/Berlin"', "function easterUtc(year)",
                       "movableMonth(today.year, 48)", 'fetch("catalog.json", { cache: "no-store" })',
                       'fetch("/topics.json", { cache: "no-store" })',
                       "Array.isArray(entry.topics)", "ID_PATTERN.test", "setResult(row, null, true)"]:
            self.assertIn(needle, js)
        for forbidden in ["localStorage", "document.cookie", "window.print()", "sendBeacon"]:
            self.assertNotIn(forbidden, js)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_javascript_syntax(self):
        subprocess.run(["node", "--check", str(ROOT / "js/calendar.js")],
                       check=True, capture_output=True, text=True)

if __name__ == "__main__":
    unittest.main()
