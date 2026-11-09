"""Paired mobile category disclosure regression (#186 / PR #473 follow-up)."""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MobileCategoryRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "js/category-mobile-rows.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "css/home-discovery.css").read_text(encoding="utf-8")
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_native_disclosures_preserved(self):
        self.assertEqual(self.home.count('name="category-browser"'), 6)
        self.assertIn('class="category-browser"', self.home)
        self.assertIn('data-browse-topic="weihnachten"', self.home)
        app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        self.assertIn('link.dataset.runtimeCategory = item.id;', app)

    def test_real_topic_link_nodes_move_in_dom_order(self):
        self.assertIn('pair[pair.length - 1].after(panel);', self.js)
        self.assertIn('panel.append(list);', self.js)
        self.assertIn('details.append(list);', self.js)
        self.assertNotIn("cloneNode", self.js)
        self.assertIn('detail.addEventListener("toggle", updateOpenPanel);', self.js)
        self.assertIn('summary.setAttribute("aria-controls", panel.id);', self.js)
        self.assertIn('panel.setAttribute("aria-labelledby", open.querySelector("summary").id);', self.js)
        self.assertIn('mobile.addEventListener("change", rebuild);', self.js)
        self.assertIn('node.matches("[data-runtime-category]")', self.js)
        self.assertIn('observer.observe(browser, { childList: true });', self.js)

    def test_closed_and_open_category_cards_keep_two_columns(self):
        self.assertNotIn('.category-browser:has(> details[open])', self.css)
        self.assertIn('.category-browser[data-category-mobile-rows] > details[open]', self.css)
        self.assertIn('grid-column: auto;', self.css)
        self.assertIn('.category-browser[data-category-mobile-rows] > .category-row-topics', self.css)
        self.assertIn('.category-browser[data-category-mobile-rows] > .category-row-topics[hidden]', self.css)
        self.assertIn('grid-template-columns: repeat(2, minmax(0, 1fr));', self.css)
        self.assertNotIn('grid-auto-flow: dense', self.css)
        self.assertIn('min-height: 44px;', self.css)

    def test_assets_are_versioned_by_content(self):
        for name in ("css/home-discovery.css", "js/category-mobile-rows.js"):
            digest = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()[:16]
            self.assertIn(f'{name}?v={digest}', self.home)

    def test_gallery_print_and_consent_untouched(self):
        self.assertIn('data-search-form', self.home)
        self.assertIn('data-gallery', self.home)
        self.assertIn('data-analytics-consent', self.home)
        self.assertIn('data-action-print', (ROOT / "detail.html").read_text(encoding="utf-8"))
        self.assertIn('js/print.js', (ROOT / "print.html").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
