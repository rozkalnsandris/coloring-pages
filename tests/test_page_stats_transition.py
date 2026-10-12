"""Legacy personalized GET is fenced; only registered v3 POST can personalize."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PageStatusCompatibilityTests(unittest.TestCase):
    def test_legacy_get_is_forbidden_but_anonymous_get_remains(self):
        worker=(ROOT/"cloudflare/stats-worker.js").read_text()
        self.assertIn('url.searchParams.has("visitor_id")',worker)
        self.assertIn('legacy_credential_forbidden',worker)
        self.assertIn('path==="/api/stats/page"',worker)
        self.assertIn('credential_expired',worker)
        self.assertIn('like_allowed=1 AND expires_at>unixepoch()',worker)
        self.assertIn('if (visitorId) return requestJson("/page"',(ROOT/"js/stats.js").read_text())
