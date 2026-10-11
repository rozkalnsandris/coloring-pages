"""Shared printed QR visits: aggregate, host-locked, source-only activation."""
import hashlib
import sqlite3
import json
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PrintQrStatsTests(unittest.TestCase):
    def test_static_shared_qr_activated_after_route_and_physical_scan(self):
        svg = ET.fromstring((ROOT / "assets/ausmalwiese-qr-dots.svg").read_text())
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertIn("https://ausmalwiese.de/q", svg.findtext("s:title", namespaces=ns))
        self.assertEqual((svg.get("width"), svg.get("height")), ("20mm", "20mm"))
        self.assertEqual(svg.get("viewBox"), "0 0 37 37")
        js = (ROOT / "js/print.js").read_text()
        self.assertIn("PRINT_QR_ROUTE_VERIFIED = true", js)
        asset = (ROOT / "assets/ausmalwiese-qr-dots.svg").read_bytes()
        version = hashlib.sha256(asset).hexdigest()[:16]
        self.assertIn(
            f'const PRINT_QR_ASSET = "assets/ausmalwiese-qr-dots.svg?v={version}"', js
        )
        self.assertIn("buildPrintBrandFooter(qrReady)", js)
        self.assertNotIn("ausmalwiese-qr-dots", (ROOT / "tools/coloring-pages-import").read_text())
        self.assertNotIn("assets/ausmalwiese-qr-dots.svg", (ROOT / "js/detail.js").read_text())

    def test_aggregate_schema_and_increments(self):
        with sqlite3.connect(":memory:") as db:
            db.executescript((ROOT / "cloudflare/stats-schema.sql").read_text())
            sql = """INSERT INTO daily_print_qr_scans (day, scan_count)
                     VALUES (date('now'), 1)
                     ON CONFLICT(day) DO UPDATE SET scan_count=scan_count+1"""
            for _ in range(4):
                db.execute(sql)
            self.assertEqual(db.execute("SELECT SUM(scan_count) FROM daily_print_qr_scans").fetchone()[0], 4)
            self.assertEqual([x[1] for x in db.execute("PRAGMA table_info(daily_print_qr_scans)")],
                             ["day", "scan_count"])
        worker = (ROOT / "cloudflare/stats-worker.js").read_text()
        self.assertIn("FROM daily_print_qr_scans", worker)
        self.assertIn("qr_scan_count", worker)
        self.assertIn("recent_qr_scans", worker)
        self.assertIn('url.hostname === PRINT_QR_HOST', worker)

    @unittest.skipUnless(shutil.which("node"), "Node required for Worker runtime simulation")
    def test_q_redirect_counts_only_eligible_get_requests(self):
        harness = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('cloudflare/stats-worker.js','utf8').replace('export default {','globalThis.worker = {');
let writes=0;
const env={DB:{prepare(sql){
  if(!sql.includes('daily_print_qr_scans'))throw Error('unexpected SQL');
  return {run: async()=>{writes+=1;return {success:true}}};
}}};
class Response {
 constructor(body,opts={}){this.status=opts.status||200;this.headers=opts.headers||{};}
}
const context={Response,URL,TextEncoder,console,crypto:require('node:crypto').webcrypto};
vm.runInNewContext(source,context);
const req=(url,method='GET',headers={},cf={})=>({
 url,method,cf,
 headers:{get:(k)=>headers[k]||null}
});
async function check(){
  let r=await context.worker.fetch(req('https://ausmalwiese.de/q'),env);
  if(r.status!==302||r.headers.location!=='https://coloring.rozkalns.net/'||writes!==1)throw Error('valid GET');
  if(!String(r.headers['cache-control']).includes('no-store'))throw Error('cache');
  if(r.headers['referrer-policy']!=='no-referrer')throw Error('referrer');
  r=await context.worker.fetch(req('https://ausmalwiese.de/q','HEAD'),env);
  if(r.status!==302||writes!==1)throw Error('HEAD counted');
  r=await context.worker.fetch(req('https://ausmalwiese.de/q','GET',{'sec-purpose':'prefetch'}),env);
  if(r.status!==302||writes!==1)throw Error('prefetch counted');
  r=await context.worker.fetch(req('https://ausmalwiese.de/q','GET',{}, {botManagement:{verifiedBot:true}}),env);
  if(r.status!==302||writes!==1)throw Error('verified bot counted');
  r=await context.worker.fetch(req('https://ausmalwiese.de/q','POST'),env);
  if(r.status!==405||writes!==1)throw Error('method');
  r=await context.worker.fetch(req('https://coloring.rozkalns.net/q'),env);
  if(r.status!==404||writes!==1)throw Error('hostname confusion');
  r=await context.worker.fetch(req('https://ausmalwiese.de/q?next=https://evil.example/'),env);
  if(r.headers.location!=='https://coloring.rozkalns.net/'||writes!==2)throw Error('open redirect');
  env.DB.prepare=()=>({run:async()=>{throw Error('D1 unavailable')}});
  r=await context.worker.fetch(req('https://ausmalwiese.de/q'),env);
  if(r.status!==302)throw Error('failure blocked visitor');
  console.log('QR_REDIRECT_SIMULATION=PASS');
}
check().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(["node", "-e", harness], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("QR_REDIRECT_SIMULATION=PASS", result.stdout)

    def test_admin_counts_are_optional_until_worker_activation(self):
        admin = (ROOT / "js/stats-admin.js").read_text()
        html = (ROOT / "stats.html").read_text()
        self.assertIn('overview.totals?.qr_scan_count === "number"', admin)
        self.assertIn('overview.totals?.recent_qr_scans === "number"', admin)
        self.assertIn("data-stats-qr-total", html)
        self.assertIn("data-stats-qr-recent", html)
        self.assertIn("QR link visits", html)
        self.assertIn("noindex,nofollow,noarchive", html)


if __name__ == "__main__":
    unittest.main()
