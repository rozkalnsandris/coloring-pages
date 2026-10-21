"""Informational support CTA has no payment destination."""
import hashlib
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

    def test_internal_dashboards_share_header_contract(self):
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        self.assertIn(".dashboard-nav {", css)
        self.assertIn("height: 70px; gap: 36px;", css)
        self.assertIn("text-decoration: none; font-size: 15px; font-weight: 700;", css)
        self.assertIn(".dashboard-home-link { justify-self: end; }", css)
        self.assertNotIn(".stats-dashboard-nav", css)
        self.assertNotIn(".stats-header-inner", css)
        self.assertIn(".skip-link:focus-visible { transform: translateY(0); }", css)
        self.assertNotIn(".skip-link:focus { transform: translateY(0); }", css)

        rule = ".stats-page main h1,\n.stats-page main h2,\n.stats-page main h3,\n.stats-page main strong { font-family: var(--font-body); }"
        self.assertIn(rule, css)
        self.assertIn(".brand {", css)
        self.assertIn("font-family: var(--font-display);", css)

        for name in ("stats.html", "traffic.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('class="dashboard-nav"', html)
            self.assertIn('class="outline-link dashboard-home-link"', html)
            self.assertNotIn("stats-dashboard-nav", html)
            self.assertNotIn("stats-header-inner", html)
            self.assertNotIn("<style>\\n", html)
            self.assertNotIn("\\n</head>", html)

    def test_css_versions(self):
        css_version = hashlib.sha256((ROOT / "css/app.css").read_bytes()).hexdigest()[:16]
        for name in ("index.html", "detail.html", "print.html", "kita.html", "stats.html", "traffic.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f'href="css/app.css?v={css_version}"', html)


if __name__ == "__main__":
    unittest.main()
