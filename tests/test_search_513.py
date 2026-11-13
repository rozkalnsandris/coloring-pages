"""Regression coverage for German search and q URL state (#513)."""
import hashlib
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Search513Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "js/app.js").read_text(encoding="utf-8")

    def test_search_helper_behavior(self):
        subprocess.run(
            ["node", str(ROOT / "tests/test_search_513.cjs")],
            cwd=ROOT,
            check=True,
            timeout=30,
        )

    def test_app_indexes_category_and_topic_metadata(self):
        self.assertIn("search?.topicTerms(topicValues, topicRegistry)", self.app)
        self.assertIn("[titleValue, ...categoryTerms, ...topicTerms]", self.app)
        self.assertIn("query.trim()", self.app)

    def test_q_is_persisted_and_restored(self):
        self.assertIn('new URLSearchParams(location.search).get("q")', self.app)
        self.assertIn("function readSearchFromUrl({ preserveWhenMissing = false } = {})", self.app)
        self.assertIn("else if (!preserveWhenMissing) searchInput.value = \"\";", self.app)
        self.assertIn("readSearchFromUrl({ preserveWhenMissing: true });", self.app)
        self.assertIn('url.searchParams.set("q", q)', self.app)
        self.assertIn('url.searchParams.delete("q")', self.app)
        self.assertIn('searchForm?.addEventListener("submit"', self.app)
        self.assertIn("syncCatalogFilterUrl();\n  applyFilters();", self.app)
        popstate = self.app.index('window.addEventListener("popstate"')
        self.assertGreater(self.app.index("readSearchFromUrl();", popstate), popstate)
        self.assertIn('if (searchInput) searchInput.value = "";', self.app)

    def test_search_and_app_assets_are_content_hashed_on_all_consumers(self):
        search_hash = hashlib.sha256((ROOT / "js/search.js").read_bytes()).hexdigest()[:16]
        app_hash = hashlib.sha256((ROOT / "js/app.js").read_bytes()).hexdigest()[:16]
        for name in ("index.html", "detail.html", "kita.html"):
            page = (ROOT / name).read_text(encoding="utf-8")
            search_tag = f'src="js/search.js?v={search_hash}"'
            app_tag = f'src="js/app.js?v={app_hash}"'
            self.assertIn(search_tag, page)
            self.assertIn(app_tag, page)
            self.assertLess(page.index(search_tag), page.index(app_tag))

    def test_existing_empty_state_remains_available(self):
        self.assertIn("Keine passenden Malvorlagen gefunden.", self.app)


if __name__ == "__main__":
    unittest.main()
