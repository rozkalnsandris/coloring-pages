"""Font stability: zero remote font requests and one immediate stack on every page."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "detail.html", "kita.html", "stats.html", "traffic.html", "print.html")


class FontDisplayContractTests(unittest.TestCase):
    def test_public_pages_use_single_local_system_font_policy(self):
        for path in PAGES:
            with self.subTest(path=path):
                html = (ROOT / path).read_text(encoding="utf-8")
                self.assertNotIn("fonts.googleapis.com", html)
                self.assertNotIn("fonts.gstatic.com", html)
                self.assertNotIn("display=optional", html)
                self.assertIn("css/stable-fonts.css?v=system-v1", html)
                self.assertLess(html.index("css/app.css?"), html.index("css/stable-fonts.css?"))

    def test_font_stack_is_immediate_and_stable(self):
        css = (ROOT / "css/stable-fonts.css").read_text(encoding="utf-8")
        self.assertIn("--font-display: system-ui", css)
        self.assertIn("--font-body: system-ui", css)
        self.assertNotIn("@font-face", css)
        self.assertNotIn("@import", css)

    def test_homepage_still_has_brand_art_and_ranking(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="hero-art"', homepage)
        self.assertIn('id="entdecken"', homepage)


if __name__ == "__main__":
    unittest.main()
