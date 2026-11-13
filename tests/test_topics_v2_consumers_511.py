"""Regression coverage for UI/UX audit #01 topics v2 consumers."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TopicsV2Consumers511Tests(unittest.TestCase):
    def test_shared_v2_parser_behavior(self):
        subprocess.run(
            ["node", str(ROOT / "tests/test_topic_registry_511.cjs")],
            cwd=ROOT,
            check=True,
            timeout=30,
        )

    def test_category_consumer_uses_shared_v2_parser(self):
        source = (ROOT / "js/category.js").read_text(encoding="utf-8")
        self.assertIn('import("/js/topic-registry.js")', source)
        self.assertIn("AusmalTopicRegistry.parse(payload)", source)
        self.assertNotIn("rozkalns.coloring-pages.topics.v1", source)
        self.assertIn("entryTopicIds(entry)", source)
        self.assertIn("legacy_terms", source)

    def test_calendar_consumer_uses_shared_v2_parser_and_keeps_fallback(self):
        source = (ROOT / "js/calendar.js").read_text(encoding="utf-8")
        self.assertIn('import("/js/topic-registry.js")', source)
        self.assertIn("AusmalTopicRegistry.toMap(registry)", source)
        self.assertNotIn("rozkalns.coloring-pages.topics.v1", source)
        self.assertIn("legacyTopicMatch", source)
        self.assertIn("topics = new Map();", source)


if __name__ == "__main__":
    unittest.main()
