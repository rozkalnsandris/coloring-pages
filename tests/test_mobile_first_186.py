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
        self.assertIn('css/mobile-first.css?v=mobile-search-first-186',html)
    def test_mobile_layout_and_existing_journey(self):
        css=(ROOT/"css/mobile-first.css").read_text(encoding="utf-8")
        self.assertIn('grid-template-areas: "copy" "search" "art"',css)
        self.assertIn('min-height: 82px',css)
        self.assertIn('focus-visible',css)
        self.assertIn('min-height: 44px',(ROOT/"css/surprise.css").read_text(encoding="utf-8"))
        js=(ROOT/"js/app.js").read_text(encoding="utf-8")
        self.assertIn('fetch("catalog.json", { cache: "no-store" })',js)
        self.assertIn('detailHref(selected.id)',js)
        self.assertIn('js/print.js', (ROOT/"print.html").read_text(encoding="utf-8"))
