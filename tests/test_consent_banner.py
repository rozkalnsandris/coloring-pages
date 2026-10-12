import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ConsentBannerSourceTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_pages_load_consent_before_stats(self):
        for page in ("index.html", "detail.html", "kita.html"):
            html = self.read(page)
            self.assertIn('css/consent.css?v=199486ea95f10006', html)
            self.assertLess(html.index("js/consent.js?v=7587038c57f09f78"),
                            html.index("js/stats.js?v=1f8620e78509d50b"))

    def test_banner_is_fixed_and_non_blocking(self):
        css = self.read("css/consent.css")
        js = self.read("js/consent.js")
        self.assertIn("position: fixed;", css)
        self.assertIn("bottom: 0;", css)
        self.assertIn("width: 100%;", css)
        self.assertIn("font: 400 12px", css)
        for label in ("Alle ablehnen", "Einstellungen", "Alle akzeptieren",
                      "Datenschutzeinstellungen", "Auswahl speichern"):
            self.assertIn(label, js)
        self.assertIn("data-consent-like", js)
        self.assertIn("data-consent-print", js)
        self.assertNotIn("getItem(ID_KEY)", js)
        self.assertIn("removeItem(ID_KEY)", js)
        self.assertIn("Löschung nicht bestätigt", js)
        self.assertIn("changeCredential(next,priorV3)", js)
        self.assertNotIn("coloring-pages-erasure-pending-v1", js)
        self.assertNotIn("retryPendingErasure", js)

    def test_stats_fail_closed_for_both_purposes(self):
        js = self.read("js/stats.js")
        self.assertIn('allows?.(purpose) !== true', js)
        self.assertIn('allows?.("like") !== true', js)
        self.assertIn('allows?.("print") !== true', js)
        self.assertIn('ensureCredential("print")', js)
        self.assertIn('getVisitorId(false)', js)
        self.assertIn('if (visitorId) return requestJson("/page", {', js)

    def test_print_remains_independent_from_consent(self):
        js = self.read("js/detail.js")
        self.assertIn("ColoringStats?.trackPrint?.(loadedEntryId)", js)
        self.assertIn("startHtmlPrint(printLink.href);", js)
        self.assertLess(js.index("ColoringStats?.trackPrint?.(loadedEntryId)"),
                        js.index("startHtmlPrint(printLink.href);"))
        self.assertIn('ColoringConsent?.openSettings?.()', js)
        self.assertIn('"coloring-consent-changed"', js)

    def test_print_page_is_clean(self):
        html = self.read("print.html")
        self.assertNotIn("consent.js", html)
        self.assertNotIn("consent.css", html)
