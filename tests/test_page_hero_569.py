"""#569 shared Page Hero v2: semantic shell, real breadcrumbs, SEO invariants."""
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ("alphabet", "essen-natur", "fahrzeuge", "figuren",
              "jahreszeiten", "lernen", "tiere")


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class PageHeroV2Tests(unittest.TestCase):
    def test_consistent_shell_and_real_html_headings(self):
        home = read("index.html")
        self.assertEqual(home.count('class="hero page-hero page-hero--home page-hero--with-art"'), 1)
        self.assertIn('<p class="page-hero-location" aria-label="Aktuelle Seite">Startseite</p>', home)
        self.assertNotIn('<nav class="page-hero-breadcrumbs" aria-label="Breadcrumb">', home)
        self.assertIn('data-search-form', home)
        self.assertIn('data-surprise-button', home)
        self.assertEqual(home.count('data-focused-topic-hero'), 1)
        self.assertLess(home.index('data-focused-topic-hero'), home.index('id="kategorien"'))
        self.assertIn('aria-current="page"></span>', home)
        self.assertEqual(home.count('data-filter-topic'), 1)
        self.assertEqual(home.count('id="hero-title"'), 1)
        self.assertEqual(home.count('id="focused-topic-title"'), 1)
        self.assertIn('id="neu"', home)
        for name in CATEGORIES:
            html = read(name + ".html")
            if name == "fahrzeuge":
                self.assertIn('class="category-hero page-hero page-hero--category page-hero--with-art"', html)
            else:
                self.assertIn('class="category-hero page-hero page-hero--category"', html)
            self.assertIn('class="container page-hero-grid"', html)
            self.assertIn('class="category-hero-copy page-hero-copy"', html)
            self.assertEqual(html.count('<h1 id="category-title">'), 1)
            self.assertEqual(html.count('aria-label="Breadcrumb"'), 1)
            self.assertRegex(html, r'<ol><li><a href="/">Startseite</a></li><li><span aria-current="page">[^<]+</span></li></ol>')
            self.assertNotIn('data-search-form', html)
            self.assertNotIn('data-surprise-button', html)
            if name == "fahrzeuge":
                self.assertIn('src="/assets/fahrzeuge-topic-hero.webp"', html)
                self.assertEqual(html.count('class="page-hero-art"'), 1)
            else:
                self.assertNotIn('page-hero-art', html)

    def test_herbst_provenance_and_three_level_crumb(self):
        h = read("herbst.html")
        self.assertIn('<ol><li><a href="/">Startseite</a></li><li><a href="/jahreszeiten">Jahreszeiten &amp; Feste</a></li><li><span aria-current="page">Herbst</span></li></ol>', h)
        self.assertIn('class="container topic-landing-grid page-hero-grid"', h)
        self.assertIn('src="/assets/herbst-topic-hero.webp"', h)
        self.assertIn('width="1755" height="896"', h)
        self.assertIn('<link rel="canonical" href="https://ausmalwiese.de/herbst">', h)
        self.assertEqual(h.count('<article class="coloring-card">'), 6)
        image = (ROOT / "assets/herbst-topic-hero.webp").read_bytes()
        self.assertEqual(hashlib.sha256(image).hexdigest(), "d077de2efb5b291cf41140722958aa771fea6bd716da387a37458af700b0ad74")

    def test_alignment_and_topic_entry_regressions(self):
        css = read("css/topic-landing-hero.css")
        app = read("js/app.js")
        discovery = read("js/category-topic-discovery.js")
        home = read("index.html")
        self.assertIn(".page-hero--home .page-hero-copy { grid-area: copy; align-self: start; }", css)
        self.assertIn(".page-hero--home .page-hero-art { grid-area: art; align-self: start; }", css)
        self.assertIn("mix-blend-mode: multiply;", css)
        self.assertIn(".page-hero--topic { scroll-margin-top: 88px; }", css)
        self.assertIn('focused-topic-title" data-focused-topic-title tabindex="-1"', home)
        self.assertIn('clearTopicAnchor: moveFocus && Boolean(activeTopic)', app)
        self.assertIn('topicTarget.scrollIntoView({ block: "start" })', app)
        self.assertIn('"Passende Malvorlagen entdecken"', app)
        self.assertIn('index.html?topic=${encodeURIComponent(topicId)}', discovery)
        self.assertNotIn('index.html?topic=${encodeURIComponent(topicId)}#neu', discovery)
        self.assertNotRegex(home, r'index\.html\?topic=[a-z0-9-]+#neu')

    def test_single_css_version_and_source_seo(self):
        css_path = ROOT / "css/topic-landing-hero.css"
        sha = hashlib.sha256(css_path.read_bytes()).hexdigest()[:16]
        self.assertIn("mask-composite: intersect;", read("css/topic-landing-hero.css"))
        self.assertIn('max-height: 200px', read("css/topic-landing-hero.css"))
        self.assertIn('page-hero-breadcrumbs', read("css/topic-landing-hero.css"))
        for p in ("index.html", "herbst.html", *(x + ".html" for x in CATEGORIES)):
            page = read(p)
            self.assertIn(f"css/topic-landing-hero.css?v={sha}", page)
            self.assertEqual(page.count('<link rel="canonical"'), 1)
            self.assertEqual(len(re.findall(r'<meta name="description" content="[^"]+">', page)), 1)


if __name__ == "__main__":
    unittest.main()
