"""Regression coverage for privacy-friendly, shared social follow footer."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (
    "index.html", "detail.html", "tiere.html", "fahrzeuge.html",
    "alphabet.html", "lernen.html", "figuren.html", "jahreszeiten.html",
    "essen-natur.html", "kalender.html", "kita.html",
)


class SocialFollowFooterTests(unittest.TestCase):
    def test_all_public_pages_use_same_assets(self):
        for name in PUBLIC:
            with self.subTest(page=name):
                page = (ROOT / name).read_text(encoding="utf-8")
                self.assertEqual(page.count('/css/social-footer.css?v=social-follow-20261022'), 1)
                self.assertEqual(page.count('/js/social-footer.js?v=social-follow-20261022'), 1)

    def test_print_and_dashboards_unchanged(self):
        for name in ("print.html", "stats.html", "traffic.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("social-footer.css", html)
            self.assertNotIn("social-footer.js", html)

    def test_no_guesswork_or_external_tracking(self):
        js = (ROOT / "js/social-footer.js").read_text(encoding="utf-8")
        self.assertIn('instagram: ""', js)
        self.assertIn('facebook: ""', js)
        self.assertIn("if (!links.length) return;", js)
        self.assertIn('url.protocol !== "https:"', js)
        self.assertIn("platform.hosts.includes(url.hostname)", js)
        self.assertIn('link.rel = "noopener noreferrer"', js)
        self.assertIn('link.target = "_blank"', js)
        self.assertIn('heading.textContent = "Folge uns"', js)
        self.assertNotIn("facebook.com/ausmalwiese", js)
        self.assertNotIn("instagram.com/ausmalwiese", js)

    def test_accessible_responsive_and_print_safe(self):
        css = (ROOT / "css/social-footer.css").read_text(encoding="utf-8")
        self.assertIn("min-height: 44px;", css)
        self.assertIn(".site-footer-link:focus-visible", css)
        self.assertIn("@media print", css)
        js = (ROOT / "js/social-footer.js").read_text(encoding="utf-8")
        self.assertIn('nav.setAttribute("aria-label"', js)
        self.assertIn('link.setAttribute("aria-label"', js)


if __name__ == "__main__":
    unittest.main()
