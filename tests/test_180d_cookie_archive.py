"""Offline SQLite regression for 180-day browser Like and page-level archive.

Uses source Worker SQL, not mocked substitute SQL. No LIVE database/Worker access.
"""
import hashlib
import re
import sqlite3
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKER=(ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")
SCHEMA=(ROOT/"cloudflare/stats-schema.sql").read_text(encoding="utf-8")
MIGRATION=(ROOT/"cloudflare/stats-cookie-like-migration.sql").read_text(encoding="utf-8")


def source_sql():
    selector=re.search(r'const EXPIRED_COOKIE_SELECTOR = "([^"]+)";',WORKER)
    assert selector, "source bounded session selector missing"
    sql=[]
    for name in ("ARCHIVE_COOKIE_SQL","DELETE_EXPIRED_COOKIE_LIKES_SQL","DELETE_EXPIRED_COOKIE_SESSIONS_SQL"):
        match=re.search(r"const "+name+r" = `(.*?)`;",WORKER,re.S)
        assert match,name
        sql.append(match.group(1).replace("${EXPIRED_COOKIE_SELECTOR}",selector.group(1)))
    return sql


def h(text):
    return hashlib.sha256(text.encode()).hexdigest()


class CookieArchiveSourceTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.executescript(SCHEMA)
        self.db.executescript(MIGRATION)

    def tearDown(self):
        self.db.close()

    def session(self,name,expired):
        key=h(name)
        self.db.execute("INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,1,unixepoch()+?)",
                        (key,-60 if expired else 86400))
        return key

    def like(self,page,key):
        self.db.execute("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",(page,key))

    def count(self,page):
        row=self.db.execute("""SELECT p.like_count+COALESCE(a.like_count,0) FROM page_stats p
              LEFT JOIN archived_like_totals a ON a.page_id=p.page_id WHERE p.page_id=?""",(page,)).fetchone()
        return row[0] if row else 0

    def archive(self, cutoff=None):
        if cutoff is None:
            cutoff=int(time.time())
        with self.db:
            return [self.db.execute(query,(cutoff,)).rowcount for query in source_sql()]

    def test_new_cookie_issuance_is_retired_but_bounded_archive_remains(self):
        self.assertNotIn("LIKE_COOKIE_TTL_SECONDS",WORKER)
        self.assertNotIn("crypto.getRandomValues",WORKER)
        self.assertIn("RETIRED_COOKIE_PATHS",WORKER)
        self.assertIn("legacy_personalized_api_retired",WORKER)
        self.assertIn("Secure; HttpOnly; SameSite=Lax",WORKER)
        self.assertIn("async scheduled(",WORKER)

    def test_expiry_preserves_counter_but_removes_pseudonymous_vote(self):
        legacy=h("legacy")
        expired=self.session("old",True)
        active=self.session("active",False)
        self.like("1234567",legacy)
        self.like("1234567",expired)
        self.like("1234567",active)
        self.like("2345678",expired)
        self.db.commit()
        self.assertEqual(self.count("1234567"),3)
        self.assertEqual(self.archive(),[2,2,1])
        self.assertEqual(self.count("1234567"),3)
        self.assertEqual(self.count("2345678"),1)
        self.assertEqual(self.db.execute("SELECT like_count FROM archived_like_totals WHERE page_id='1234567'").fetchone(),(1,))
        self.assertEqual(self.db.execute("SELECT visitor_hash FROM likes WHERE page_id='1234567' ORDER BY visitor_hash").fetchall(),
                         [(v,) for v in sorted((legacy,active))])
        self.assertEqual(self.db.execute("SELECT 1 FROM like_cookie_sessions WHERE cookie_hash=?",(expired,)).fetchone(),None)
        self.assertEqual(self.archive(),[0,0,0]) # idempotent; no double counting

    def test_revocation_before_expiry_reduces_only_active_counter(self):
        expired=self.session("old",True)
        active=self.session("current",False)
        self.like("1234567",expired)
        self.like("1234567",active)
        self.db.commit()
        self.archive()
        with self.db:
            self.db.execute("DELETE FROM likes WHERE visitor_hash=?",(active,))
            self.db.execute("DELETE FROM like_cookie_sessions WHERE cookie_hash=?",(active,))
        self.assertEqual(self.count("1234567"),1)
        self.assertEqual(self.db.execute("SELECT like_count FROM archived_like_totals WHERE page_id='1234567'").fetchone(),(1,))

    def test_late_failure_rolls_back_archive_likes_and_session_delete(self):
        expired=self.session("blocked",True)
        self.like("1234567",expired)
        self.db.executescript("""CREATE TRIGGER deny_session_delete BEFORE DELETE ON like_cookie_sessions
        BEGIN SELECT RAISE(ABORT,'simulated rollback'); END;""")
        self.db.commit()
        with self.assertRaises(sqlite3.DatabaseError):
            self.archive()
        self.assertEqual(self.count("1234567"),1)
        self.assertEqual(self.db.execute("SELECT count(*) FROM archived_like_totals").fetchone()[0],0)
        self.assertIsNotNone(self.db.execute("SELECT 1 FROM likes WHERE visitor_hash=?",(expired,)).fetchone())
        self.assertIsNotNone(self.db.execute("SELECT 1 FROM like_cookie_sessions WHERE cookie_hash=?",(expired,)).fetchone())

    def test_many_expired_sessions_are_bounded_to_100_per_batch(self):
        for i in range(105):
            key=self.session("expired-"+str(i),True)
            self.like("1234567",key)
        self.db.commit()
        self.assertEqual(self.archive()[2],100)
        self.assertEqual(self.count("1234567"),105)
        self.assertEqual(self.archive()[2],5)
        self.assertEqual(self.archive(),[0,0,0])
        self.assertEqual(self.count("1234567"),105)

    def test_time_travel_restore_resurrects_pseudonymous_rows(self):
        """An old database snapshot can reintroduce erased Like records."""
        expired=self.session("snapshot",True)
        self.like("1234567",expired)
        self.db.commit()
        snapshot=sqlite3.connect(":memory:")
        try:
            self.db.backup(snapshot)
            self.assertEqual(self.archive(),[1,1,1])
            self.assertEqual(self.count("1234567"),1)
            self.assertEqual(self.db.execute("SELECT COUNT(*) FROM likes").fetchone()[0],0)
            snapshot.backup(self.db)
            self.assertEqual(self.count("1234567"),1)
            self.assertIsNotNone(self.db.execute(
                "SELECT 1 FROM likes WHERE visitor_hash=?",(expired,)
            ).fetchone())
            self.assertEqual(self.archive(),[1,1,1])
            self.assertEqual(self.count("1234567"),1)
            self.assertEqual(self.archive(),[0,0,0])
        finally:
            snapshot.close()

    def test_legacy_not_migrated_and_archive_has_no_identifiers(self):
        self.assertIn("archived_like_totals",MIGRATION)
        archive_schema=MIGRATION.split("CREATE TABLE IF NOT EXISTS archived_like_totals",1)[1]
        for field in ("visitor_hash","cookie_hash","consent_recorded_at","created_at"):
            self.assertNotIn(field,archive_schema)
        self.assertIn("D1.batch",WORKER) if "D1.batch" in WORKER else self.assertIn("env.DB.batch",WORKER)


if __name__=="__main__":
    unittest.main()
