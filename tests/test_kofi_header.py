"""Ko-fi support CTA is visible in the header but cannot take payment before URL setup."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KofiHeaderContractTests(unittest.TestCase):
    def test_support_precedes_search_on_public_pages(self):
        for name in ("index.html", "detail.html"):
            with self.subTest(page=name):
                html = (ROOT / name).read_text(encoding="utf-8")
                group_start = html.index('class="header-actions"')
                support = html.index('class="header-support"', group_start)
                search = html.index('class="header-search"', group_start)
                menu = html.index('class="menu-button"', group_start)
                group_end = html.index("</div>", group_start)
                self.assertLess(support, search)
                self.assertLess(search, menu)
                self.assertLess(menu, group_end)
                self.assertIn("Ko-fi bald verfügbar", html[support:search])
                self.assertIn("disabled", html[support:search])
                self.assertNotIn("href=", html[support:search])
                self.assertNotIn("ko-fi.com/", html)
                self.assertIn("css/app.css?v=kofi-header-v1", html)

    def test_responsive_header_keeps_mobile_menu(self):
        styles = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn(".header-actions {", styles)
        self.assertIn(".header-support-label { display: none; }", styles)
        self.assertIn(".header-actions { margin-left: auto; gap: 8px; }", styles)
        self.assertIn(".header-search { display: none; }", styles)


if __name__ == "__main__":
    unittest.main()
