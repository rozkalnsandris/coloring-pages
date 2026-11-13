"""Regression coverage for UI/UX audit #511 finding 18 category pagination."""

import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_PAGES = (
    "tiere.html", "fahrzeuge.html", "alphabet.html", "lernen.html",
    "figuren.html", "jahreszeiten.html", "essen-natur.html",
)


class CategoryPagination511Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "js/category.js").read_text(encoding="utf-8")

    def test_category_uses_same_twenty_item_batch_as_home(self):
        self.assertIn("const CATEGORY_PAGE_SIZE = 20;", self.source)
        self.assertIn("let categoryVisibleLimit = CATEGORY_PAGE_SIZE;", self.source)
        self.assertIn(
            "const visibleEntries = filteredEntries.slice(0, categoryVisibleLimit);",
            self.source,
        )
        self.assertIn(
            "loadMoreButton.hidden = visibleEntries.length >= filteredEntries.length;",
            self.source,
        )

    def test_filters_and_history_reset_visible_batch(self):
        self.assertGreaterEqual(
            self.source.count("renderCategoryEntries(categoryEntries, { resetLimit: true });"),
            5,
        )
        self.assertIn("renderCategoryEntries(entries, { resetLimit: true });", self.source)
        self.assertIn("if (resetLimit) categoryVisibleLimit = CATEGORY_PAGE_SIZE;", self.source)

    def test_keyboard_load_more_focuses_first_new_card(self):
        self.assertIn(
            'const previousVisibleCount = gallery?.querySelectorAll(".coloring-card").length || 0;',
            self.source,
        )
        self.assertIn("const shouldMoveFocus = event.detail === 0;", self.source)
        self.assertIn(
            'nextCards[previousVisibleCount]?.querySelector("a")?.focus({ preventScroll: true });',
            self.source,
        )

    def test_all_category_pages_expose_hashed_load_more_contract(self):
        version = hashlib.sha256((ROOT / "js/category.js").read_bytes()).hexdigest()[:16]
        for filename in CATEGORY_PAGES:
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('data-category-load-more', html, filename)
            self.assertIn('>Mehr anzeigen</button>', html, filename)
            self.assertIn(f'src="/js/category.js?v={version}"', html, filename)


if __name__ == "__main__":
    unittest.main()
