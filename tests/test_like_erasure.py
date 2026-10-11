"""Offline security and SQLite contract tests for draft erase-likes flow."""
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
const {webcrypto, createHash} = require('node:crypto');
const fixture = JSON.parse(process.argv[1]);
const id = 'v2-' + 'a'.repeat(64);
const victimHash = createHash('sha256').update(id).digest('hex');
const otherHash = createHash('sha256').update('v2-' + 'b'.repeat(64)).digest('hex');
let hashes = [victimHash, victimHash, otherHash];
let writes = 0, limits = 0;
const db = {
  prepare(sql) {
    if (sql !== 'DELETE FROM likes WHERE visitor_hash = ?') throw Error('unscoped SQL');
    return {bind(hash) {
      return {async run() {
        writes++;
        if (fixture.dbError) throw Error('D1 unavailable');
        if (fixture.dbFailure) return {success:false};
        hashes = hashes.filter(x => x !== hash);
        return {success:true,meta:{changes:2}};
      }};
    }};
  },
};
const ctx = {URL, Response, Request, TextEncoder, crypto:webcrypto};
const source = fs.readFileSync('cloudflare/stats-worker.js','utf8')
  .replace('export default {', 'globalThis.testWorker = {');
vm.runInNewContext(source,ctx);
const headers = {'origin':fixture.origin ?? 'https://coloring.rozkalns.net',
 'sec-fetch-site':fixture.site ?? 'same-origin',
 'content-type':fixture.contentType ?? 'application/json'};
const body = fixture.rawBody ?? JSON.stringify({visitor_id: fixture.id ?? id});
const request = new Request('https://coloring.rozkalns.net/api/stats/erase-likes',{
 method: fixture.method ?? 'POST',headers,
 ...(fixture.method === 'GET' ? {} : {body}),
});
const env = {PUBLIC_ORIGIN:'https://coloring.rozkalns.net',DB:db,
 RATE_LIMITER:{limit:async ()=>{limits++;return {success:!fixture.limited}}}};
ctx.testWorker.fetch(request,env).then(async res => {
 const text=await res.text(); const data=JSON.parse(text);
 console.log(JSON.stringify({status:res.status,data,writes,limits,hashes}));
}).catch(e => console.log(JSON.stringify({error:true,writes,hashes})));
"""

class LikeErasureTests(unittest.TestCase):
    def run_worker(self, **fixture):
        if not shutil.which("node"):
            self.skipTest("node required")
        completed = subprocess.run(["node", "-e", WORKER_HARNESS,
            json.dumps(fixture)], cwd=ROOT, capture_output=True, text=True,
            check=True)
        return json.loads(completed.stdout.strip())

    def test_success_is_scoped_and_no_other_user_is_deleted(self):
        result = self.run_worker()
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["data"], {"ok": True})
        self.assertEqual(result["writes"], 1)
        self.assertEqual(len(result["hashes"]), 1)

    def test_weak_legacy_or_wrong_origin_cannot_delete(self):
        for payload in ({"id": "v-weak-123456"}, {"id": "example"},
            {"origin":"https://evil.example"}, {"site":"cross-site"},
            {"rawBody":'{"visitor_id":"v2-abc","other":true}'},
            {"contentType":"text/plain"}, {"limited":True}):
            with self.subTest(payload=payload):
                out=self.run_worker(**payload)
                self.assertNotEqual(out.get("status"), 200)
                self.assertEqual(out["writes"], 0)
                self.assertEqual(len(out["hashes"]), 3)

    def test_failed_or_ambiguous_d1_cannot_acknowledge_erasure(self):
        for test in ({"dbError": True}, {"dbFailure": True}):
            with self.subTest(test=test):
                out=self.run_worker(**test)
                self.assertNotEqual(out.get("data"), {"ok": True})

    def test_schema_triggers_are_consistent_and_prints_untouched(self):
        schema=(ROOT/"cloudflare/stats-schema.sql").read_text(encoding="utf-8")
        with sqlite3.connect(":memory:") as db:
            db.executescript(schema)
            user=hashlib.sha256(b"v2-user").hexdigest()
            other=hashlib.sha256(b"v2-other").hexdigest()
            db.executemany("INSERT INTO likes(page_id,visitor_hash) VALUES (?,?)",
                [("p1",user),("p2",user),("p1",other)])
            db.execute("UPDATE page_stats SET print_count=7 WHERE page_id='p1'")
            db.execute("DELETE FROM likes WHERE visitor_hash = ?", (user,))
            self.assertEqual(db.execute(
                "SELECT like_count,print_count FROM page_stats WHERE page_id='p1'").fetchone(),(1,7))
            self.assertEqual(db.execute(
                "SELECT like_count FROM page_stats WHERE page_id='p2'").fetchone(),(0,))
            db.execute("DELETE FROM likes WHERE visitor_hash = ?", (user,))
            self.assertEqual(db.execute(
                "SELECT like_count FROM page_stats WHERE page_id='p1'").fetchone(),(1,))

    def test_source_uses_post_only_and_secure_new_tokens(self):
        worker=(ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")
        stats=(ROOT/"js/stats.js").read_text(encoding="utf-8")
        consent=(ROOT/"js/consent.js").read_text(encoding="utf-8")
        self.assertIn('POST" && path==="/api/stats/erase-likes"',worker)
        self.assertIn('DELETE FROM likes WHERE visitor_hash = ?',worker)
        self.assertIn('request.headers.get("origin")',worker)
        self.assertIn('sec-fetch-site',worker)
        self.assertIn('globalThis.crypto.getRandomValues',stats)
        self.assertNotIn('Math.random()',stats)
        self.assertIn('if (visitorId) return requestJson("/page"',stats)
        self.assertNotIn('query.set("visitor_id"',stats)
        self.assertIn('window.ColoringStats?.getErasureProof?.()',consent)
        self.assertIn('window.confirm(',consent)
        self.assertIn('Einwilligung widerrufen; Löschung nicht bestätigt',consent)
