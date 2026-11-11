"""Offline SEO regression for the /tiere initial-HTML pilot (#485).

The six motif examples are deliberately static, source-owned *links* only.
Production /catalog.json remains canonical and replaces the seed gallery
after JavaScript loads. No image binary or production catalogue is committed.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_IDS = ("0254850", "6573390", "8919636", "0930109", "1785175", "5710253")


class TiereInitialHtmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "tiere.html").read_text(encoding="utf-8")
        cls.category_js = (ROOT / "js/category.js").read_text(encoding="utf-8")

    def initial_gallery(self):
        gallery = re.search(
            r'<div class="gallery" data-category-gallery aria-live="polite">(.*?)</div>',
            self.page,
            flags=re.S,
        )
        self.assertIsNotNone(gallery, "initial gallery must exist in source HTML")
        return gallery.group(1)

    def test_six_genuine_static_cards_not_noscript_or_js_generated(self):
        gallery = self.initial_gallery()
        cards = re.findall(r'<article class="coloring-card">(.*?)</article>', gallery, re.S)
        self.assertEqual(len(cards), len(SEED_IDS))
        self.assertNotIn("<noscript", gallery)
        self.assertNotIn("<script", gallery)
        self.assertIn('data-category-total>6</span>', self.page)
        self.assertIn("angezeigte Malvorlagen", self.page)

    def test_each_card_has_matching_crawlable_detail_links_and_webp_image(self):
        gallery = self.initial_gallery()
        cards = re.findall(r'<article class="coloring-card">(.*?)</article>', gallery, re.S)
        ids = []
        for card in cards:
            links = re.findall(r'<a\b[^>]*href="/detail[.]html[?]id=([0-9]{7})"[^>]*>', card)
            self.assertEqual(len(links), 2, "both image and title must link to the detail")
            self.assertEqual(links[0], links[1])
            match = re.search(
                r'<img\b[^>]*src="/media/([0-9]{7})/thumb[.]webp"[^>]*alt="([^"]+)"',
                card,
            )
            self.assertIsNotNone(match, "image URL and descriptive alt must exist in HTML")
            self.assertEqual(match.group(1), links[0])
            self.assertGreaterEqual(len(match.group(2)), 8)
            self.assertLessEqual(len(match.group(2)), 100)
            self.assertIn("<h3>", card)
            ids.append(links[0])
        self.assertEqual(tuple(ids), SEED_IDS)
        self.assertEqual(len(set(ids)), len(ids))

    def test_seed_is_replaced_by_existing_dynamic_catalogue_gallery(self):
        self.assertIn('data-category-page="tiere"', self.page)
        self.assertIn('data-category-gallery aria-live="polite"', self.page)
        self.assertIn('src="/js/category.js?v=', self.page)
        self.assertIn('fetch("/catalog.json"', self.category_js)
        self.assertIn('gallery.replaceChildren(fragment)', self.category_js)

    def test_unique_canonical_robots_and_useful_german_landing(self):
        self.assertEqual(
            self.page.count('<link rel="canonical" href="https://ausmalwiese.de/tiere">'),
            1,
        )
        self.assertNotIn('content="noindex"', self.page)
        self.assertIn('<html lang="de">', self.page)
        self.assertIn("<h1 id=\"category-title\">Kostenlose Tier-Ausmalbilder zum Ausdrucken</h1>", self.page)
        self.assertIn("Tier-Ausmalbilder für Kinder", self.page)


if __name__ == "__main__":
    unittest.main()
