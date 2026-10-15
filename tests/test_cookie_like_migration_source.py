"""Offline-only SQLite gate for the proposed, unapplied Like cookie session schema.

This does not certify the cookie Worker/UI or any LIVE D1 migration.
"""
import hashlib
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "cloudflare/stats-schema.sql").read_text(encoding="utf-8")
MIGRATION = (ROOT / "cloudflare/stats-cookie-like-migration.sql").read_text(encoding="utf-8")
DESIGN = (ROOT / "docs/LIKE_PRINT_COOKIE_REDESIGN_182.md").read_text(encoding="utf-8")


class LikeCookieSchemaDraftTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA)

    def tearDown(self):
        self.db.close()

    def test_additive_migration_preserves_legacy_like_counts(self):
        legacy = hashlib.sha256(b"previous-credential").hexdigest()
        self.db.execute("INSERT INTO likes(page_id, visitor_hash) VALUES (?, ?)", ("1234567", legacy))
        self.db.execute("UPDATE page_stats SET print_count=12 WHERE page_id='1234567'")
        self.db.executescript(MIGRATION)
        self.db.executescript(MIGRATION)  # idempotence before any rollout
        self.assertEqual(
            self.db.execute("SELECT like_count, print_count FROM page_stats WHERE page_id='1234567'").fetchone(),
            (1, 12),
        )
        self.assertEqual(
            self.db.execute("SELECT visitor_hash FROM likes WHERE page_id='1234567'").fetchone()[0],
            legacy,
        )
        self.assertIsNotNone(self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_like_cookie_sessions_expiry'"
        ).fetchone())
        self.assertIsNotNone(self.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='trigger' AND name='likes_after_delete'"
        ).fetchone())

    def test_cookie_digest_metadata_and_constraints(self):
        self.db.executescript(MIGRATION)
        digest = hashlib.sha256(b"browser-secret-random-token").hexdigest()
        self.db.execute(
            "INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,?,?)",
            (digest, 1, 2000000000),
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,?,?)",
                (digest, 1, 2000000001),
            )
        for bad in ("short", "F" * 64, "z" * 64):
            with self.subTest(digest=bad), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(
                    "INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,?,?)",
                    (bad, 1, 2000000000),
                )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,?,?)",
                ("a" * 64, 0, 2000000000),
            )

    def test_draft_does_not_claim_release_or_approved_ttl(self):
        self.assertIn("SOURCE ONLY", DESIGN)
        self.assertIn("not approved", DESIGN.lower())
        self.assertIn("Time Travel", DESIGN)
        self.assertIn("Print", DESIGN)
        self.assertIn("legacy", DESIGN.lower())
        self.assertIn("active-versus-archived", DESIGN)
        self.assertNotIn("DROP TABLE", MIGRATION.upper())
        self.assertNotIn("DELETE FROM", MIGRATION.upper())
        self.assertNotIn("ALTER TABLE", MIGRATION.upper())


if __name__ == "__main__":
    unittest.main()
