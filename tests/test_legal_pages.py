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

    def test_legal_pages_use_current_ausmalwiese_wordmark(self):
        for name in ("impressum.html", "datenschutz.html"):
            with self.subTest(page=name):
                html = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn('aria-label="Ausmalwiese Startseite"', html)
                self.assertIn('<span>Ausmal</span>', html)
                self.assertIn('<span class="brand-wiese"><b>w</b><b>i</b><b>e</b><b>s</b><b>e</b></span>', html)
                self.assertIn("Ausmalwiese", html)
                self.assertNotIn("Coloring Pages", html)
                self.assertNotIn("brand-pages", html)

    def test_privacy_draft_matches_existing_stats_contract(self):
        privacy = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        frontend = (ROOT / "js/stats.js").read_text(encoding="utf-8")
        worker = (ROOT / "cloudflare/stats-worker.js").read_text(encoding="utf-8")
        self.assertIn("pseudonymisierte Nutzungsstatistik", privacy)
        self.assertIn("URL-Parameter", privacy)
        self.assertIn('query.set("visitor_id", visitorId)', frontend)
        self.assertIn('return requestJson(`/page?${query}`);', frontend)
        self.assertIn('request.method==="GET" && path==="/api/stats/page"', worker)
        self.assertIn("const visitorHash = await sha256(visitorId);", worker)
        print_source = frontend.split("function trackPrint(pageId) {", 1)[1].split("window.ColoringStats =", 1)[0]
        self.assertIn("getVisitorId(true)", print_source)
        self.assertIn("visitor_id: visitorId", print_source)
        self.assertIn('rateLimit(env,body.visitor_id,"print")', worker)
        self.assertIn("Landesbeauftragten für Datenschutz", privacy)
    def test_consent_banner_legal_draft_is_explicitly_release_gated(self):
        privacy = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        report = (ROOT / "docs/LEGAL_PAGES_REVIEW.md").read_text(encoding="utf-8")
        for expected in (
            "coloring-pages-consent-v1", "coloring-pages-visitor-v1",
            "Alle ablehnen", "Alle akzeptieren", "Datenschutzeinstellungen",
            "Gefällt mir", "Druckstatistik", "URL-Parameter",
            "nicht automatisch", "ohne Einwilligung", "Cloudflare Rate Limiter",
        ):
            self.assertIn(expected.lower(), privacy.lower())
        self.assertIn("PR #183 consent banner alignment", report)
        self.assertIn("Both PRs remain Draft", report)
        self.assertIn("NOT RELEASE READY", report)

    def test_v3_notice_does_not_reuse_obsolete_v2_claims(self):
        privacy = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        report = (ROOT / "docs/LEGAL_PAGES_REVIEW.md").read_text(encoding="utf-8")
        for expected in (
            "Cloudflare Worker", "v3-", "coloring-pages-visitor-v1",
            "serverseitig erfassten Zeitpunkt", "Ablaufdatum",
            "getrennt erlaubten Zwecke", "derselben Transaktion",
            "alte v3-Kennung", "v2-Kennungen", "nicht mehr angenommen",
            "URL-Parameter", "Löschung nicht bestätigt",
            "zum Zeitpunkt der", "ohne Einwilligung", "Cloudflare Rate Limiter",
            "Backups", "nach der Einwilligung",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected.lower(), privacy.lower())
        for forbidden in (
            "nicht dauerhaft gesperrt", "Wir führen kein",
            "like_erasure_blocks", "blocked_until",
            "24-Stunden-Funktion", "coloring-pages-erasure-pending-v1",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, privacy)
        self.assertIn("v3 / PR #183 exact head", report)
        self.assertIn("eb1627dd9945f00fb84511f2fa4161371b4f1e30", report)
        self.assertIn("visitor_credentials", report)
        self.assertIn("CONSENT_TTL_SECONDS", report)
        self.assertIn("unapplied", report)
        self.assertIn("NOT RELEASE READY", report)

    def test_v3_art13_gaps_are_not_claimed_resolved(self):
        privacy = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        report = (ROOT / "docs/LEGAL_PAGES_REVIEW.md").read_text(encoding="utf-8")
        for required in ("Art. 13(1)(e)–(f)", "Art. 13(2)(a)",
                         "Art. 8", "TDDDG §25", "D1 Time Travel",
                         "legacy", "Cloudflare", "DDG §5",
                         "actual", "no legal certification"):
            with self.subTest(required=required):
                self.assertIn(required.lower(), report.lower())
        self.assertIn("die konkrete gültigkeitsdauer", privacy.lower())
        self.assertNotIn("Wir führen kein", privacy)

    def test_art13_open_facts_and_ddg_contact_are_reviewed_without_invention(self):
        report = (ROOT / "docs/LEGAL_PAGES_REVIEW.md").read_text(encoding="utf-8")
        impressum = (ROOT / "impressum.html").read_text(encoding="utf-8")
        for requirement in ("Art. 13", "DDG §5", "Cloudflare", "no verified second",
                            "not a legal sign-off"):
            self.assertIn(requirement.lower(), report.lower())
        self.assertIn("mailto:", impressum)
        self.assertNotIn('href="tel:', impressum)

    def test_self_hosted_woff2_and_licenses(self):
        import hashlib
        import re
        css = (ROOT / "css/fonts.css").read_text(encoding="utf-8")
        font_hash = hashlib.sha256(css.encode("utf-8")).hexdigest()[:16]
        app_hash = hashlib.sha256((ROOT / "css/app.css").read_bytes()).hexdigest()[:16]
        paths = re.findall(r'src: url\("\.\./(assets/fonts/[^"]+\.woff2)"\)', css)
        self.assertEqual(len(paths), 2)
        for path in paths:
            data = (ROOT / path).read_bytes()
            self.assertEqual(data[:4], b"wOF2")
            self.assertIn(hashlib.sha256(data).hexdigest()[:16], path)
        for family in ("Baloo 2", "Nunito"):
            self.assertIn('font-family: "' + family + '";', css)
        for name in ("OFL-Baloo2.txt", "OFL-Nunito.txt"):
            license_text = (ROOT / "assets/fonts" / name).read_text(encoding="utf-8-sig")
            self.assertIn("SIL OPEN FONT LICENSE", license_text)
        self.assertNotIn("data:font/", css)
        for name in (*PUBLIC_PAGES, "impressum.html", "datenschutz.html"):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f'href="css/fonts.css?v={font_hash}"', html)
            self.assertIn(f'href="css/app.css?v={app_hash}"', html)
            self.assertNotIn("fonts.googleapis.com", html)
            self.assertNotIn("fonts.gstatic.com", html)
        for name in PUBLIC_PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            expected_version = (
                "instagram-216" if name in ("index.html", "detail.html")
                else "kita-campaign-v1"
            )
            self.assertIn(f"js/stats.js?v={expected_version}", html)

    def test_privacy_uses_consistent_formal_address(self):
        import re
        privacy = (ROOT / "datenschutz.html").read_text(encoding="utf-8")
        self.assertIn("Sie können", privacy)
        self.assertIsNone(re.search(r"\b(?:du|deine|deines|kannst)\b", privacy, flags=re.I))

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
