"""UI audit regressions for breadcrumb targets and visible filter summary (#515)."""
import hashlib
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BREADCRUMB_HARNESS = r"""
const fs = require("node:fs"), vm = require("node:vm");
const fixture = JSON.parse(process.argv[1]);
const source = fs.readFileSync("js/detail.js", "utf8");
const start = source.indexOf("const DETAIL_CATEGORY_ROUTES");
const end = source.indexOf("function setAction(", start);
if (start < 0 || end < 0) throw new Error("breadcrumb helper segment absent");
const context = {URLSearchParams, window:{location:{search:fixture.search || ""}}};
vm.runInNewContext(source.slice(start, end), context);
console.log(context.detailCategoryHref(fixture.category));
"""

def breadcrumb_href(category, search=""):
    if not shutil.which("node"):
        raise unittest.SkipTest("Node.js unavailable")
    result = subprocess.run(
        ["node", "-e", BREADCRUMB_HARNESS, json.dumps({"category": category, "search": search})],
        cwd=ROOT, check=True, text=True, capture_output=True,
    )
    return result.stdout.strip()

class Audit515Tests(unittest.TestCase):
    def test_breadcrumb_core_and_fallback_routes(self):
        self.assertEqual(breadcrumb_href("tiere"), "/tiere")
        self.assertEqual(breadcrumb_href("fahrzeuge"), "/fahrzeuge")
        self.assertEqual(breadcrumb_href("seasonal"), "/jahreszeiten")
        self.assertEqual(breadcrumb_href("essen-natur"), "/essen-natur")
        self.assertEqual(breadcrumb_href("natur"), "index.html?category=natur#neu")
        self.assertEqual(breadcrumb_href("INVALID VALUE"), "index.html#kategorien")

    def test_breadcrumb_preserves_only_allowlisted_campaign(self):
        self.assertEqual(breadcrumb_href("tiere", "?campaign=dortmund-01"), "/tiere?campaign=dortmund-01")
        self.assertEqual(breadcrumb_href("natur", "?campaign=dortmund-01"), "index.html?category=natur&campaign=dortmund-01#neu")
        self.assertEqual(breadcrumb_href("tiere", "?campaign=other"), "/tiere")

    def test_detail_updates_breadcrumb_href_and_hash(self):
        source = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        self.assertIn("breadcrumbCategory.href = detailCategoryHref(entry.category);", source)
        version = hashlib.sha256((ROOT / "js/detail.js").read_bytes()).hexdigest()[:16]
        self.assertIn(f"js/detail.js?v={version}", html)

    def test_visible_result_count_and_filter_summary_markup(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="metadata-filter-hint result-count" aria-live="polite" data-result-count', html)
        self.assertNotIn('class="result-count sr-only"', html)
        self.assertIn("data-active-filters", html)
        self.assertIn("data-reset-all-filters", html)
        self.assertIn("Alle Filter zurücksetzen", html)

    def test_filter_summary_reuses_existing_reset_and_tracks_constraints(self):
        source = (ROOT / "js/filter-summary.js").read_text(encoding="utf-8")
        for expected in ("Suche:", "Kategorie:", "Thema:", "Alter:", "Schwierigkeit:", "existingReset?.click()"):
            self.assertIn(expected, source)

    def test_filter_helper_asset_hash_is_exact(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        version = hashlib.sha256((ROOT / "js/filter-summary.js").read_bytes()).hexdigest()[:16]
        self.assertIn(f"js/filter-summary.js?v={version}", html)

if __name__ == "__main__":
    unittest.main()
