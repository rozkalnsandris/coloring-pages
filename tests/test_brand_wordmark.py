"""Keep the Ausmalwiese wordmark consistent across HTML pages and small screens."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "detail.html", "kita.html", "stats.html", "traffic.html")
LETTERS = '<span class="brand-wiese"><b>w</b><b>i</b><b>e</b><b>s</b><b>e</b></span>'


class BrandWordmarkTests(unittest.TestCase):
    def test_shared_header_wordmark(self):
        for page in PAGES:
            with self.subTest(page=page):
                html = (ROOT / page).read_text(encoding="utf-8")
                brand = re.search(r'<a class="brand"[^>]*>(.*?)</a>', html, re.S)
                self.assertIsNotNone(brand)
                markup = brand.group(1)
                self.assertIn('class="brand-paw"', markup)
                self.assertIn('<span>Ausmal</span>', markup)
                self.assertIn(LETTERS, markup)
                self.assertNotIn("Coloring", markup)
                self.assertIn('aria-label="Ausmalwiese', brand.group(0))
                self.assertEqual(html.count('class="brand-wiese"'), 1)

    def test_brand_styles_and_responsive_admin_header(self):
        styles = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn('.brand-word { display: inline-flex; align-items: baseline; }', styles)
        self.assertIn('.brand-wiese b:nth-child(5)', styles)
        self.assertNotIn('.brand-pages', styles)
        self.assertNotIn('.brand-bilder', styles)
        self.assertIn('.stats-page .brand { font-size: clamp(18px, 4.7vw, 24px); }', styles)


if __name__ == "__main__":
    unittest.main()
