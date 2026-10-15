"""Source-only SQLite lock/interleaving tests for Like expiry, not a real D1 load test."""
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT/"cloudflare/stats-schema.sql").read_text(encoding="utf-8")
MIGRATION = (ROOT/"cloudflare/stats-cookie-like-migration.sql").read_text(encoding="utf-8")


def digest(label):
    return hashlib.sha256(label.encode()).hexdigest()


def archived(conn, page):
    result=conn.execute(
        "SELECT COALESCE(p.like_count,0)+COALESCE(a.like_count,0) FROM page_stats p "
        "LEFT JOIN archived_like_totals a ON a.page_id=p.page_id WHERE p.page_id=?",
        (page,)
    ).fetchone()
    return result[0] if result else 0


class ArchiveInterleavings(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.name=str(Path(self.tmp.name)/"likes.sqlite")
        self.a=sqlite3.connect(self.name,timeout=0,isolation_level=None)
        self.b=sqlite3.connect(self.name,timeout=0,isolation_level=None)
        self.a.executescript(SCHEMA)
        self.a.executescript(MIGRATION)
        self.cutoff=2000000000
        self.expired=digest("expired")
        self.active=digest("active")
        self.a.execute("INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,1,?)",
                       (self.expired,self.cutoff))
        self.a.execute("INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,1,?)",
                       (self.active,self.cutoff+3600))
        self.a.execute("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",("1234567",self.expired))
        self.a.execute("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",("1234567",self.active))

    def tearDown(self):
        self.a.close()
        self.b.close()
        self.tmp.cleanup()

    def archive(self,db):
        from test_180d_cookie_archive import source_sql
        return [db.execute(sql,(self.cutoff,)).rowcount for sql in source_sql()]

    def test_two_archive_transactions_serialize_and_never_double_count(self):
        self.a.execute("BEGIN IMMEDIATE")
        self.assertEqual(self.archive(self.a),[1,1,1])
        with self.assertRaises(sqlite3.OperationalError):
            self.b.execute("BEGIN IMMEDIATE")
        self.a.execute("COMMIT")
        self.b.execute("BEGIN IMMEDIATE")
        self.assertEqual(self.archive(self.b),[0,0,0])
        self.b.execute("COMMIT")
        self.assertEqual(archived(self.a,"1234567"),2)
        self.assertEqual(self.a.execute("SELECT like_count FROM archived_like_totals").fetchone(),(1,))

    def test_withdrawal_before_archive_excludes_vote(self):
        self.a.execute("BEGIN IMMEDIATE")
        deleted=self.a.execute("DELETE FROM likes WHERE visitor_hash=?",(self.expired,)).rowcount
        removed=self.a.execute("DELETE FROM like_cookie_sessions WHERE cookie_hash=?",(self.expired,)).rowcount
        self.assertEqual((deleted,removed),(1,1))
        self.a.execute("COMMIT")
        self.assertEqual(self.archive(self.b),[0,0,0])
        self.assertEqual(archived(self.a,"1234567"),1)
        self.assertIsNone(self.a.execute("SELECT 1 FROM archived_like_totals").fetchone())

    def test_archive_before_withdrawal_cannot_mutate_irreversible_total(self):
        self.assertEqual(self.archive(self.a),[1,1,1])
        self.assertEqual(self.b.execute("DELETE FROM likes WHERE visitor_hash=?",(self.expired,)).rowcount,0)
        self.assertEqual(self.b.execute("DELETE FROM like_cookie_sessions WHERE cookie_hash=?",(self.expired,)).rowcount,0)
        self.assertEqual(archived(self.a,"1234567"),2)

    def test_inflight_like_is_rejected_after_archive_deletes_session(self):
        self.assertEqual(self.archive(self.a),[1,1,1])
        change=self.b.execute(
            "INSERT INTO likes(page_id,visitor_hash) SELECT ?,cookie_hash FROM like_cookie_sessions "
            "WHERE cookie_hash=? AND expires_at>? ON CONFLICT(page_id,visitor_hash) DO NOTHING",
            ("7654321",self.expired,self.cutoff)
        ).rowcount
        self.assertEqual(change,0)
        self.assertEqual(archived(self.a,"1234567"),2)
        self.assertIsNone(self.b.execute(
            "SELECT 1 FROM likes WHERE visitor_hash=?",(self.expired,)
        ).fetchone())

    def test_stale_like_cannot_race_with_open_write_transaction(self):
        self.a.execute("BEGIN IMMEDIATE")
        self.assertEqual(self.archive(self.a),[1,1,1])
        with self.assertRaises(sqlite3.OperationalError):
            self.b.execute(
                "INSERT INTO likes(page_id,visitor_hash) SELECT ?,cookie_hash FROM like_cookie_sessions "
                "WHERE cookie_hash=? AND expires_at>? ON CONFLICT(page_id,visitor_hash) DO NOTHING",
                ("7654321",self.expired,self.cutoff)
            )
        self.a.execute("COMMIT")
        self.assertEqual(self.b.execute(
            "INSERT INTO likes(page_id,visitor_hash) SELECT ?,cookie_hash FROM like_cookie_sessions "
            "WHERE cookie_hash=? AND expires_at>? ON CONFLICT(page_id,visitor_hash) DO NOTHING",
            ("7654321",self.expired,self.cutoff)
        ).rowcount,0)
        self.assertEqual(archived(self.a,"1234567"),2)


if __name__=="__main__":
    unittest.main()
