"""Regression coverage for UI/UX audit #09 + #10 homepage discovery and compact intros."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HomepageDiscoveryIntro511Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "js/app.js").read_text(encoding="utf-8")

    def test_diverse_discovery_precedes_true_latest_and_weekly_moves_below_latest(self):
        self.assertLess(self.home.index("data-discovery-picks"), self.home.index('id="neu"'))
        self.assertLess(self.home.index('id="neu"'), self.home.index("data-weekly-feature"))
        self.assertLess(self.home.index("data-weekly-feature"), self.home.index('id="entdecken"'))
        self.assertIn("Bunt gemischt entdecken", self.home)
        self.assertIn("Zu den neuesten Malvorlagen", self.home)
        self.assertIn('<h2 id="gallery-title" tabindex="-1">Neue Malvorlagen</h2>', self.home)

    def test_discovery_uses_existing_catalogue_without_an_extra_fetch(self):
        helper = (ROOT / "js/discovery-picks.js").read_text(encoding="utf-8")
        self.assertNotIn("fetch(", helper)
        self.assertIn("AusmalDiscoveryPicks?.choose(entries, 4)", self.app)
        self.assertIn("createCatalogCard(entry)", self.app)
        self.assertIn("hasActiveCatalogFilters", self.app)
        self.assertIn("updateDiscoveryPicksVisibility", self.app)

    def test_exact_content_versions_and_script_order(self):
        for filename in ("js/discovery-picks.js", "js/app.js", "css/home-compact.css"):
            digest = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()[:16]
            self.assertIn(filename + "?v=" + digest, self.home)
        self.assertLess(self.home.index("js/discovery-picks.js"), self.home.index("js/app.js"))

    def test_compact_intro_copy_on_category_and_calendar_pages(self):
        for filename in (
            "tiere.html", "fahrzeuge.html", "alphabet.html", "lernen.html",
            "figuren.html", "essen-natur.html", "jahreszeiten.html",
        ):
            html = (ROOT / filename).read_text(encoding="utf-8")
            hero = html.split('<section class="category-hero"', 1)[1].split("</section>", 1)[0]
            paragraph = hero.split("<p>", 1)[1].split("</p>", 1)[0]
            self.assertLessEqual(len(paragraph), 110, filename)
            self.assertIn("A4", paragraph)
        calendar = (ROOT / "kalender.html").read_text(encoding="utf-8")
        self.assertIn("Finde Malvorlagen nach Monat, Jahreszeit oder Fest", calendar)
        self.assertIn("Die Themen sind Anregungen; Ferien und Schulbeginn", calendar)

    def test_diversity_selector_prefers_distinct_categories_and_preserves_input_order(self):
        harness = r"""
const fs=require('node:fs'),vm=require('node:vm');
const ctx={globalThis:{}};
vm.runInNewContext(fs.readFileSync('js/discovery-picks.js','utf8'),ctx);
const catalog=JSON.parse(process.argv[1]);
const before=catalog.map(x=>x.id);
const picks=ctx.globalThis.AusmalDiscoveryPicks.choose(catalog,4);
console.log(JSON.stringify({before,after:catalog.map(x=>x.id),ids:picks.map(x=>x.id),cats:picks.map(x=>x.category)}));
"""
        catalog = [
            {"id":"1000001","title":"Tier 1","thumb":"/media/1000001/thumb.webp","category":"tiere"},
            {"id":"1000002","title":"Tier 2","thumb":"/media/1000002/thumb.webp","category":"tiere"},
            {"id":"1000003","title":"Auto","thumb":"/media/1000003/thumb.webp","category":"fahrzeuge"},
            {"id":"1000004","title":"Lernen","thumb":"/media/1000004/thumb.webp","category":"lernen"},
            {"id":"1000005","title":"Winter","thumb":"/media/1000005/thumb.webp","category":"jahreszeiten"},
        ]
        result = subprocess.run(
            ["node", "-e", harness, json.dumps(catalog)],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=10,
        )
        data = json.loads(result.stdout)
        self.assertEqual(data["before"], data["after"])
        self.assertEqual(data["ids"], ["1000001", "1000003", "1000004", "1000005"])
        self.assertEqual(len(set(data["cats"])), 4)


if __name__ == "__main__":
    unittest.main()
