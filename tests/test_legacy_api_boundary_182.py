"""Offline fixed-cutoff archival and user-directed legacy erasure regression."""
import hashlib
import json
import shutil
import sqlite3
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKER=(ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")
SCHEMA=(ROOT/"cloudflare/stats-schema.sql").read_text(encoding="utf-8")
MIGRATION=(ROOT/"cloudflare/stats-cookie-like-migration.sql").read_text(encoding="utf-8")


class CookieArchiveBoundaryAndLegacyTests(unittest.TestCase):
    def test_source_binds_identical_cutoff_and_retires_legacy_writes(self):
        chunk=WORKER.split("async function archiveExpiredCookieLikes(env) {",1)[1].split("export default {",1)[0]
        self.assertIn("const cutoff = Math.floor(Date.now()/1000);",chunk)
        self.assertIn("expires_at<=?1",WORKER)
        self.assertNotIn("expires_at<=unixepoch() ORDER BY",WORKER)
        for key in ("ARCHIVE_COOKIE_SQL","DELETE_EXPIRED_COOKIE_LIKES_SQL","DELETE_EXPIRED_COOKIE_SESSIONS_SQL"):
            self.assertIn("env.DB.prepare("+key+").bind(cutoff)",chunk)
        for endpoint in ("/api/stats/page","/api/stats/print","/api/stats/like","/api/stats/credential"):
            self.assertIn('path==="'+endpoint+'"',WORKER)
        self.assertIn("legacy_personalized_api_retired",WORKER)
        self.assertIn('path==="/api/stats/erase-legacy-v3"',WORKER)
        self.assertIn("no_matching_active_records",WORKER)

    def test_expiry_second_never_archives_or_deletes_a_later_cookie(self):
        from test_180d_cookie_archive import source_sql
        db=sqlite3.connect(":memory:")
        try:
            db.executescript(SCHEMA)
            db.executescript(MIGRATION)
            cutoff=2000000000
            early=hashlib.sha256(b"early").hexdigest()
            later=hashlib.sha256(b"later").hexdigest()
            db.executemany(
                "INSERT INTO like_cookie_sessions(cookie_hash,consent_notice_version,expires_at) VALUES (?,1,?)",
                [(early,cutoff),(later,cutoff+1)])
            db.executemany("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",
                           [("1234567",early),("1234567",later)])
            with db:
                changed=[db.execute(query,(cutoff,)).rowcount for query in source_sql()]
            self.assertEqual(changed,[1,1,1])
            self.assertEqual(db.execute("SELECT like_count FROM page_stats WHERE page_id='1234567'").fetchone(),(1,))
            self.assertEqual(db.execute("SELECT like_count FROM archived_like_totals WHERE page_id='1234567'").fetchone(),(1,))
            self.assertEqual(db.execute("SELECT visitor_hash FROM likes").fetchall(),[(later,)])
            self.assertEqual(db.execute("SELECT cookie_hash FROM like_cookie_sessions").fetchall(),[(later,)])
            with db:
                replay=[db.execute(query,(cutoff,)).rowcount for query in source_sql()]
            self.assertEqual(replay,[0,0,0])
        finally:
            db.close()

    def test_only_one_user_directed_legacy_deletion_v2_or_v3(self):
        if not shutil.which("node"):
            self.skipTest("node unavailable")
        script=r"""
const fs=require('fs'), vm=require('vm'),kind=process.argv[1],id=kind+'-'+'a'.repeat(64);
const calls=[],store=new Map([['coloring-pages-visitor-v1',id]]);
const context={
  URL,URLSearchParams,Blob,location:{pathname:'/privacy-test',search:''},
  navigator:{sendBeacon:()=>false},document:{dispatchEvent(){}},
  localStorage:{getItem(k){return store.get(k)||null},removeItem(k){store.delete(k)}},
  window:{ColoringConsent:{allows(){return false},syncFromServer(){}}},
  fetch:async(path,opts={})=>{
    calls.push({path,body:JSON.parse(opts.body||'{}')});
    return {ok:true,status:200,async json(){return {ok:true,matched:true}}};
  }
};
vm.runInNewContext(fs.readFileSync('js/stats-cookie.js','utf8'),context);
(async()=>{
 await context.window.ColoringStats.eraseLegacyLikes();
 let secondRejected=false;
 try{await context.window.ColoringStats.eraseLegacyLikes()}catch{secondRejected=true}
 console.log(JSON.stringify({calls,stored:[...store],secondRejected}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""
        for kind,url in (("v2","/api/stats/erase-likes"),("v3","/api/stats/erase-legacy-v3")):
            with self.subTest(kind=kind):
                proc=subprocess.run(["node","-e",script,kind],cwd=ROOT,
                                    text=True,capture_output=True,check=True)
                state=json.loads(proc.stdout)
                self.assertEqual(state["calls"],[{"path":url,"body":{"visitor_id":kind+"-"+"a"*64}}])
                self.assertEqual(state["stored"],[])
                self.assertTrue(state["secondRejected"])


if __name__=="__main__":
    unittest.main()
