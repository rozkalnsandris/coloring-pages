"""Regression coverage for UI/UX audit #511 finding 18 shared catalogue reads."""

import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_PAGES = (
    "tiere.html", "fahrzeuge.html", "alphabet.html", "lernen.html",
    "figuren.html", "jahreszeiten.html", "essen-natur.html",
)
APP_PAGES = ("index.html", "detail.html", "kita.html", "kita-herbst.html")
BASKET_PAGES = ("index.html", "detail.html", "kita-herbst.html") + CATEGORY_PAGES


class CatalogResource511Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        cls.detail = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        cls.category = (ROOT / "js/category.js").read_text(encoding="utf-8")
        cls.basket = (ROOT / "js/print-basket-ui.mjs").read_text(encoding="utf-8")

    def test_startup_consumers_share_one_page_level_promise_key(self):
        marker = "globalThis.__ausmalCatalogPromise"
        for source in (self.app, self.detail, self.category, self.basket):
            self.assertIn(marker, source)
            self.assertIn('cache: "no-store"', source)
            self.assertNotIn("catalog-resource.mjs", source)

    def test_home_starts_independent_registries_and_catalogue_together(self):
        self.assertIn("const catalogPromise = loadSharedCatalog();", self.app)
        self.assertIn("const [categoryResource, topicResource, catalog] = await Promise.all([", self.app)
        self.assertIn("loadCategoryRegistry(),", self.app)
        self.assertIn("loadTopicRegistry(),", self.app)
        self.assertIn("catalogPromise,", self.app)
        self.assertIn('fetch("catalog.json", { cache: "no-store" })', self.app)

    def test_detail_category_and_basket_keep_isolated_fetch_fallbacks(self):
        self.assertIn('fetch("catalog.json", { cache: "no-store" })', self.detail)
        self.assertIn('fetch("/catalog.json", { cache: "no-store" })', self.category)
        self.assertIn("catalog = await loadSharedCatalog();", self.basket)
        self.assertIn('credentials: "same-origin"', self.basket)

    def test_failed_startup_request_clears_shared_promise(self):
        for source in (self.app, self.detail, self.category, self.basket):
            self.assertIn("globalThis.__ausmalCatalogPromise = null;", source)

    def test_export_freshness_gate_stays_direct_and_uncached(self):
        self.assertEqual(self.basket.count('fetch("/catalog.json", {'), 2)
        for marker in (
            'credentials: "omit"',
            'redirect: "error"',
            'signal: controller.signal',
            "expandBasketForExport(selectedIds, catalogFresh)",
            "page.printUrl !== basket.pages[index]?.printUrl",
        ):
            self.assertIn(marker, self.basket)

    def test_changed_assets_are_content_hashed_on_all_consumers(self):
        versions = {
            "app": hashlib.sha256((ROOT / "js/app.js").read_bytes()).hexdigest()[:16],
            "detail": hashlib.sha256((ROOT / "js/detail.js").read_bytes()).hexdigest()[:16],
            "category": hashlib.sha256((ROOT / "js/category.js").read_bytes()).hexdigest()[:16],
            "basket": hashlib.sha256((ROOT / "js/print-basket-ui.mjs").read_bytes()).hexdigest()[:16],
        }
        for name in APP_PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f'js/app.js?v={versions["app"]}', html, name)
        detail = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertIn(f'js/detail.js?v={versions["detail"]}', detail)
        for name in CATEGORY_PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f'js/category.js?v={versions["category"]}', html, name)
        for name in BASKET_PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f'js/print-basket-ui.mjs?v={versions["basket"]}', html, name)


if __name__ == "__main__":
    unittest.main()
