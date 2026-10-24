"""Legacy cookie model retirement: only erasure compatibility remains.

No Cloudflare access. These source gates ensure new persistent Like sessions and
personalized choices cannot be created after the aggregate frontend cutover.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT / "cloudflare/stats-worker.js").read_text(encoding="utf-8")


class CookieEndpointRetirementTests(unittest.TestCase):
    def test_creation_state_and_choice_routes_are_retired(self):
        for path in (
            "/api/stats/like/session",
            "/api/stats/like/state",
            "/api/stats/like/consent",
            "/api/stats/like/choice",
        ):
            self.assertIn(path, WORKER)
        self.assertIn("RETIRED_COOKIE_PATHS", WORKER)
        self.assertIn("legacy_personalized_api_retired", WORKER)
        for forbidden in (
            "LIKE_COOKIE_TTL_SECONDS",
            "crypto.getRandomValues(bytes)",
            "INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version",
            "INSERT INTO likes(page_id,visitor_hash) SELECT",
        ):
            self.assertNotIn(forbidden, WORKER)

    def test_cookie_erasure_remains_available_without_new_personalized_writes(self):
        self.assertIn('path !== "/api/stats/like/forget"', WORKER)
        self.assertIn("DELETE FROM likes WHERE visitor_hash=?", WORKER)
        self.assertIn("DELETE FROM like_cookie_sessions WHERE cookie_hash=?", WORKER)
        self.assertIn('likeSetCookie("",0)', WORKER)
        self.assertIn("erasure_unconfirmed", WORKER)

    def test_aggregate_print_does_not_read_personal_id(self):
        snippet = WORKER.split("async function recordAggregatePrint(env, request) {")[1].split("/* Source-only bounded expiry", 1)[0]
        for forbidden in ("visitor_id", "VISITOR_KEY", "readLikeCookie", "cookieLikeSession"):
            self.assertNotIn(forbidden, snippet)
        self.assertIn('["page_id","campaign"]', snippet)
        self.assertIn('rateLimit(env,ip,"aggregate-print")', snippet)
        self.assertIn("strictWrite(request)", snippet)


if __name__ == "__main__":
    unittest.main()
