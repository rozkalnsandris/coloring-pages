"""Regression tests for minimal one-statement D1 Like erasure and known replay limit."""
import hashlib
import json
import shutil
import sqlite3
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER_HARNESS = r"""
const vm = require('node:vm');
const fs = require('node:fs');
const {webcrypto,createHash} = require('node:crypto');
const f = JSON.parse(process.argv[1]);
const id = 'v2-'+'a'.repeat(64);
const hash = createHash('sha256').update(id).digest('hex');
const other = createHash('sha256').update('v2-'+'b'.repeat(64)).digest('hex');
let rows = [hash,hash,other], writes=0, limits=0;
const db = {
 prepare(sql) {
   if(sql !== 'DELETE FROM likes WHERE visitor_hash = ?') throw Error('unexpected SQL');
   return {bind(value){return {async run(){
     writes++;
     if(f.dbError)throw Error('D1 unavailable');
     if(f.dbFailure)return {success:false};
     rows=rows.filter(x=>x!==value);
     return {success:true,meta:{changes:2}};
   }}}};
 }
};
const context={URL,Request,Response,TextEncoder,crypto:webcrypto};
vm.runInNewContext(fs.readFileSync('cloudflare/stats-worker.js','utf8')
  .replace('export default {','globalThis.testWorker = {'),context);
const target=f.target||'https://coloring.rozkalns.net';
const headers={
  origin:f.origin??'https://coloring.rozkalns.net',
  'sec-fetch-site':f.site??'same-origin',
  'content-type':f.contentType??'application/json'
};
const req = new Request(target+'/api/stats/erase-likes',{
  method:'POST',headers,body:f.rawBody??JSON.stringify({visitor_id:f.id??id})
});
const env={DB:db,RATE_LIMITER:{limit:async()=>{limits++;return {success:!f.limited}}}};
context.testWorker.fetch(req,env).then(async res=>{
 console.log(JSON.stringify({status:res.status,body:await res.json(),writes,limits,rows}));
}).catch(()=>console.log(JSON.stringify({status:500,writes,limits,rows})));
"""

class MinimalErasureTests(unittest.TestCase):
    def run_worker(self, **fixture):
        if not shutil.which("node"):
            self.skipTest("node required")
        p=subprocess.run(["node","-e",WORKER_HARNESS,json.dumps(fixture)],
            cwd=ROOT,capture_output=True,text=True,check=True)
        return json.loads(p.stdout)

    def test_deletes_only_this_credential_without_extra_tables(self):
        out=self.run_worker()
        self.assertEqual(out["status"],200)
        self.assertEqual(out["body"],{"ok":True})
        self.assertEqual(out["writes"],1)
        self.assertEqual(len(out["rows"]),1)

    def test_invalid_credential_and_cross_origin_do_not_write(self):
        for f in ({"id":"v-legacy"}, {"id":"example"}, {"origin":"https://evil.example"},
                  {"site":"cross-site"}, {"site":"same-site"},
                  {"rawBody":'{"visitor_id":"v2-abc","other":true}'},
                  {"contentType":"text/plain"}, {"limited":True}):
            with self.subTest(f=f):
                x=self.run_worker(**f)
                self.assertNotEqual(x["status"],200)
                self.assertEqual(x["writes"],0)
                self.assertEqual(len(x["rows"]),3)

    def test_each_exact_public_host_only_accepts_matching_origin(self):
        hosts=("https://coloring.rozkalns.net","https://ausmalwiese.de","https://www.ausmalwiese.de")
        for host in hosts:
            with self.subTest(host=host):
                x=self.run_worker(target=host,origin=host)
                self.assertEqual(x["status"],200)
                for other in hosts:
                    if other!=host:
                        x=self.run_worker(target=host,origin=other)
                        self.assertEqual(x["status"],403)
                        self.assertEqual(x["writes"],0)
        for host in ("http://ausmalwiese.de","https://preview.ausmalwiese.de"):
            with self.subTest(host=host):
                x=self.run_worker(target=host,origin=host)
                self.assertEqual(x["status"],403)
                self.assertEqual(x["writes"],0)

    def test_failed_or_uncertain_write_cannot_acknowledge_erasure(self):
        for f in ({"dbError":True},{"dbFailure":True}):
            with self.subTest(f=f):
                x=self.run_worker(**f)
                self.assertNotEqual(x.get("body"),{"ok":True})
                self.assertEqual(x["writes"],1)

    def test_d1_like_counters_remain_consistent_without_suppression_table(self):
        schema=(ROOT/"cloudflare/stats-schema.sql").read_text(encoding="utf-8")
        self.assertNotIn("like_erasure_blocks",schema)
        with sqlite3.connect(":memory:") as db:
            db.executescript(schema)
            h=hashlib.sha256(b"v2-a").hexdigest()
            other=hashlib.sha256(b"v2-b").hexdigest()
            db.executemany("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",
                [("p1",h),("p2",h),("p1",other)])
            db.execute("UPDATE page_stats SET print_count=7 WHERE page_id='p1'")
            db.execute("DELETE FROM likes WHERE visitor_hash=?",(h,))
            self.assertEqual(db.execute("SELECT like_count,print_count FROM page_stats WHERE page_id='p1'").fetchone(),(1,7))
            self.assertEqual(db.execute("SELECT like_count FROM page_stats WHERE page_id='p2'").fetchone(),(0,))
            # Accepted residual risk: a still-valid old credential can re-insert a Like.
            db.execute("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",( "p1",h))
            self.assertEqual(db.execute("SELECT like_count FROM page_stats WHERE page_id='p1'").fetchone(),(2,))

    def test_worker_source_has_no_guard_table_or_persistent_recovery_key(self):
        worker=(ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")
        consent=(ROOT/"js/consent.js").read_text(encoding="utf-8")
        stats=(ROOT/"js/stats.js").read_text(encoding="utf-8")
        self.assertIn('POST" && path==="/api/stats/erase-likes"',worker)
        self.assertIn('DELETE FROM likes WHERE visitor_hash = ?',worker)
        self.assertNotIn("like_erasure_blocks",worker)
        self.assertNotIn("blocked_until",worker)
        self.assertNotIn("coloring-pages-erasure-pending-v1",consent)
        self.assertNotIn("retryPendingErasure",consent)
        self.assertIn("read()?.[purpose] === true",consent)
        self.assertIn("await eraseProof(proof);",consent)
        self.assertIn("window.ColoringStats?.getErasureProof?.()",consent)
        self.assertIn("globalThis.crypto.getRandomValues",stats)
        self.assertNotIn("Math.random()",stats)
        self.assertIn('if (visitorId) return requestJson("/page"',stats)
        self.assertNotIn('query.set("visitor_id"',stats)
