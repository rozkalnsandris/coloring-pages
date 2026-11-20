"""Offline regression for six verified vehicle motif links in initial HTML (#604)."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (
    ("3398005", "Fröhliches Auto"),
    ("2997759", "Polizeiauto"),
    ("8100589", "Fröhliches Feuerwehrauto"),
    ("8203063", "Junge Auf Traktor"),
    ("5302250", "Fröhlicher Radlader"),
    ("6266418", "Junge Im Bagger"),
)


class FahrzeugeInitialLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "fahrzeuge.html").read_text(encoding="utf-8")
        cls.category_js = (ROOT / "js/category.js").read_text(encoding="utf-8")
        cls.detail_html = (ROOT / "detail.html").read_text(encoding="utf-8")

    def initial_gallery(self):
        match = re.search(
            r'<div class="gallery" data-category-gallery aria-live="polite">(.*?)</div>',
            self.page,
            flags=re.S,
        )
        self.assertIsNotNone(match)
        return match.group(1)

    def test_exact_six_source_cards_with_native_detail_links_and_thumbnails(self):
        gallery = self.initial_gallery()
        cards = re.findall(r'<article class="coloring-card">(.*?)</article>', gallery, re.S)
        self.assertEqual(len(cards), len(SEEDS))
        self.assertNotIn("<script", gallery)
        self.assertNotIn("<noscript", gallery)

        for card, (expected_id, expected_title) in zip(cards, SEEDS):
            with self.subTest(id=expected_id):
                anchors = re.findall(
                    r'<a\b[^>]*href="/detail[.]html[?]id=([0-9]{7})"[^>]*>',
                    card,
                )
                self.assertEqual(anchors, [expected_id, expected_id])
                image = re.search(
                    r'<img\b[^>]*src="/media/([0-9]{7})/thumb[.]webp"[^>]*alt="([^"]+)"',
                    card,
                )
                self.assertIsNotNone(image)
                self.assertEqual(image.group(1), expected_id)
                self.assertGreaterEqual(len(image.group(2)), 12)
                self.assertLessEqual(len(image.group(2)), 120)
                self.assertIn(
                    f'<h3><a href="/detail.html?id={expected_id}">{expected_title}</a></h3>',
                    card,
                )

        self.assertEqual(len({id_ for id_, _ in SEEDS}), len(SEEDS))

    def test_page_semantics_canonical_metadata_and_indexability(self):
        self.assertIn('<html lang="de">', self.page)
        self.assertIn('data-category-page="fahrzeuge"', self.page)
        self.assertEqual(
            self.page.count('<link rel="canonical" href="https://ausmalwiese.de/fahrzeuge">'),
            1,
        )
        self.assertNotIn('content="noindex"', self.page)
        self.assertIn(
            '<title>Kostenlose Fahrzeug-Ausmalbilder zum Ausdrucken | Ausmalwiese</title>',
            self.page,
        )
        self.assertIn('name="description" content="Kostenlose Fahrzeug-Ausmalbilder', self.page)
        self.assertIn('<h1 id="category-title">Kostenlose Fahrzeug-Ausmalbilder</h1>', self.page)
        self.assertIn('aria-label="Breadcrumb"', self.page)
        self.assertIn('Ausmalwiese-Hund neben einem Feuerwehrauto', self.page)
        self.assertIn('Entdecke Fahrzeug-Malvorlagen für Kinder', self.page)
        self.assertIn('aria-label="Weitere Malvorlagen-Kategorien"', self.page)

    def test_initial_count_status_and_nojs_fallback(self):
        self.assertIn('data-category-total>6</span>', self.page)
        self.assertIn('angezeigte Malvorlagen', self.page)
        self.assertIn('Weitere Fahrzeug-Malvorlagen werden geladen.', self.page)
        self.assertIn(
            'Diese sechs Fahrzeug-Motive sind direkt verfügbar.',
            self.page,
        )
        self.assertIn('Für die vollständige Auswahl bitte JavaScript aktivieren.', self.page)

    def test_hydration_filters_pagination_and_print_path_remain_intact(self):
        self.assertIn('src="/js/category.js?v=', self.page)
        self.assertIn('fetch("/catalog.json"', self.category_js)
        self.assertIn('gallery.replaceChildren(fragment)', self.category_js)
        self.assertIn('const CATEGORY_PAGE_SIZE = 20;', self.category_js)
        self.assertIn('categoryVisibleLimit += CATEGORY_PAGE_SIZE;', self.category_js)
        self.assertIn('ensureCategoryMetadataFilters()', self.category_js)
        self.assertIn('ensureCategoryTopicFilter(entries)', self.category_js)
        self.assertIn('data-category-load-more hidden', self.page)
        self.assertIn('data-action-print', self.detail_html)
        self.assertIn('data-detail-preview', self.detail_html)


if __name__ == "__main__":
    unittest.main()
