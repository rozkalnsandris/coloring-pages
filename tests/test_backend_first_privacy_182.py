"""Backend-first #182 privacy split: source-only compatibility and minimization gates."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT / "cloudflare/stats-worker.js").read_text(encoding="utf-8")
SCHEMA = (ROOT / "cloudflare/stats-schema.sql").read_text(encoding="utf-8")
CLEANUP = (ROOT / "cloudflare/stats-remove-daily-visitor-hmac.sql").read_text(encoding="utf-8")


class BackendFirstPrivacySplit(unittest.TestCase):
    def test_daily_visitor_hmac_processing_is_removed(self):
        self.assertNotIn("VISITOR_HMAC_KEY", WORKER)
        self.assertNotIn("hmacSha256", WORKER)
        self.assertNotIn("daily_visitors", WORKER)
        self.assertNotIn("CREATE TABLE IF NOT EXISTS daily_visitors", SCHEMA)
        self.assertIn("DROP TABLE IF EXISTS daily_visitors", CLEANUP)

    def test_backend_is_backward_compatible_until_frontend_cutover(self):
        self.assertIn('path==="/api/stats/like") return toggleLike', WORKER)
        self.assertIn('path==="/api/stats/print") return recordPrint', WORKER)
        self.assertIn('path==="/api/stats/page") return pageStats', WORKER)
        self.assertNotIn("legacy_personalized_api_retired", WORKER)

    def test_future_like_and_print_backends_exist_in_parallel(self):
        self.assertIn('path.startsWith("/api/stats/like/")', WORKER)
        self.assertIn('path==="/api/stats/print-aggregate"', WORKER)
        self.assertIn("const LIKE_COOKIE_TTL_SECONDS = 180 * 24 * 60 * 60", WORKER)
        self.assertIn("async scheduled(", WORKER)
        self.assertIn("archived_like_totals", SCHEMA)
        self.assertIn("like_cookie_sessions", SCHEMA)

    def test_frontend_cutover_files_are_not_in_backend_pr_tree(self):
        for rel in ("css/consent.css","js/consent.js","js/like-cookie-consent.js","js/stats-cookie.js"):
            self.assertFalse((ROOT / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
