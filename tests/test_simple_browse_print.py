"""Small source regression checks for the primary find → preview → print journey."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SimpleBrowsePrintTests(unittest.TestCase):
    def test_home_show_categories_and_new_before_trending(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        items = ['id="hero"', 'id="kategorien"', 'id="neu"',
                 'id="entdecken"', 'id="unterstuetzen"']
        offsets = [page.index(item) for item in items]
        self.assertEqual(offsets, sorted(offsets))
        self.assertEqual(page.count('id="entdecken"'), 1)
        self.assertIn('data-ranking-tab="trending"', page)
        self.assertIn('data-gallery', page)
        self.assertIn('data-search-form', page)

    def test_print_remains_primary_and_png_keeps_full_quality(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        js = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        self.assertLess(html.index('data-action-print '),
                        html.index('data-action-png download'))
        self.assertLess(html.index('data-action-png download'),
                        html.index('data-action-like '))
        self.assertIn('Einfach auf A4 drucken', html)
        self.assertIn('hochauflösende PNG-Druckdatei', html)
        self.assertIn('print.html?id=', js)
        self.assertIn('page.print', js)
        self.assertIn('startHtmlPrint(printLink.href)', js)
        self.assertIn('${entry.title} | Ausmalwiese', js)

    def test_like_is_accessible_and_svg_state_driven(self):
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        js = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn('<svg class="like-heart"', html)
        self.assertIn('aria-pressed="false"', html)
        self.assertIn('likeButton.setAttribute("aria-pressed"', js)
        self.assertNotIn('heart.textContent', js)
        self.assertIn('.action-like.is-liked .like-heart { fill:currentColor; }', css)

    def test_screen_print_help_does_not_enter_paper_layout(self):
        html = (ROOT / "print.html").read_text(encoding="utf-8")
        js = (ROOT / "js/print.js").read_text(encoding="utf-8")
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn('class="print-help"', html)
        self.assertIn('data-print-back', html)
        self.assertIn('printBack.href = `detail.html?id=', js)
        self.assertIn('.print-help,', css[css.index('@media print {'):])
        self.assertIn('PRINT_QR_ROUTE_VERIFIED = true', js)

    def test_changed_static_assets_have_exact_hash_versions(self):
        css = (ROOT / "css/app.css").read_bytes()
        detail_js = (ROOT / "js/detail.js").read_bytes()
        print_js = (ROOT / "js/print.js").read_bytes()
        versions = (
            ("css/app.css", hashlib.sha256(css).hexdigest()[:16],
             ("index.html", "detail.html", "print.html",
              "kita.html", "stats.html", "traffic.html")),
            ("js/detail.js", hashlib.sha256(detail_js).hexdigest()[:16], ("detail.html",)),
            ("js/print.js", hashlib.sha256(print_js).hexdigest()[:16], ("print.html",)),
        )
        for asset, version, pages in versions:
            for page in pages:
                with self.subTest(asset=asset, page=page):
                    html = (ROOT / page).read_text(encoding="utf-8")
                    self.assertIn(f'{asset}?v={version}', html)


if __name__ == "__main__":
    unittest.main()
