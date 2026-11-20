"""Issue #573: exact owner-approved Fahrzeuge Page Hero asset and HTML regression."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "assets/fahrzeuge-topic-hero.webp"
APPROVED_SHA256 = "5cf25e6cdd6a5b719f8f8c34577d3e9cba28b6b3a3c71199b24559855d9575b5"


class FahrzeugeHero573Tests(unittest.TestCase):
    def test_owner_approved_art_is_unchanged(self):
        self.assertTrue(ART.is_file())
        self.assertEqual(hashlib.sha256(ART.read_bytes()).hexdigest(), APPROVED_SHA256)

    def test_illustrated_shell_preserves_source_seo_and_gallery(self):
        html = (ROOT / "fahrzeuge.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="canonical" href="https://ausmalwiese.de/fahrzeuge">', html)
        self.assertIn('<h1 id="category-title">Kostenlose Fahrzeug-Ausmalbilder</h1>', html)
        self.assertEqual(html.count('<h1 id="category-title">'), 1)
        self.assertIn('class="category-hero page-hero page-hero--category page-hero--with-art"', html)
        self.assertEqual(html.count('class="page-hero-art"'), 1)
        self.assertIn('src="/assets/fahrzeuge-topic-hero.webp"', html)
        self.assertIn('width="1755" height="896" decoding="async" fetchpriority="high"', html)
        css = (ROOT / "css/topic-landing-hero.css").read_bytes()
        digest = hashlib.sha256(css).hexdigest()[:16]
        self.assertIn(f"/css/topic-landing-hero.css?v={digest}", html)
        self.assertNotIn("page-hero-illustrated-category.css", html)
        self.assertFalse((ROOT / "css/page-hero-illustrated-category.css").exists())
        self.assertIn(
            ".page-hero--category.page-hero--with-art .page-hero-copy {\n"
            "  align-self: start;\n}", css.decode("utf-8")
        )
        self.assertIn('alt="Ausmalwiese-Hund neben einem Feuerwehrauto und einem blauen Auto"', html)
        self.assertIn('aria-label="Breadcrumb"', html)
        self.assertIn('data-category-gallery', html)
        self.assertIn('data-category-load-more', html)
        self.assertIn('data-category-page="fahrzeuge"', html)
        # Approved Hero artwork excludes construction vehicles, not gallery motifs.
        hero = html.split('    <section class="category-hero', 1)[1].split('    </section>', 1)[0]
        self.assertNotIn('Bulldozer', hero)
        self.assertNotIn('Bagger', hero)


if __name__ == "__main__":
    unittest.main()
