"""Regression contract for Cloudflare email-obfuscation SEO cleanup (#495)."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAILTO = '<a href="mailto:andris@rozkalns.net">andris@rozkalns.net</a>'
PROTECTED = f"<!--email_off-->{MAILTO}<!--/email_off-->"
LEGAL_PAGES = {
    "impressum.html": 1,
    "datenschutz.html": 2,
}


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class EmailObfuscationSeoTests(unittest.TestCase):
    def test_every_legal_mailto_is_explicitly_excluded_from_cloudflare_obfuscation(self):
        for path, expected in LEGAL_PAGES.items():
            page = read(path)
            self.assertEqual(page.count(MAILTO), expected, path)
            self.assertEqual(page.count(PROTECTED), expected, path)

    def test_email_off_markers_wrap_the_complete_mailto_anchor(self):
        for path, expected in LEGAL_PAGES.items():
            page = read(path)
            protected = re.findall(
                r"<!--email_off--><a href=\"mailto:andris@rozkalns[.]net\">"
                r"andris@rozkalns[.]net</a><!--/email_off-->",
                page,
            )
            self.assertEqual(len(protected), expected, path)

    def test_source_does_not_link_to_cloudflare_email_protection_endpoint(self):
        for path in LEGAL_PAGES:
            self.assertNotIn("/cdn-cgi/l/email-protection", read(path))

    def test_legal_canonical_contract_is_unchanged(self):
        impressum = read("impressum.html")
        datenschutz = read("datenschutz.html")
        self.assertEqual(
            impressum.count(
                '<link rel="canonical" href="https://ausmalwiese.de/impressum.html">'
            ),
            1,
        )
        self.assertNotIn('content="noindex"', impressum)
        self.assertNotIn('content="noindex"', datenschutz)


if __name__ == "__main__":
    unittest.main()
