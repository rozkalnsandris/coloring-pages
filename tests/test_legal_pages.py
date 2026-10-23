"""Structural and factual regression tests for German legal pages.

These checks prevent stale product claims; they are not legal certification.
"""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PAGES = ("index.html", "detail.html", "kita.html", "stats.html", "traffic.html")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


class LegalPagesTests(unittest.TestCase):
    def test_operator_contact_and_german_pages(self):
        for name in ("impressum.html", "datenschutz.html"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('lang="de"', text)
            self.assertIn("Andris Rožkalns", text)
            self.assertIn("Meylantstraße 10", text)
            self.assertIn("44319 Dortmund", text)
            self.assertIn("andris@rozkalns.net", text)
            self.assertNotIn("<script", text)

    def test_privacy_matches_aggregate_model_not_superseded_cookie_model(self):
        text = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        for expected in (
            "keine dauerhafte Browserkennung",
            "aggregierte Druckabsicht",
            "CF-Connecting-IP",
            "Cloudflare Rate Limiter",
            "Art. 6 Abs. 1 lit. f DSGVO",
            "Widerspruch",
            "Legacy-Endpunkte",
        ):
            self.assertIn(expected, text)
        for stale in (
            "__Secure-aw-like-v1",
            "180 Tage",
            "Gefällt-mir-Einstellungen für Erwachsene",
            "coloring-pages-visitor-v1",
            "visitor_id",
        ):
            self.assertNotIn(stale, text)

    def test_legacy_transition_is_not_claimed_complete(self):
        text = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        self.assertIn("Altbestände noch vorhanden", text)
        self.assertIn("getrennt geprüften Lösch- oder", text)
        self.assertIn("nicht automatisch", text)

    def test_primary_pages_link_legal_pages(self):
        for name in PUBLIC_PAGES:
            parser = Links()
            parser.feed((ROOT / name).read_text(encoding="utf-8"))
            self.assertIn("impressum.html", parser.hrefs, name)
            self.assertIn("datenschutz.html", parser.hrefs, name)

    def test_legal_pages_are_packaged(self):
        docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY impressum.html datenschutz.html /usr/share/nginx/html/", docker
        )

    def test_internal_review_tracks_current_model(self):
        review = (ROOT / "docs/LEGAL_PAGES_REVIEW.md").read_text(encoding="utf-8")
        for expected in (
            "DRAFT / SOURCE REVIEW ONLY / NO LEGAL CERTIFICATION",
            "/api/stats/like-aggregate",
            "/api/stats/print-aggregate",
            "CF-Connecting-IP",
            "Legacy personalized",
            "Remaining gates",
        ):
            self.assertIn(expected, review)


if __name__ == "__main__":
    unittest.main()
