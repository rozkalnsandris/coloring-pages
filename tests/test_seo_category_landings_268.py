"""SEO contract for issue #268 category landing pages."""
import hashlib
import html as html_lib
import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://ausmalwiese.de"
OLD = "https://coloring.rozkalns.net"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class SeoCategoryLandingTests(unittest.TestCase):
    def setUp(self):
        registry = json.loads(read("metadata/categories.json"))
        self.categories = [(item["id"], item["label"]) for item in registry["categories"]]
        self.ids = [item[0] for item in self.categories]

    def test_exact_six_canonical_registry_categories_have_static_landings(self):
        self.assertEqual(
            self.ids,
            ["tiere", "fahrzeuge", "alphabet", "lernen", "figuren", "jahreszeiten"],
        )
        titles = set()
        descriptions = set()
        headings = set()
        for category_id, label in self.categories:
            page = read(f"{category_id}.html")
            escaped_label = html_lib.escape(label, quote=True)
            self.assertIn(f'data-category-page="{category_id}"', page)
            self.assertIn(f'data-category-label="{escaped_label}"', page)
            self.assertIn(f'<link rel="canonical" href="{ORIGIN}/{category_id}">', page)
            self.assertNotIn(OLD, page)
            title = re.search(r"<title>(.*?)</title>", page, re.S).group(1)
            desc = re.search(r'<meta name="description" content="([^"]+)">', page).group(1)
            h1 = re.search(r'<h1 id="category-title">(.*?)</h1>', page, re.S).group(1)
            self.assertTrue(title.strip())
            self.assertTrue(desc.strip())
            self.assertTrue(h1.strip())
            titles.add(title)
            descriptions.add(desc)
            headings.add(h1)
        self.assertEqual(len(titles), 6)
        self.assertEqual(len(descriptions), 6)
        self.assertEqual(len(headings), 6)

    def test_home_category_cards_are_crawlable_links_to_exact_routes(self):
        index = read("index.html")
        for category_id, _ in self.categories:
            self.assertRegex(
                index,
                rf'<a [^>]*href="/{category_id}" data-filter="{category_id}">',
            )
        self.assertIn('href="/essen-natur" data-collection-filter="essen-natur"', index)
        self.assertNotIn('type="button" data-filter=', index)

    def test_derived_essen_natur_landing_uses_topic_group_without_changing_registry(self):
        page = read("essen-natur.html")
        self.assertIn('data-category-page="essen-natur"', page)
        self.assertIn('data-category-label="Essen &amp; Natur"', page)
        self.assertIn('data-category-topics="obst,gemuese,blumen,bauernhof"', page)
        self.assertIn(f'<link rel="canonical" href="{ORIGIN}/essen-natur">', page)
        self.assertNotIn("essen-natur", self.ids)

    def test_category_runtime_filters_exact_or_derived_topic_collection(self):
        js = read("js/category.js")
        self.assertIn('fetch("/catalog.json"', js)
        self.assertIn('fetch("/topics.json"', js)
        self.assertIn("entryCategoryIds(entry).includes(category)", js)
        self.assertIn("categoryTopics.has(topicId)", js)
        version = hashlib.sha256((ROOT / "js/category.js").read_bytes()).hexdigest()[:16]
        for category_id in (*self.ids, "essen-natur"):
            self.assertIn(f'src="/js/category.js?v={version}"', read(f"{category_id}.html"))
        self.assertIn("topic.legacy_terms.some", js)
        self.assertIn("encodeURIComponent(String(id))", js)
        self.assertNotIn(OLD, js)

    def test_static_and_generated_sitemaps_include_landings_once(self):
        expected = [f"{ORIGIN}/", f"{ORIGIN}/kita", *(f"{ORIGIN}/{x}" for x in self.ids), f"{ORIGIN}/essen-natur"]
        root = ET.fromstring(read("sitemap.xml"))
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text for loc in root.findall("sm:url/sm:loc", ns)]
        self.assertEqual(urls, expected)

        generator = read("tools/coloring-pages-sitemap")
        for category_id in self.ids:
            self.assertIn(f'"{category_id}"', generator)
        self.assertIn('"essen-natur"', generator)
        self.assertIn("CATEGORY_ROUTES", generator)

    def test_container_serves_clean_extensionless_routes(self):
        dockerfile = read("Dockerfile")
        nginx = read("deploy/nginx.conf")
        for category_id in [*self.ids, "essen-natur"]:
            self.assertIn(f"{category_id}.html", dockerfile)
            self.assertIn(category_id, nginx)
        self.assertIn('try_files /$1.html =404;', nginx)


if __name__ == "__main__":
    unittest.main()
