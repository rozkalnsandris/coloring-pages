"""Issue #564: managed Topic switch remains navigable without duplicating controls."""
import hashlib
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TopicNavigation564Tests(unittest.TestCase):
    def test_fixed_herbst_is_canonical_and_home_keeps_one_select(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        landing = (ROOT / "herbst.html").read_text(encoding="utf-8")
        app = (ROOT / "js/app.js").read_text(encoding="utf-8")
        topic = (ROOT / "js/topic-landing.js").read_text(encoding="utf-8")
        self.assertIn('href="https://ausmalwiese.de/herbst"', landing)
        self.assertEqual(home.count('data-filter-topic'), 1)
        self.assertNotIn('data-clear-active-topic', home)
        self.assertIn('if (topicField) topicField.hidden = false;', app)
        self.assertIn('topicFilter.value === "herbst"', app)
        self.assertIn('new URL("/herbst", window.location.origin)', app)
        self.assertIn('filterPanel.setTopics(managedTopics, topicId)', topic)
        self.assertIn('new URL(selected === "herbst" ? "/herbst" : "/", window.location.origin)', topic)
        self.assertIn('filterPanel.topic.addEventListener("change"', topic)
        self.assertIn('window.addEventListener("pageshow"', topic)
        self.assertIn('filterPanel.topic.value = topicId;', topic)
        self.assertIn('filterPanel.topic.setAttribute("aria-describedby", note.id)', topic)
        self.assertIn('if (destination.pathname === "/") destination.hash = "#neu";', topic)
        self.assertIn('entryTopicIds(entry).includes(topicId)', topic)
        self.assertIn('gallery.replaceChildren(fragment)', topic)
        self.assertNotIn("gallery.replaceChildren", topic.split("} catch {", 1)[1])
        for script in ("js/app.js", "js/topic-landing.js"):
            subprocess.run(["node", "--check", str(ROOT / script)], check=True, timeout=15)

    def test_exact_resource_versions_and_no_new_indexable_routes(self):
        app = hashlib.sha256((ROOT / "js/app.js").read_bytes()).hexdigest()[:16]
        topic = hashlib.sha256((ROOT / "js/topic-landing.js").read_bytes()).hexdigest()[:16]
        for page in ("index.html", "detail.html", "kita.html", "kita-herbst.html"):
            self.assertIn(f"js/app.js?v={app}", (ROOT / page).read_text(encoding="utf-8"))
        landing = (ROOT / "herbst.html").read_text(encoding="utf-8")
        self.assertIn(f"js/topic-landing.js?v={topic}", landing)
        self.assertNotIn('href="/bauernhof"', landing)
        self.assertNotIn('href="/tanzen"', landing)


if __name__ == "__main__":
    unittest.main()
