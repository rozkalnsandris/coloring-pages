"""Verify mobile search-first structure without changing print or catalogue code."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MobileFirstTests(unittest.TestCase):
    def test_semantic_visual_and_keyboard_order(self):
        html=(ROOT/"index.html").read_text(encoding="utf-8")
        self.assertLess(html.index('class="hero-search-tools"'),html.index('class="hero-art"'))
        self.assertLess(html.index('data-search-form'),html.index('data-surprise-button'))
        self.assertLess(html.index('data-surprise-button'),html.index('class="hero-art"'))
        self.assertIn('data-filter="tiere"',html)
        self.assertIn('data-ranking-tab="popular"',html)
        self.assertIn('data-ranking-tab="trending"',html)
        self.assertIn('css/mobile-first.css?v=mobile-hero-size-186',html)
    def test_mobile_hero_art_keeps_natural_aspect_ratio(self):
        css=(ROOT/"css/mobile-first.css").read_text(encoding="utf-8")
        mobile=css.split("@media (max-width: 720px) {", 1)[1].split("@media (max-width: 360px) {", 1)[0]
        self.assertIn(".hero-art { width: min(100%, 420px); margin: 2px auto 0; }", mobile)
        self.assertIn(".hero-art img { max-height: none; }", mobile)
        self.assertNotIn("max-height: 125px", mobile)
        desktop=(ROOT/"css/app.css").read_text(encoding="utf-8")
        self.assertIn("width: 100%; height: auto; max-height: 390px;", desktop)

    def test_mobile_layout_and_existing_journey(self):
        css=(ROOT/"css/mobile-first.css").read_text(encoding="utf-8")
        self.assertIn('grid-template-areas: "copy" "search" "art"',css)
        self.assertIn('min-height: 94px',css)
        self.assertIn('focus-visible',css)
        self.assertIn('grid-row: 3; display: block',css)
        self.assertIn('min-height: 44px',(ROOT/"css/surprise.css").read_text(encoding="utf-8"))
        js=(ROOT/"js/app.js").read_text(encoding="utf-8")
        self.assertIn('fetch("catalog.json", { cache: "no-store" })',js)
        self.assertIn('detailHref(selected.id)',js)
        self.assertIn('js/print.js', (ROOT/"print.html").read_text(encoding="utf-8"))
