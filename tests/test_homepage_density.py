"""Keep homepage gallery cards compact and surprise next to search."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class HomepageDensityTests(unittest.TestCase):
    def test_cards_follow_content_height(self):
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        gallery = css.split(".gallery {", 1)[1].split("}", 1)[0]
        self.assertIn("align-items: start;", gallery)
        self.assertIn(".badges { margin-top: 0; }", css)
        self.assertIn(".ranking-gallery .coloring-card { height: auto; }", css)
        self.assertIn('.ranking-discover[aria-busy="false"] .ranking-gallery { min-height: 0; }', css)
        self.assertIn('.ranking-discover[aria-busy="false"] .ranking-status:not([hidden]) { position: static; }', css)

    def test_surprise_is_part_of_search_toolbar_but_not_submit(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "css/surprise.css").read_text(encoding="utf-8")
        self.assertLess(html.index('data-search-form'), html.index('data-surprise-button'))
        self.assertIn('type="button" data-surprise-button', html)
        self.assertIn(".hero-search-tools .search { flex: 1 1 auto;", css)
        self.assertIn(".surprise-action { display: flex;", css)
        self.assertIn("@media (max-width: 720px)", css)
        self.assertIn("min-height: 44px", css)


if __name__ == "__main__":
    unittest.main()
