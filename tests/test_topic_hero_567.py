"""Issue #567: shared topic hero and approved Herbst WebP source contract."""
import hashlib
import struct
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
        self.assertIn('class="category-hero topic-landing-hero topic-landing-hero--static topic-landing-hero--with-art page-hero page-hero--static page-hero--with-art"', page)
        self.assertIn('data-topic-landing-art>', page)
        self.assertIn('src="/assets/herbst-topic-hero.webp"', page)
        self.assertIn('alt="Ausmalwiese-Hund mit Kürbissen und buntem Herbstlaub"', page)
        self.assertIn('width="1755" height="896"', page)
        self.assertIn('fetchpriority="high"', page)
        self.assertEqual(page.count('<article class="coloring-card">'), 6)
        self.assertNotIn('href="/bauernhof"', page)

    def test_homepage_semantic_focused_hero_and_single_selector(self):
        html = read("index.html")
        app = read("js/app.js")
        css = read("css/topic-landing-hero.css")
        self.assertIn('data-focused-topic-hero', html)
        self.assertLess(html.index('data-focused-topic-hero'), html.index('id="kategorien"'))
        self.assertIn('class="hero page-hero page-hero--home page-hero--with-art"', html)
        self.assertIn('<h1 id="focused-topic-title" data-focused-topic-title tabindex="-1">', html)
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
        self.assertIn('"/assets/" + topicId + "-topic-hero.webp"', code)
        self.assertIn('"bauernhof": Object.freeze(', code)
        self.assertIn('"weihnachten": Object.freeze(', code)
        self.assertNotIn("tanzen: Object.freeze(", code)
        self.assertEqual(code.count('image: Object.freeze('), 3)
        self.assertIn('d077de2efb5b291cf41140722958aa771fea6bd716da387a37458af700b0ad74', code)
        for file in ("js/topic-hero-content.js", "js/app.js"):
            subprocess.run(["node", "--check", str(ROOT / file)], check=True, timeout=15)

    def test_approved_webp_bytes_and_dimensions(self):
        raw = (ROOT / "assets/herbst-topic-hero.webp").read_bytes()
        self.assertEqual(len(raw), 119446)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "d077de2efb5b291cf41140722958aa771fea6bd716da387a37458af700b0ad74")
        self.assertEqual(raw[:4], b"RIFF")
        self.assertEqual(raw[8:16], b"WEBPVP8 ")
        width = struct.unpack_from("<H", raw, 26)[0] & 0x3FFF
        height = struct.unpack_from("<H", raw, 28)[0] & 0x3FFF
        self.assertEqual((width, height), (1755, 896))

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
