"""Proposed cookie endpoints: static gates against accidental Print identity linkage.

Functional browser/Worker edge tests remain required before release.
"""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WORKER = (ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")


class CookieEndpointDraftTests(unittest.TestCase):
    def test_cookie_is_secure_and_only_on_like_route(self):
        self.assertIn('const LIKE_COOKIE_NAME = "__Secure-aw-like-v1"', WORKER)
        self.assertIn('const LIKE_COOKIE_PATH = "/api/stats/like"', WORKER)
        self.assertIn('Secure; HttpOnly; SameSite=Lax', WORKER)
        self.assertIn('Max-Age=', WORKER)
        self.assertIn('LIKE_COOKIE_TTL_SECONDS', WORKER)
        self.assertIn('if (!ttl || !env.RATE_LIMITER || !ip)', WORKER)
        self.assertIn('strictWrite(request)', WORKER)
        self.assertIn('consent_notice_version', WORKER)
        self.assertIn('likeSetCookie("",0)', WORKER)

    def test_desired_state_guard_and_recovery(self):
        self.assertIn('typeof body.liked !== "boolean"', WORKER)
        self.assertIn('ON CONFLICT(page_id,visitor_hash) DO NOTHING', WORKER)
        self.assertIn('INSERT INTO likes(page_id,visitor_hash) SELECT ?,cookie_hash FROM like_cookie_sessions', WORKER)
        self.assertIn('DELETE FROM like_cookie_sessions WHERE cookie_hash=?', WORKER)
        self.assertIn('erasure_unconfirmed', WORKER)

    def test_aggregate_print_does_not_read_personal_id(self):
        snippet = WORKER.split('async function recordAggregatePrint(env, request) {')[1].split('export default {')[0]
        for forbidden in ('visitor_id', 'VISITOR_KEY', 'readLikeCookie', 'cookieLikeSession'):
            self.assertNotIn(forbidden, snippet)
        self.assertIn('["page_id","campaign"]', snippet)
        self.assertIn('rateLimit(env,ip,"aggregate-print")', snippet)
        self.assertIn('strictWrite(request)', snippet)
        self.assertIn('recordAggregatePrint(env,request)', WORKER)
        self.assertIn('cookieLikeRoutes(env,request,path)', WORKER)


if __name__ == "__main__":
    unittest.main()
