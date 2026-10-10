"""Minimal structural checks for draft German legal pages (not legal sign-off)."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PAGES = ("index.html", "detail.html", "kita.html", "stats.html", "traffic.html")

class ALinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)

class LegalPageSourceTests(unittest.TestCase):
    def test_pages_have_correct_operator_and_contact(self):
        for name in ("impressum.html", "datenschutz.html"):
            with self.subTest(name=name):
                s = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("Andris Rožkalns", s)
                self.assertIn("andris@rozkalns.net", s)
                self.assertIn("Meylantstraße 10", s)
                self.assertIn("44319 Dortmund", s)
                self.assertIn("Deutschland", s)
                self.assertNotIn("Noch nicht hinterlegt", s)
                self.assertNotIn("Postanschrift ist noch nicht angegeben", s)
                self.assertIn('lang="de"', s)
                self.assertIn('class="legal-footer"', s)
                self.assertNotIn("<script", s)

    def test_privacy_minimization_matches_worker_and_browser(self):
        privacy = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        frontend = (ROOT / "js/stats.js").read_text(encoding="utf-8")
        worker = (ROOT / "cloudflare/stats-worker.js").read_text(encoding="utf-8")
        self.assertIn("Körper einer HTTPS-POST-Anfrage", privacy)
        self.assertIn("pseudonymisierte Nutzungsstatistik", privacy)
        self.assertNotIn('query.set("visitor_id", visitorId)', frontend)
        self.assertIn('return requestJson("/page", {', frontend)
        self.assertIn('body: JSON.stringify({page_id: pageId, visitor_id: visitorId})', frontend)
        self.assertIn('(request.method==="GET" || request.method==="POST") && path==="/api/stats/page"', worker)
        self.assertIn('const visitorHash = await sha256(visitorId);', worker)
        print_source = frontend.split("function trackPrint(pageId) {", 1)[1].split("window.ColoringStats =", 1)[0]
        self.assertNotIn("getVisitorId", print_source)
        self.assertNotIn("visitor_id", print_source)
        self.assertIn('rateLimit(env,dailyKey,"print")', worker)
        self.assertIn("Landesbeauftragten für Datenschutz", privacy)

    def test_self_hosted_woff2_and_licenses(self):
        import base64
        import re
        css = (ROOT / "css/fonts.css").read_text(encoding="utf-8")
        payloads = re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', css)
        self.assertEqual(len(payloads), 2)
        for payload in payloads:
            content = base64.b64decode(payload, validate=True)
            self.assertEqual(content[:4], b"wOF2")
            self.assertGreater(len(content), 10000)
        for family in ("Baloo 2", "Nunito"):
            self.assertIn('font-family: "' + family + '";', css)
        for name in ("OFL-Baloo2.txt", "OFL-Nunito.txt"):
            license = (ROOT / "assets/fonts" / name).read_text(encoding="utf-8")
            self.assertIn("SIL OPEN FONT LICENSE Version 1.1", license)
        for name in (*PUBLIC_PAGES, "impressum.html", "datenschutz.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn('href="css/fonts.css?v=privacy-ofl-v1"', html)
            self.assertNotIn("fonts.googleapis.com", html)
            self.assertNotIn("fonts.gstatic.com", html)
        for name in PUBLIC_PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("js/stats.js?v=privacy-v1", html)

    def test_public_pages_link_both_legal_pages(self):
        for name in PUBLIC_PAGES:
            with self.subTest(name=name):
                p = ALinks()
                p.feed((ROOT / name).read_text(encoding="utf-8"))
                self.assertIn("impressum.html", p.hrefs)
                self.assertIn("datenschutz.html", p.hrefs)

    def test_both_pages_are_packaged(self):
        docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY impressum.html datenschutz.html /usr/share/nginx/html/", docker
        )
        self.assertIn("css/app.css", str(ROOT / "css/app.css"))
        self.assertIn(".legal-footer", (ROOT / "css/app.css").read_text(encoding="utf-8"))

    def test_blockers_remain_explicit_until_review(self):
        report = (ROOT / "docs/LEGAL_PAGES_REVIEW.md").read_text(encoding="utf-8")
        self.assertIn("NOT RELEASE READY", report)
        self.assertIn("ladungsfähige Anschrift", report)
        self.assertIn("TDDDG", report)
        self.assertIn("Google Fonts", report)

if __name__ == "__main__":
    unittest.main()
