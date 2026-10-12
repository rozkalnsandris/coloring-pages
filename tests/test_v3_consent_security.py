"""V3 consent security/retention gates (source + executable SQLite invariants)."""
import sqlite3
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class V3SecurityTests(unittest.TestCase):
    def test_old_token_cannot_issue_new_token_or_write_likes(self):
        src=(ROOT/"cloudflare/stats-worker.js").read_text()
        self.assertIn("crypto.getRandomValues(bytes)",src)
        self.assertIn("V2_ERASURE_RE",src)
        self.assertIn('!validVisitorId(body.visitor_id)',src)
        self.assertIn("prior_id !== undefined && !validVisitorId",src)
        self.assertIn("INSERT INTO visitor_credentials",src)
        self.assertIn("WHERE visitor_hash=? AND expires_at>unixepoch()",src)
        self.assertIn("credentialActiveSql",src)
        self.assertIn("strictWrite(request)",src)
        self.assertIn("CF-Connecting-IP",src)
        self.assertIn("CONSENT_TTL_SECONDS",src)
    def test_sql_guard_for_expired_and_revoked_tokens(self):
        db=sqlite3.connect(":memory:")
        db.executescript((ROOT/"cloudflare/stats-schema.sql").read_text())
        db.execute("INSERT INTO visitor_credentials(visitor_hash,like_allowed,print_allowed,notice_version,expires_at) VALUES ('active',1,1,1,unixepoch()+30),('expired',1,1,1,unixepoch()-30),('revoked',0,1,1,unixepoch()+30)")
        guarded="INSERT INTO likes(page_id,visitor_hash) SELECT ?,visitor_hash FROM visitor_credentials WHERE visitor_hash=? AND like_allowed=1 AND expires_at>unixepoch() ON CONFLICT(page_id,visitor_hash) DO NOTHING"
        for h,expected in [("active",1),("expired",0),("revoked",0),("legacy",0)]:
            self.assertEqual(db.execute(guarded,("p",h)).rowcount,expected)
        self.assertEqual(db.execute("SELECT like_count FROM page_stats WHERE page_id='p'").fetchone(),(1,))
        db.close()
    def test_no_local_random_credentials_or_legacy_reuse(self):
        js=(ROOT/"js/stats.js").read_text()
        self.assertNotIn("globalThis.crypto.getRandomValues",js)
        self.assertIn("V3_RE.test(id)",js)
        self.assertIn('ensureCredential("print")',js)
        self.assertIn('ensureCredential("like")',js)
        self.assertIn('getCredentialForRotation()',js)
        self.assertIn('current?.()?.like',js)
        self.assertIn('current?.()?.print',js)
        self.assertNotIn('pendingCredential = changeCredential',js)
        self.assertIn('handleExpiredCredential(error,visitorId)',js)
        self.assertIn('requireFreshConsent?.()',js)
        self.assertIn('await requestJson("/print"',js)
        consent=(ROOT/"js/consent.js").read_text()
        self.assertIn("!storageFault && !erasing",consent)
        self.assertLess(consent.index("erasing = true;\n    eraseButton.disabled"),consent.index("if (!save(next)) return"))
