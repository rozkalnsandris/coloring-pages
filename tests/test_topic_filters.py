"""Homepage compact topic-filter contract."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TopicFilterTests(unittest.TestCase):
    def test_topic_registry_is_unique_and_keeps_requested_core_topics(self):
        registry = json.loads((ROOT / "metadata/topics.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["schema"], "rozkalns.coloring-pages.topics.v1")
        ids = [item["id"] for item in registry["topics"]]
        self.assertEqual(len(ids), len(set(ids)))
        for expected in ("winter", "fasching", "fruehling", "ostern", "muttertag", "sommer",
                         "halloween", "obst", "gemuese", "dinosaurier", "bauernhof", "weltraum",
                         "blumen", "meerestiere", "sport", "einhoerner"):
            self.assertIn(expected, ids)
        seasonal = [item for item in registry["topics"] if item["kind"] == "seasonal"]
        self.assertTrue(seasonal)
        for item in seasonal:
            self.assertRegex(item["active_from"], r"^\d{2}-\d{2}$")
            self.assertRegex(item["active_to"], r"^\d{2}-\d{2}$")

    def test_homepage_has_compact_topic_mount_points(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("data-topic-explorer", page)
        self.assertIn("data-topic-list", page)
        self.assertIn("data-topic-clear", page)

    def test_homepage_groups_topics_under_native_disclosures(self):
        import re
        from urllib.parse import parse_qs, urlsplit
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Was möchtest du ausmalen?", page)
        self.assertNotIn("Beliebte Themen", page)
        self.assertEqual(page.count('name="category-browser"'), 6)
        self.assertIn('href="/fahrzeuge" data-filter="fahrzeuge"', page)
        groups = dict(re.findall(
            r'<details class="category-group category-group-([^"]+)"[^>]*>(.*?)</details>',
            page, re.S))
        self.assertIn('href="/alphabet"', groups["learning"])
        self.assertIn('href="/lernen"', groups["learning"])
        self.assertIn('data-browse-topic="obst"', groups["food"])
        self.assertIn('data-browse-topic="gemuese"', groups["food"])
        registry = json.loads((ROOT / "metadata/topics.json").read_text(encoding="utf-8"))
        ids = {topic["id"] for topic in registry["topics"]}
        links = re.findall(r'href="([^"]+)" data-browse-topic="([^"]+)"', page)
        self.assertEqual({topic for _, topic in links}, ids)
        for href, topic in links:
            self.assertEqual(parse_qs(urlsplit(href).query), {"topic": [topic]})
            self.assertEqual(urlsplit(href).fragment, "neu")
        version = hashlib.sha256((ROOT / "css/home-discovery.css").read_bytes()).hexdigest()[:16]
        self.assertIn(f"css/home-discovery.css?v={version}", page)

    def test_public_filters_use_explicit_category_memberships(self):
        home = (ROOT / "js/app.js").read_text(encoding="utf-8")
        landing = (ROOT / "js/category.js").read_text(encoding="utf-8")
        self.assertIn("function entryCategoryIds(entry)", home)
        self.assertIn("entries.map(entryCategoryIds)", home)
        self.assertIn("categories.includes(activeCategory)", home)
        self.assertIn("entryCategoryIds(entry).join", home)
        self.assertIn("function entryCategoryIds(entry)", landing)
        self.assertIn("entryCategoryIds(entry).includes(category)", landing)
        self.assertNotIn("if (entry.category === category)", landing)

    def test_runtime_prefers_explicit_topics_and_keeps_legacy_fallback(self):
        source = (ROOT / "js/app.js").read_text(encoding="utf-8")
        self.assertIn('fetch("/topics.json"', source)
        self.assertIn("Array.isArray(entry?.topics)", source)
        self.assertIn("topic.legacy_terms.some", source)
        self.assertIn('button.setAttribute("aria-pressed"', source)
        self.assertIn("matchesTopic", source)
        self.assertIn('new Set(["obst", "gemuese", "blumen", "bauernhof"])', source)
        self.assertIn("collectionTopics.has(topicId)", source)
        self.assertIn('new URLSearchParams(location.search).get("topic")', source)
        self.assertIn('url.searchParams.set("topic", activeTopic)', source)

    def test_public_topic_filters_match_each_explicit_membership(self):
        # A page with two canonical topics must appear once under either filter.
        home = (ROOT / "js/app.js").read_text(encoding="utf-8")
        landing = (ROOT / "js/category.js").read_text(encoding="utf-8")
        self.assertIn("new Set(entry.topics.map", home)
        self.assertIn("entryTopicIds(entry).forEach", home)
        self.assertIn("topicValues.includes(activeTopic)", home)
        self.assertIn("new Set(entry.topics.map", landing)
        self.assertIn("entryTopicIds(entry).forEach", landing)
        self.assertIn("entryTopicIds(entry).includes(activeTopic.id)", landing)

    def test_topic_chips_keep_mobile_touch_targets_and_horizontal_scroll(self):
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn(".topic-chip", css)
        self.assertIn("min-height: 48px", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("scroll-snap-type: x proximity", css)
        home_css = (ROOT / "css/home-discovery.css").read_text(encoding="utf-8")
        self.assertIn(".category-subtopics a", home_css)
        self.assertIn("min-height: 44px", home_css)
        self.assertIn("focus-visible", home_css)

    def test_category_landings_use_accessible_in_page_topic_filters(self):
        source = (ROOT / "js" / "category.js").read_text(encoding="utf-8")
        self.assertIn("categoryTopicCandidates", source)
        self.assertIn("ensureCategoryTopicFilter", source)
        self.assertIn("renderCategoryEntries", source)
        self.assertIn('button.type = "button"', source)
        self.assertIn('button.setAttribute("aria-pressed"', source)
        self.assertIn('"Malvorlagen nach Thema filtern"', source)
        self.assertIn('activeTopic.label + " entdecken"', source)

    def test_essen_natur_keeps_exact_curated_topic_scope(self):
        page = (ROOT / "essen-natur.html").read_text(encoding="utf-8")
        self.assertIn(
            'data-category-topics="obst,gemuese,blumen,bauernhof"',
            page,
        )
        source = (ROOT / "js" / "category.js").read_text(encoding="utf-8")
        self.assertIn("if (categoryTopics.size)", source)
        self.assertIn("return [...categoryTopics]", source)

    def test_canonical_category_filters_do_not_create_facet_urls(self):
        source = (ROOT / "js" / "category.js").read_text(encoding="utf-8")
        self.assertNotIn("URLSearchParams", source)
        self.assertNotIn("history.pushState", source)
        self.assertNotIn("location.search", source)
        self.assertIn("MAX_CATEGORY_TOPICS = 8", source)
        self.assertIn('category === "jahreszeiten" ? "seasonal" : "evergreen"', source)

    def test_category_topic_strip_is_mobile_first(self):
        css = (ROOT / "css" / "category.css").read_text(encoding="utf-8")
        self.assertIn(".category-topic-strip", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("scroll-snap-type: x proximity", css)
        self.assertIn(".category-topic-chip", css)
        self.assertIn("min-height: 44px", css)
        self.assertIn("min-height: 48px", css)

    def test_container_serves_topic_registry(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY metadata/topics.json /usr/share/nginx/html/topics.json", dockerfile)
        self.assertIn("COPY metadata/topics.json /usr/local/share/coloring-pages/topics.json", dockerfile)


if __name__ == "__main__":
    unittest.main()
