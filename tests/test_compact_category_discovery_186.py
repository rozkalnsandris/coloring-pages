"""Source regressions for the compact mobile category browser (#186).

Live-browser and print-master acceptance remain separate checks.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CompactCategoryDiscovery186Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "css/home-discovery.css").read_text(encoding="utf-8")

    def test_home_keeps_native_category_and_topic_navigation(self):
        self.assertIn('<nav class="category-browser"', self.home)
        self.assertIn('name="category-browser"', self.home)
        self.assertIn('data-filter="tiere"', self.home)
        self.assertIn('data-filter="fahrzeuge"', self.home)
        self.assertIn('data-browse-topic="weihnachten"', self.home)
        self.assertIn('href="#neu" data-reset-filters', self.home)

    def test_mobile_two_column_with_full_width_open_disclosure(self):
        compact = self.css.split(
            "@media (min-width: 361px) and (max-width: 540px) {", 1
        )[1]
        for rule in (
            "grid-template-columns: repeat(2, minmax(0, 1fr));",
            ".category-group[open] { grid-column: 1 / -1; }",
            ".category-group[open] .category-subtopics",
            ".category-group-hint { display: none; }",
            "min-height: 76px;",
        ):
            self.assertIn(rule, compact)
        self.assertIn(
            ".category-browser { grid-template-columns: 1fr; gap: 8px; }",
            self.css,
        )
        self.assertIn(
            ".category-subtopics a {", self.css
        )
        self.assertIn("min-height: 44px;", self.css)
        self.assertIn(
            ".category-subtopics a:hover { background: var(--category-tint); }",
            self.css,
        )
        self.assertNotIn("text-decoration: underline", self.css)
        self.assertNotIn("text-underline-offset", self.css)
        self.assertIn(".category-subtopics a:focus-visible", self.css)
        self.assertIn(
            "grid-template-columns: repeat(4, minmax(0, 1fr));",
            self.css,
        )


    def test_open_category_keeps_consistent_mobile_card_widths(self):
        self.assertNotIn(
            ".category-browser:has(> details[open])",
            self.css,
        )
        self.assertIn(
            ".category-browser[data-category-mobile-rows] > details[open]",
            self.css,
        )
        self.assertIn(
            ".category-browser[data-category-mobile-rows] > .category-row-topics",
            self.css,
        )
        self.assertIn(
            ".category-browser { grid-template-columns: repeat(2, minmax(0, 1fr)); }",
            self.css,
        )
        self.assertNotIn("grid-auto-flow: dense", self.css)

    def test_runtime_category_icon_matches_core_card_slot(self):
        self.assertIn(".category-direct[data-runtime-category]::before", self.css)
        self.assertIn('content: "\\1f3a8";', self.css)
        self.assertIn("flex: 0 0 48px;", self.css)
        self.assertIn("flex-basis: 34px;", self.css)
        self.assertIn("overflow-wrap: anywhere;", self.css)
        js = (ROOT / "js/app.js").read_text(encoding="utf-8")
        self.assertIn('link.dataset.runtimeCategory = item.id;', js)
        self.assertIn('link.className = "category-group category-group-vehicles category-direct";', js)

    def test_existing_find_preview_print_contract_untouched(self):
        self.assertIn(
            "css/home-discovery.css?v=3c0db56e326f0fb8", self.home
        )
        self.assertIn('data-search-form', self.home)
        self.assertIn('data-gallery', self.home)
        self.assertIn('data-ranking-tab="trending"', self.home)
        self.assertIn('data-ranking-tab="popular"', self.home)
        self.assertIn('data-analytics-consent', self.home)
        detail = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertIn('data-detail-page-switcher', detail)
        self.assertIn('data-action-print', detail)
        self.assertIn('data-action-png', detail)
        print_page = (ROOT / "print.html").read_text(encoding="utf-8")
        self.assertIn('data-print-button', print_page)
        self.assertIn('js/print.js', print_page)


if __name__ == "__main__":
    unittest.main()
