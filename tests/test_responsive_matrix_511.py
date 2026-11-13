"""Regression contracts for UI/UX audit #511 finding 15."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MATRIX_WIDTHS = (320, 360, 361, 390, 412, 540, 541, 768, 1440)


class ResponsiveMatrix511Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "css/home-discovery.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "js/category-mobile-rows.js").read_text(encoding="utf-8")
        cls.doc = (ROOT / "docs/UI_UX_RESPONSIVE_511_15.md").read_text(encoding="utf-8")

    def test_matrix_evidence_names_every_required_width(self):
        for width in MATRIX_WIDTHS:
            self.assertIn(f"| {width} |", self.doc)
        self.assertIn("Status: **NO_FIX**", self.doc)

    def test_css_and_js_share_the_same_mobile_row_breakpoint(self):
        query = "(min-width: 361px) and (max-width: 540px)"
        self.assertGreaterEqual(self.css.count(f"@media {query}"), 3)
        self.assertIn(f'window.matchMedia("{query}")', self.js)

    def test_boundary_layout_contract_is_explicit(self):
        self.assertIn("@media (max-width: 540px)", self.css)
        self.assertIn(".category-browser { grid-template-columns: 1fr; gap: 8px; }", self.css)
        self.assertIn(
            ".category-browser { grid-template-columns: repeat(2, minmax(0, 1fr)); }",
            self.css,
        )
        self.assertIn("@media (max-width: 800px)", self.css)

    def test_horizontal_overflow_safeguards_remain(self):
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr));", self.css)
        self.assertIn("min-width: 0;", self.css)
        self.assertIn(".category-group-copy { display: grid; gap: 4px; min-width: 0; }", self.css)
        self.assertIn(".category-subtopic-label { min-width: 0; overflow-wrap: anywhere; }", self.css)
        self.assertIn(
            ".category-browser[data-category-mobile-rows] > .category-row-topics {",
            self.css,
        )

    def test_progressive_enhancement_restores_native_layout_outside_range(self):
        self.assertIn("if (!mobile.matches) return;", self.js)
        self.assertIn('browser.removeAttribute("data-category-mobile-rows");', self.js)
        self.assertIn('details.append(list);', self.js)
        self.assertIn('mobile.addEventListener("change", rebuild);', self.js)


if __name__ == "__main__":
    unittest.main()
