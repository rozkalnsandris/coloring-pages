"""Disconnected source tests for the #376 first-party pageview client."""
from pathlib import Path
import hashlib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GoatCounterPageviewClientTests(unittest.TestCase):
    def test_client_is_minimal_same_origin_fail_open_and_no_retry(self):
        source = (ROOT / "js/pageview.js").read_text(encoding="utf-8")
        for required in (
            'const ROUTE = "/api/pageview"',
            'const PAGE_ID_RE = /^[0-9]{7}$/',
            "const attempted = new Set()",
            "attempted.add(pageId)",
            'JSON.stringify({ page_id: pageId })',
            'method: "POST"',
            '"content-type": "application/json"',
            'credentials: "omit"',
            'cache: "no-store"',
            'redirect: "error"',
            'referrerPolicy: "no-referrer"',
            "keepalive: true",
            ".catch(() => {})",
        ):
            self.assertIn(required, source)

        for forbidden in (
            "localStorage",
            "sessionStorage",
            "document.cookie",
            "navigator.userAgent",
            "campaign",
            "utm_",
            "visitor_id",
            "referrer:",
            "setTimeout",
            "setInterval",
        ):
            self.assertNotIn(forbidden, source)

    def test_detail_loads_pinned_client_before_detail_script(self):
        source = (ROOT / "js/pageview.js").read_bytes()
        digest = hashlib.sha256(source).hexdigest()[:16]
        html = (ROOT / "detail.html").read_text(encoding="utf-8")
        pageview_tag = f'js/pageview.js?v={digest}'
        detail_tag = "js/detail.js?v="
        self.assertIn(pageview_tag, html)
        self.assertLess(html.index(pageview_tag), html.index(detail_tag))

    def test_detail_emits_only_after_catalog_entry_is_validated(self):
        detail = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        lookup = 'const entry = catalog.find((item) => item && item.id === id);'
        assignment = "loadedEntryId=entry.id;"
        pageview = "window.AusmalPageviews?.track?.(entry.id);"
        self.assertIn(lookup, detail)
        self.assertIn(assignment, detail)
        self.assertIn(pageview, detail)
        self.assertLess(detail.index(lookup), detail.index(assignment))
        self.assertLess(detail.index(assignment), detail.index(pageview))

    def test_existing_stats_view_call_remains_unchanged_and_separate(self):
        detail = (ROOT / "js/detail.js").read_text(encoding="utf-8")
        pageview = "window.AusmalPageviews?.track?.(entry.id);"
        existing = "window.ColoringStats?.trackView?.(entry.id);"
        self.assertIn(existing, detail)
        self.assertLess(detail.index(pageview), detail.index(existing))


if __name__ == "__main__":
    unittest.main()
