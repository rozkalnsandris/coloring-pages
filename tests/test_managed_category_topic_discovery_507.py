"""Regression coverage for managed Category↔Topic homepage discovery (#507)."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManagedCategoryTopicDiscovery507Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        cls.nginx = (ROOT / "deploy/nginx.conf").read_text(encoding="utf-8")
        cls.css = (ROOT / "css/home-discovery.css").read_text(encoding="utf-8")

    def test_public_projection_has_exact_content_mount_route(self):
        block = re.search(
            r"location = /category-topics\.json \{(?P<body>.*?)\n        \}",
            self.nginx,
            re.S,
        )
        self.assertIsNotNone(block)
        body = block.group("body")
        self.assertIn("root /var/lib/coloring-pages/public;", body)
        self.assertIn('add_header Cache-Control "no-store" always;', body)
        self.assertIn("try_files /category-topics.json =503;", body)

    def test_core_groups_declare_canonical_ids_and_keep_no_js_broad_links(self):
        for marker in (
            'data-category-ids="tiere"',
            'data-category-ids="fahrzeuge"',
            'data-category-ids="figuren"',
            'data-category-ids="jahreszeiten"',
            'data-category-ids="alphabet lernen"',
        ):
            self.assertIn(marker, self.home)
        for href in ("/tiere", "/fahrzeuge", "/figuren", "/jahreszeiten", "/alphabet", "/lernen"):
            self.assertIn(f'href="{href}"', self.home)

        for category_id in ("tiere", "fahrzeuge", "figuren", "jahreszeiten"):
            match = re.search(
                rf'<details[^>]+data-category-ids="{category_id}"[^>]*>(.*?)</details>',
                self.home,
                re.S,
            )
            self.assertIsNotNone(match)
            self.assertNotIn("data-browse-topic=", match.group(1))

        self.assertIn("data-curated-topic-group", self.home)
        self.assertIn('data-browse-topic="obst"', self.home)

    def test_consumer_validates_exact_registry_bytes_and_fails_relationship_only(self):
        helper_pos = self.home.index("js/category-topic-discovery.js")
        app_pos = self.home.index('src="js/app.js?v=')
        self.assertLess(helper_pos, app_pos)
        self.assertIn('fetch("/category-topics.json", { cache: "no-store" })', self.app)
        self.assertIn('globalThis.crypto.subtle.digest("SHA-256", bytes)', self.app)
        self.assertIn("loadCategoryTopicProjection(categoryResource, topicResource)", self.app)
        self.assertIn("renderCategoryDiscovery(categoryTopics);", self.app)
        self.assertIn("Invalid/missing relationships must not block gallery", self.app)

    def test_links_are_delegated_and_native_disclosures_keep_mobile_accessibility(self):
        self.assertIn('categoryBrowser?.addEventListener("click"', self.app)
        self.assertIn('event.target.closest("[data-browse-topic]")', self.app)
        self.assertIn('<summary>', self.home)
        self.assertIn(".category-subtopics a {", self.css)
        self.assertIn("min-height: 44px;", self.css)

    def test_behavioral_projection_contract(self):
        subprocess.run(
            ["node", str(ROOT / "tests/test_category_topic_discovery_507.cjs")],
            cwd=ROOT,
            check=True,
            timeout=30,
        )


if __name__ == "__main__":
    unittest.main()
