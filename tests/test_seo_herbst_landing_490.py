"""Offline contract for the single /herbst topic landing pilot (#490)."""

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://ausmalwiese.de"
SEED_IDS = ("7297970", "6815543", "5809727", "0613080", "1377848", "2381761")

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

class HerbstLandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = read("herbst.html")
        cls.js = read("js/topic-landing.js")

    def initial_gallery(self):
        match = re.search(r'<div class="gallery" data-topic-gallery aria-live="polite">(.*?)</div>', self.page, re.S)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_unique_metadata_and_exact_self_canonical(self):
        self.assertIn("<title>Kostenlose Herbst-Ausmalbilder zum Ausdrucken | Ausmalwiese</title>", self.page)
        self.assertEqual(self.page.count(f'<link rel="canonical" href="{ORIGIN}/herbst">'), 1)
        self.assertIn('<h1 id="category-title">Kostenlose Herbst-Ausmalbilder zum Ausdrucken</h1>', self.page)
        self.assertIn("Herbst-Ausmalbilder für Kinder", self.page)
        self.assertNotIn('content="noindex"', self.page)

    def test_six_static_seed_cards_are_real_crawlable_html(self):
        cards = re.findall(r'<article class="coloring-card">(.*?)</article>', self.initial_gallery(), re.S)
        self.assertEqual(len(cards), 6)
        found = []
        for card in cards:
            links = re.findall(r'href="/detail[.]html[?]id=([0-9]{7})"', card)
            self.assertEqual(len(links), 2)
            self.assertEqual(links[0], links[1])
            image = re.search(r'<img[^>]+src="/media/([0-9]{7})/thumb[.]webp"[^>]+alt="([^"]+)"', card)
            self.assertIsNotNone(image)
            self.assertEqual(image.group(1), links[0])
            self.assertGreaterEqual(len(image.group(2)), 12)
            found.append(links[0])
        self.assertEqual(tuple(found), SEED_IDS)
        self.assertEqual(len(set(found)), 6)

    def test_runtime_uses_exact_managed_topic_membership_and_keeps_seed_on_failure(self):
        self.assertIn('fetch("/topics.json"', self.js)
        self.assertIn('fetch("/catalog.json"', self.js)
        self.assertIn('entryTopicIds(entry).includes(topicId)', self.js)
        self.assertIn('Array.isArray(entry?.topics)', self.js)
        self.assertNotIn("legacy_terms", self.js)
        self.assertIn("gallery.replaceChildren(fragment)", self.js)
        self.assertNotIn("gallery.replaceChildren", self.js.split("} catch {", 1)[1])

    def test_homepage_exposes_native_canonical_herbst_link_only_for_pilot(self):
        index = read("index.html")
        self.assertIn('<a href="/herbst"><span class="category-subtopic-icon" aria-hidden="true">🍂</span><span class="category-subtopic-label">Herbst</span></a>', index)
        self.assertIn('data-static-topic="herbst"', index)
        self.assertNotIn('topic=herbst#neu', index)
        helper = read("js/category-topic-discovery.js")
        self.assertIn('herbst: "/herbst"', helper)
        self.assertIn('index.html?topic=', helper)
        for topic in ("winter", "sommer", "dinosaurier", "sport", "weihnachten"):
            self.assertNotIn(f"topic={topic}#neu", index)

    def test_container_and_clean_route_include_only_single_topic_pilot(self):
        docker = read("Dockerfile")
        nginx = read("deploy/nginx.conf")
        self.assertIn("herbst.html", docker)
        self.assertIn("essen-natur|herbst)$", nginx)
        self.assertNotIn("dinosaurier.html", docker)
        self.assertNotIn("weihnachten.html", docker)

    def test_static_and_generated_sitemap_include_herbst_once(self):
        root = ET.fromstring(read("sitemap.xml"))
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text for loc in root.findall("sm:url/sm:loc", ns)]
        self.assertEqual(urls.count(f"{ORIGIN}/herbst"), 1)
        generator = read("tools/coloring-pages-sitemap")
        self.assertIn('PILOT_TOPIC_ROUTES = ("herbst",)', generator)
        self.assertNotIn("topics.json", generator)

if __name__ == "__main__":
    unittest.main()
