"""Issue #567 shared topic hero: source, SEO and fallback contract (no art yet)."""
import hashlib
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class TopicHero567Tests(unittest.TestCase):
    def test_herbst_static_seo_and_art_gate(self):
        page = read("herbst.html")
        self.assertIn('href="https://ausmalwiese.de/herbst"', page)
        self.assertIn('<title>Kostenlose Herbst-Ausmalbilder zum Ausdrucken | Ausmalwiese</title>', page)
        self.assertIn('<h1 id="category-title">Kostenlose Herbst-Ausmalbilder zum Ausdrucken</h1>', page)
        self.assertIn('class="category-hero topic-landing-hero topic-landing-hero--static"', page)
        self.assertIn('data-topic-landing-art hidden', page)
        self.assertEqual(page.count('<article class="coloring-card">'), 6)
        self.assertNotIn('src="/assets/topic-hero/herbst.webp"', page)
        self.assertNotIn('href="/bauernhof"', page)

    def test_homepage_semantic_focused_hero_and_single_selector(self):
        html = read("index.html")
        app = read("js/app.js")
        css = read("css/topic-landing-hero.css")
        self.assertIn('data-focused-topic-hero', html)
        self.assertIn('<h1 id="focused-topic-title" data-focused-topic-title>', html)
        self.assertIn('data-focused-topic-art hidden', html)
        self.assertEqual(html.count('data-filter-topic'), 1)
        self.assertIn('if (typeof syncTopicLandingHero === "function") syncTopicLandingHero(selected);', app)
        self.assertIn('if (homeHero) homeHero.hidden = focused;', app)
        self.assertIn('focusedTopicIntro.hidden = !entry?.intro;', app)
        self.assertIn('globalThis.AusmalTopicHero?.get(selected.id)', app)
        self.assertIn('image.width = entry.image.width;', app)
        self.assertIn('#hero[hidden]', css)
        self.assertIn('.topic-landing-hero--with-art', css)
        self.assertIn('min-width: 0', css)
        self.assertIn('@media (max-width: 720px)', css)
        self.assertIn('object-fit: contain', css)

    def test_manifest_does_not_invent_unapproved_topics_or_images(self):
        code = read("js/topic-hero-content.js")
        self.assertIn("rozkalns.ausmalwiese.topic-hero.v1", code)
        self.assertIn("Object.prototype.hasOwnProperty.call", code)
        self.assertIn("return null;", code)
        self.assertIn('"/assets/topic-hero/" + topicId + ".webp"', code)
        self.assertNotIn("bauernhof: Object.freeze(", code)
        self.assertNotIn("tanzen: Object.freeze(", code)
        self.assertNotIn('image: Object.freeze(', code)
        for file in ("js/topic-hero-content.js", "js/app.js"):
            subprocess.run(["node", "--check", str(ROOT / file)], check=True, timeout=15)

    def test_versioned_consumers(self):
        app_hash = hashlib.sha256((ROOT / "js/app.js").read_bytes()).hexdigest()[:16]
        css_hash = hashlib.sha256((ROOT / "css/topic-landing-hero.css").read_bytes()).hexdigest()[:16]
        manifest_hash = hashlib.sha256((ROOT / "js/topic-hero-content.js").read_bytes()).hexdigest()[:16]
        for page in ("index.html", "detail.html", "kita.html", "kita-herbst.html"):
            self.assertIn(f"js/app.js?v={app_hash}", read(page))
        self.assertIn(f"css/topic-landing-hero.css?v={css_hash}", read("index.html"))
        self.assertIn(f"css/topic-landing-hero.css?v={css_hash}", read("herbst.html"))
        self.assertIn(f"js/topic-hero-content.js?v={manifest_hash}", read("index.html"))


if __name__ == "__main__":
    unittest.main()
