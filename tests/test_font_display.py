"""Ensure the shared webfont policy cannot regress to late font swaps."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_PAGES = ("index.html", "detail.html", "kita.html", "stats.html", "traffic.html")


class FontDisplayContractTests(unittest.TestCase):
    def test_locally_bundled_font_display_remains_optional(self):
        css = (ROOT / "css/fonts.css").read_text(encoding="utf-8")
        self.assertEqual(css.count("font-display: optional;"), 2)
        self.assertNotIn("font-display: swap;", css)
        for path in FONT_PAGES:
            with self.subTest(path=path):
                html = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("css/fonts.css?v=privacy-ofl-v1", html)
                self.assertNotIn("fonts.googleapis.com", html)
                self.assertNotIn("fonts.gstatic.com", html)

    def test_hero_and_typography_remain_intact(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        styles = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn('class="hero-art"', homepage)
        self.assertIn('id="entdecken"', homepage)
        self.assertIn('--font-display: "Baloo 2"', styles)
        self.assertIn('--font-body: "Nunito"', styles)


if __name__ == "__main__":
    unittest.main()
