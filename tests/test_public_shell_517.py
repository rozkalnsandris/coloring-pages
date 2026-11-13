"""Regression coverage for the unified public shell (#517)."""
import hashlib
import html as html_module
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "index.html", "detail.html", "tiere.html", "fahrzeuge.html", "alphabet.html",
    "lernen.html", "figuren.html", "jahreszeiten.html", "essen-natur.html", "herbst.html",
    "kalender.html", "kita.html", "impressum.html", "datenschutz.html", "name.html",
]
NAV_LABELS = ["Malvorlagen", "Kategorien", "Kalender", "Kita & Vorschule"]


def labels(fragment):
    return [
        html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
        for value in re.findall(r"<a\b[^>]*>(.*?)</a>", fragment, flags=re.S)
    ]


class PublicShellTests(unittest.TestCase):
    def test_navigation_order_is_consistent(self):
        for path in PAGES:
            source = (ROOT / path).read_text(encoding="utf-8")
            desktop = re.search(r'<nav class="desktop-nav"[^>]*>(.*?)</nav>', source, flags=re.S)
            mobile = re.search(r'<nav id="mobile-nav"[^>]*>(.*?)</nav>', source, flags=re.S)
            self.assertIsNotNone(desktop, path)
            self.assertIsNotNone(mobile, path)
            self.assertEqual(labels(desktop.group(1)), NAV_LABELS, path)
            self.assertEqual(labels(mobile.group(1)), NAV_LABELS, path)
            self.assertNotIn("header-support", source, path)

    def test_one_information_footer_keeps_core_links(self):
        for path in PAGES:
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"<footer\b", source)), 1, path)
            footer = re.search(r"<footer\b.*?</footer>", source, flags=re.S).group(0)
            for label in ("Über uns", "Website weiterempfehlen", "Impressum", "Datenschutz", "Kontakt"):
                self.assertIn(label, footer, path)
            self.assertIn("data-social-footer", footer, path)

    def test_social_enhances_existing_footer(self):
        source = (ROOT / "js/social-footer.js").read_text(encoding="utf-8")
        self.assertIn('document.querySelector("[data-social-footer]")', source)
        self.assertNotIn('document.createElement("footer")', source)

    def test_legal_pages_have_mobile_menu_behavior(self):
        version = hashlib.sha256((ROOT / "js/public-nav.js").read_bytes()).hexdigest()[:16]
        for path in ("impressum.html", "datenschutz.html"):
            self.assertIn(
                f"js/public-nav.js?v={version}",
                (ROOT / path).read_text(encoding="utf-8"),
                path,
            )

    def test_social_assets_are_content_versioned(self):
        js_hash = hashlib.sha256((ROOT / "js/social-footer.js").read_bytes()).hexdigest()[:16]
        css_hash = hashlib.sha256((ROOT / "css/social-footer.css").read_bytes()).hexdigest()[:16]
        for path in PAGES:
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn(f"js/social-footer.js?v={js_hash}", source, path)
            self.assertIn(f"css/social-footer.css?v={css_hash}", source, path)


if __name__ == "__main__":
    unittest.main()
