"""Focused structural regressions for issue #256 legal-page reconciliation.

These checks verify source facts and packaging; they are not legal certification.
"""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEGAL_FOOTER_PAGES = ("index.html", "detail.html", "datenschutz.html", "impressum.html")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


class LegalPages256Tests(unittest.TestCase):
    def test_impressum_has_operator_contact(self):
        text = (ROOT / "impressum.html").read_text(encoding="utf-8")
        for expected in (
            'lang="de"',
            "Andris Rožkalns",
            "Meylantstraße 10",
            "44319 Dortmund",
            "andris@rozkalns.net",
        ):
            self.assertIn(expected, text)
        self.assertIn('src="js/social-footer.js?v=', text)
        self.assertIn('src="js/public-nav.js?v=', text)
        self.assertNotIn("goatcounter-simple.js", text)

    def test_existing_legal_footers_link_both_pages(self):
        for name in LEGAL_FOOTER_PAGES:
            parser = Links()
            parser.feed((ROOT / name).read_text(encoding="utf-8"))
            self.assertIn("/impressum.html", parser.hrefs, name)
            self.assertIn("/datenschutz.html", parser.hrefs, name)

    def test_privacy_copy_matches_aggregate_like_print_model(self):
        text = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        for expected in (
            "keine dauerhafte Browserkennung",
            "keinen Like-Cookie",
            "kein Fingerprinting",
            "Cloudflare Rate Limiter",
            "nicht als Reaktions- oder Druckkennung in D1 gespeichert",
            "nicht automatisch gelöscht",
        ):
            self.assertIn(expected, text)
        for stale in (
            "__Secure-aw-like-v1",
            "180 Tage",
            "coloring-pages-visitor-v1",
        ):
            self.assertNotIn(stale, text)

    def test_impressum_is_packaged(self):
        docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY stats.html traffic.html kita.html kalender.html impressum.html datenschutz.html /usr/share/nginx/html/",
            docker,
        )

    def test_review_records_current_scope_and_limits(self):
        text = (ROOT / "docs/LEGAL_PAGES_REVIEW.md").read_text(encoding="utf-8")
        for expected in (
            "SOURCE REVIEW ONLY / NO LEGAL CERTIFICATION",
            "/api/stats/like-aggregate",
            "HTTP 410",
            "impressum.html",
            "does not mutate D1",
            "Draft PR #158",
        ):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
