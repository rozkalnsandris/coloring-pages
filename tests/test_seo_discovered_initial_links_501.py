"""SEO regression for initial crawlable detail links added from GSC #501."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGES = {
    "figuren.html": (
        "figuren",
        ("0678119", "0901643", "2314419", "2775405", "2889626", "3798896"),
    ),
    "jahreszeiten.html": (
        "jahreszeiten",
        ("1066839", "1182412", "2326012", "3912267"),
    ),
}


class DiscoveredInitialLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.category_js = (ROOT / "js/category.js").read_text(encoding="utf-8")

    def initial_gallery(self, page):
        gallery = re.search(
            r'<div class="gallery" data-category-gallery aria-live="polite">(.*?)</div>',
            page,
            flags=re.S,
        )
        self.assertIsNotNone(gallery, "initial gallery must exist in source HTML")
        return gallery.group(1)

    def test_exact_search_console_examples_are_native_initial_links(self):
        for filename, (_, expected_ids) in PAGES.items():
            with self.subTest(filename=filename):
                page = (ROOT / filename).read_text(encoding="utf-8")
                gallery = self.initial_gallery(page)
                cards = re.findall(
                    r'<article class="coloring-card">(.*?)</article>', gallery, re.S
                )
                self.assertEqual(len(cards), len(expected_ids))
                ids = []
                for card in cards:
                    links = re.findall(
                        r'<a\b[^>]*href="/detail[.]html[?]id=([0-9]{7})"[^>]*>',
                        card,
                    )
                    self.assertEqual(len(links), 2)
                    self.assertEqual(links[0], links[1])
                    image = re.search(
                        r'<img\b[^>]*src="/media/([0-9]{7})/thumb[.]webp"[^>]*alt="([^"]+)"',
                        card,
                    )
                    self.assertIsNotNone(image)
                    self.assertEqual(image.group(1), links[0])
                    self.assertGreaterEqual(len(image.group(2)), 8)
                    self.assertLessEqual(len(image.group(2)), 120)
                    self.assertIn("<h3>", card)
                    ids.append(links[0])
                self.assertEqual(tuple(ids), expected_ids)
                self.assertEqual(len(set(ids)), len(ids))
                self.assertNotIn("<noscript", gallery)
                self.assertNotIn("<script", gallery)

    def test_category_identity_canonical_and_indexability_are_preserved(self):
        for filename, (category, expected_ids) in PAGES.items():
            with self.subTest(filename=filename):
                page = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(f'data-category-page="{category}"', page)
                self.assertEqual(
                    page.count(
                        f'<link rel="canonical" href="https://ausmalwiese.de/{category}">'
                    ),
                    1,
                )
                self.assertNotIn('content="noindex"', page)
                self.assertIn(
                    f"data-category-total>{len(expected_ids)}</span>",
                    page,
                )

    def test_runtime_catalogue_still_replaces_seed_gallery(self):
        self.assertIn('fetch("/catalog.json"', self.category_js)
        self.assertIn("gallery.replaceChildren(fragment)", self.category_js)
        for filename in PAGES:
            page = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('data-category-gallery aria-live="polite"', page)
            self.assertIn('src="/js/category.js?v=', page)


if __name__ == "__main__":
    unittest.main()
