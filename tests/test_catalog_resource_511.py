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
BASKET_PAGES = ("index.html", "detail.html") + CATEGORY_PAGES


class CatalogResource511Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = (ROOT / "js/catalog-resource.mjs").read_text(encoding="utf-8")
        cls.app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        cls.detail = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        cls.category = (ROOT / "js/category.js").read_text(encoding="utf-8")
        cls.basket = (ROOT / "js/print-basket-ui.mjs").read_text(encoding="utf-8")

    def test_shared_catalogue_loader_memoizes_one_page_request(self):
        self.assertIn("let catalogPromise = null;", self.shared)
        self.assertIn("if (!catalogPromise)", self.shared)
        self.assertEqual(self.shared.count('fetch("/catalog.json"'), 1)
        self.assertIn('cache: "no-store"', self.shared)
        self.assertIn('credentials: "same-origin"', self.shared)
        self.assertIn("catalogPromise = null;", self.shared)
        self.assertIn("return catalogPromise;", self.shared)

    def test_home_starts_independent_registries_and_catalogue_together(self):
        self.assertIn('const catalogPromise = import("/js/catalog-resource.mjs")', self.app)
        self.assertIn("const [categoryResource, topicResource, catalog] = await Promise.all([", self.app)
        self.assertIn("loadCategoryRegistry(),", self.app)
        self.assertIn("loadTopicRegistry(),", self.app)
        self.assertIn("catalogPromise,", self.app)
        self.assertNotIn('fetch("catalog.json"', self.app)

    def test_detail_category_and_basket_share_catalogue_loader(self):
        self.assertIn('import("/js/catalog-resource.mjs")', self.detail)
        self.assertIn('import("/js/catalog-resource.mjs")', self.category)
        self.assertIn('from "./catalog-resource.mjs"', self.basket)
        self.assertIn("catalog = await loadCatalog();", self.basket)
        self.assertNotIn('fetch("catalog.json"', self.detail)
        self.assertNotIn('fetch("/catalog.json"', self.category)

    def test_export_freshness_gate_stays_direct_and_uncached(self):
        self.assertEqual(self.basket.count('fetch("/catalog.json", {'), 1)
        for marker in (
            'cache: "no-store"',
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
