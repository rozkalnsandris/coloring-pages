"""Regression coverage for UI/UX audit #11 + #12 category metadata filters."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_PAGES = (
    "tiere.html", "fahrzeuge.html", "alphabet.html", "lernen.html",
    "figuren.html", "essen-natur.html", "jahreszeiten.html",
)


class CategoryMetadataFilters511Tests(unittest.TestCase):
    def test_helper_filters_valid_values_and_preserves_unrelated_url_state(self):
        harness = r"""
const fs=require('node:fs'),vm=require('node:vm');
const ctx={globalThis:{},URL,URLSearchParams};
vm.runInNewContext(fs.readFileSync('js/category-metadata-filters.js','utf8'),ctx);
const api=ctx.globalThis.AusmalCategoryMetadataFilters;
const parsed=api.read('?age=3-6&difficulty=easy&campaign=dortmund-01');
const invalid=api.read('?age=9-12&difficulty=hard');
const entry={age:'3-6',difficulty:'easy'};
const unknown={};
const url=api.applyToUrl(new URL('https://example.test/tiere?campaign=dortmund-01&age=4-8'),{age:'',difficulty:'normal'});
console.log(JSON.stringify({
  parsed,invalid,
  match:api.matches(entry,parsed),
  mismatch:api.matches(entry,{age:'4-8',difficulty:''}),
  unknownUnfiltered:api.matches(unknown,{age:'',difficulty:''}),
  unknownFiltered:api.matches(unknown,{age:'3-6',difficulty:''}),
  active:api.hasActive(parsed),
  url:url.pathname+url.search,
}));
"""
        result = subprocess.run(
            ["node", "-e", harness],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=10,
        )
        data = json.loads(result.stdout)
        self.assertEqual(data["parsed"], {"age": "3-6", "difficulty": "easy"})
        self.assertEqual(data["invalid"], {"age": "", "difficulty": ""})
        self.assertTrue(data["match"])
        self.assertFalse(data["mismatch"])
        self.assertTrue(data["unknownUnfiltered"])
        self.assertFalse(data["unknownFiltered"])
        self.assertTrue(data["active"])
        self.assertEqual(data["url"], "/tiere?campaign=dortmund-01&difficulty=normal")

    def test_category_controller_keeps_url_back_forward_and_empty_recovery(self):
        source = (ROOT / "js/category.js").read_text(encoding="utf-8")
        self.assertIn('history.pushState(null, "", next)', source)
        self.assertIn('window.addEventListener("popstate"', source)
        self.assertIn("readMetadataFiltersFromUrl();", source)
        self.assertIn("Keine Malvorlagen passen zu diesen Filtern.", source)
        self.assertIn("Filter zurücksetzen", source)
        self.assertIn("Vorlagen ohne Altersangabe findest du unter", source)
        self.assertIn("AGE_FILTER_VALUES.has(entry.age)", source)
        self.assertIn("const difficultyLabel = DIFFICULTY_LABELS[entry.difficulty];", source)

    def test_all_category_pages_use_shared_filters_and_exact_content_versions(self):
        helper_hash = hashlib.sha256((ROOT / "js/category-metadata-filters.js").read_bytes()).hexdigest()[:16]
        category_hash = hashlib.sha256((ROOT / "js/category.js").read_bytes()).hexdigest()[:16]
        metadata_css_hash = hashlib.sha256((ROOT / "css/metadata-filters.css").read_bytes()).hexdigest()[:16]
        for filename in CATEGORY_PAGES:
            html = (ROOT / filename).read_text(encoding="utf-8")
            helper = f'/js/category-metadata-filters.js?v={helper_hash}'
            controller = f'/js/category.js?v={category_hash}'
            css = f'/css/metadata-filters.css?v={metadata_css_hash}'
            self.assertIn(css, html, filename)
            self.assertIn(helper, html, filename)
            self.assertIn(controller, html, filename)
            self.assertLess(html.index(helper), html.index(controller), filename)


if __name__ == "__main__":
    unittest.main()
