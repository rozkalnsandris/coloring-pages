"""SQLite transactional regressions for v3 revocation and replay fencing."""
import hashlib
import sqlite3
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def h(s): return hashlib.sha256(s.encode()).hexdigest()
class V3ErasureTests(unittest.TestCase):
    def test_revoke_cannot_recreate_like_and_keeps_print_intents(self):
        schema=(ROOT/"cloudflare/stats-schema.sql").read_text()
        with sqlite3.connect(":memory:") as db:
            db.executescript(schema)
            old,new,other=h("v3-old"),h("v3-new"),h("other")
            for token,like,print_ in [(old,1,1),(other,1,0)]:
                db.execute("INSERT INTO visitor_credentials(visitor_hash,like_allowed,print_allowed,notice_version,expires_at) VALUES (?,?,?,?,unixepoch()+86400)",(token,like,print_,1))
            db.executemany("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",[("p1",old),("p2",old),("p1",other)])
            db.execute("UPDATE page_stats SET print_count=7 WHERE page_id='p1'")
            db.execute("BEGIN")
            db.execute("INSERT INTO visitor_credentials(visitor_hash,like_allowed,print_allowed,notice_version,expires_at) SELECT ?,0,1,1,unixepoch()+86400 FROM visitor_credentials WHERE visitor_hash=? AND expires_at>unixepoch()",(new,old))
            db.execute("DELETE FROM likes WHERE visitor_hash=? AND EXISTS(SELECT 1 FROM visitor_credentials WHERE visitor_hash=?)",(old,new))
            db.execute("DELETE FROM visitor_credentials WHERE visitor_hash=? AND EXISTS(SELECT 1 FROM visitor_credentials WHERE visitor_hash=?)",(old,new))
            db.commit()
            guarded="INSERT INTO likes(page_id,visitor_hash) SELECT ?,visitor_hash FROM visitor_credentials WHERE visitor_hash=? AND like_allowed=1 AND expires_at>unixepoch() ON CONFLICT(page_id,visitor_hash) DO NOTHING"
            self.assertEqual(db.execute(guarded,("p1",old)).rowcount,0)
            self.assertEqual(db.execute(guarded,("p1",new)).rowcount,0)
            self.assertEqual(db.execute(guarded,("p1",other)).rowcount,0)  # already liked
            self.assertEqual(db.execute("SELECT like_count,print_count FROM page_stats WHERE page_id='p1'").fetchone(),(1,7))
            self.assertEqual(db.execute("SELECT like_count FROM page_stats WHERE page_id='p2'").fetchone(),(0,))
            self.assertEqual(db.execute("SELECT print_allowed,like_allowed FROM visitor_credentials WHERE visitor_hash=?",(new,)).fetchone(),(1,0))
    def test_legacy_id_cannot_write_and_erasure_stays_available(self):
        source=(ROOT/"cloudflare/stats-worker.js").read_text()
        self.assertIn("V2_ERASURE_RE.test(value)",source)
        self.assertIn('DELETE FROM likes WHERE visitor_hash = ?',source)
        self.assertIn('legacy_credential_forbidden',source)
        self.assertIn('SELECT ?,visitor_hash FROM visitor_credentials',source)
        self.assertIn('print_allowed=1 AND expires_at>unixepoch()',source)
        self.assertIn('path==="/api/stats/credential"',source)
        self.assertNotIn("like_erasure_blocks",source)
    def test_schema_migration_and_source_are_same(self):
        schema=(ROOT/"cloudflare/stats-schema.sql").read_text()
        migration=(ROOT/"cloudflare/stats-v3-migration.sql").read_text()
        self.assertIn(migration[migration.index("CREATE TABLE"):].strip(),schema)
