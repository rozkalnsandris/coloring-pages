"""Informational support CTA has no payment destination."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SupportHeaderTests(unittest.TestCase):
    def test_navigation_and_mobile(self):
        for name in ("index.html", "detail.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            group = html.split('class="header-actions"', 1)[1].split("</div>", 1)[0]
            support = group.index('class="header-support"')
            search = group.index('class="header-search"')
            menu = group.index('class="menu-button"')
            self.assertLess(support, search)
            self.assertLess(search, menu)
            self.assertIn('href="index.html#unterstuetzen"', group[support:search])
            self.assertIn('aria-label="Projekt unterstützen – Informationen"', group[support:search])
            self.assertNotIn("disabled", group[support:search])
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn(".header-support-label { display: none; }", css)
        self.assertIn(".header-search { display: none; }", css)

    def test_no_payment_surface(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="unterstuetzen"', home)
        self.assertIn("Wir nehmen aktuell keine Zahlungen entgegen.", home)
        for name in ("index.html", "detail.html"):
            html = (ROOT / name).read_text(encoding="utf-8").lower()
            for payment in ("ko-fi.com/", "paypal.me/", "buymeacoffee.com/", "stripe.com/", "iban"):
                self.assertNotIn(payment, html)

    def test_css_versions(self):
        for name in ("index.html", "detail.html", "print.html", "kita.html", "stats.html", "traffic.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('href="css/app.css?v=5e9842ed2f6c1edc"', html)


if __name__ == "__main__":
    unittest.main()
