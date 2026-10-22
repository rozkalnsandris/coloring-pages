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
        self.assertIn("data-current-topics", page)
        self.assertIn("data-topic-list", page)
        self.assertIn("data-topic-clear", page)

    def test_homepage_explains_categories_and_popular_topics(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Nach Kategorien entdecken", page)
        self.assertIn('class="category-description"', page)
        self.assertIn("Halloween, Herbst &amp; Weihnachten", page)
        self.assertIn("Beliebte Themen", page)
        self.assertIn("Obst, Gemüse, Dinosaurier, Weltraum &amp; mehr direkt auswählen.", page)
        version = hashlib.sha256((ROOT / "css/home-discovery.css").read_bytes()).hexdigest()[:16]
        self.assertIn(f"css/home-discovery.css?v={version}", page)

    def test_runtime_prefers_explicit_topics_and_keeps_legacy_fallback(self):
        source = (ROOT / "js/app.js").read_text(encoding="utf-8")
        self.assertIn('fetch("/topics.json"', source)
        self.assertIn("Array.isArray(entry?.topics)", source)
        self.assertIn("topic.legacy_terms.some", source)
        self.assertIn('button.setAttribute("aria-pressed"', source)
        self.assertIn("matchesTopic", source)
        self.assertIn('new URLSearchParams(location.search).get("topic")', source)
        self.assertIn('url.searchParams.set("topic", activeTopic)', source)

    def test_topic_chips_keep_mobile_touch_targets_and_horizontal_scroll(self):
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn(".topic-chip", css)
        self.assertIn("min-height: 48px", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("scroll-snap-type: x proximity", css)
        home_css = (ROOT / "css/home-discovery.css").read_text(encoding="utf-8")
        self.assertIn(".category-description", home_css)
        self.assertIn(".topic-heading-copy p", home_css)

    def test_container_serves_topic_registry(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY metadata/topics.json /usr/share/nginx/html/topics.json", dockerfile)


if __name__ == "__main__":
    unittest.main()
