"""Source and runtime regressions for fixed Instagram UTM landing attribution (#216)."""
import hashlib
import json
import shutil
import sqlite3
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstagramTrafficTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node required for browser runtime simulation")
    def test_browser_allows_only_external_tagged_landings(self):
        harness = r"""
const fs=require('fs'),vm=require('vm');
const code=fs.readFileSync('js/stats.js','utf8');
function visit(url, referrer='', navType='navigate'){
  const u=new URL(url), calls=[];
  const ctx={
    window:{}, URL, URLSearchParams, location:u, document:{referrer},
    performance:{getEntriesByType:()=>[{type:navType}]},
    fetch:(dest,options)=>{calls.push({dest,body:JSON.parse(options.body)});return Promise.resolve({});},
    navigator:{}, localStorage:{getItem:()=>null,setItem:()=>{}},
    crypto:require('node:crypto').webcrypto, console,
  };
  vm.runInNewContext(code,ctx);
  if(calls.length!==1||calls[0].dest!=='/api/stats/visit')throw Error('visit request missing');
  return JSON.stringify(calls[0].body);
}
for(const kind of ['profile','story','reel']){
  const u='https://ausmalwiese.de/?utm_source=instagram&utm_medium=social&utm_campaign='+kind;
  if(visit(u)!==JSON.stringify({campaign:'instagram-'+kind,stage:'landing'}))
    throw Error('tagged '+kind);
}
const direct='https://ausmalwiese.de/detail.html?id=1234567&utm_source=instagram&utm_medium=social&utm_campaign=story';
if(visit(direct)!==JSON.stringify({campaign:'instagram-story',stage:'landing'}))throw Error('detail');
const valid='https://ausmalwiese.de/?utm_source=instagram&utm_medium=social&utm_campaign=profile';
for(const url of [
  'https://ausmalwiese.de/',
  valid.replace('utm_medium=social','utm_medium=paid'),
  valid.replace('utm_source=instagram','utm_source=facebook'),
  valid.replace('utm_campaign=profile','utm_campaign=unknown'),
  valid+'&utm_source=instagram',
  'https://coloring.rozkalns.net/?utm_source=instagram&utm_medium=social&utm_campaign=profile',
])if(visit(url)!=='{}')throw Error('unallowed '+url);
if(visit(valid,'https://ausmalwiese.de/detail.html')!=='{}')throw Error('internal');
if(visit(valid,'https://www.ausmalwiese.de/detail.html')!=='{}')throw Error('www internal');
if(visit(valid,'','reload')!=='{}')throw Error('reload');
if(visit('https://ausmalwiese.de/?campaign=dortmund-01&utm_source=instagram&utm_medium=social&utm_campaign=profile')!==
   JSON.stringify({campaign:'dortmund-01',stage:'catalog'}))throw Error('Dortmund precedence');
console.log('INSTAGRAM_BROWSER=PASS');
"""
        result = subprocess.run(["node", "-e", harness], cwd=ROOT,
                                text=True, capture_output=True, timeout=20, check=False)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("INSTAGRAM_BROWSER=PASS", result.stdout)

    @unittest.skipUnless(shutil.which("node"), "Node required for Worker simulation")
    def test_worker_allowlists_landing_only_and_rejects_prefetch(self):
        harness = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('cloudflare/stats-worker.js','utf8');
const script=source.replace('export default {','globalThis.worker = {');
const ctx={URL,Response,Headers,TextEncoder,crypto:require('node:crypto').webcrypto,console};
vm.runInNewContext(script,ctx);
if(!vm.runInNewContext("validCampaign('instagram-profile')",ctx))throw Error('profile not allowed');
if(vm.runInNewContext("validCampaign('instagram-test')",ctx))throw Error('arbitrary allowed');
let rows=[];const env={DB:{prepare(sql){return {bind(...args){rows.push({sql,args});return this;},run:async()=>({})}}}};
function statement(campaign,event){return vm.runInNewContext('campaignEventStatement',ctx)(env,campaign,event);}
if(statement('instagram-story','catalog')!==null||statement('instagram-story','print')!==null
    ||statement('instagram-story','detail','1234567')!==null)throw Error('nonlanding');
if(!statement('instagram-story','landing'))throw Error('landing missing');
if(!statement('dortmund-01','catalog'))throw Error('Dortmund broken');
console.log('INSTAGRAM_WORKER=PASS');
"""
        result = subprocess.run(["node", "-e", harness], cwd=ROOT,
                                text=True, capture_output=True, timeout=20, check=False)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("INSTAGRAM_WORKER=PASS", result.stdout)

    def test_daily_aggregate_7_30_windows_keep_dortmund_and_no_identity(self):
        with sqlite3.connect(":memory:") as db:
            schema=(ROOT/"cloudflare/stats-schema.sql").read_text(encoding="utf-8")
            db.executescript(schema)
            self.assertIn("daily_campaign_events", schema)
            self.assertNotIn("referrer_url", schema)
            data=[
                ("instagram-profile","landing","",0,2),
                ("instagram-profile","landing","",6,1),
                ("instagram-story","landing","",8,4),
                ("instagram-reel","landing","",29,5),
                ("instagram-profile","landing","",31,19),
                ("dortmund-01","catalog","",0,7),
            ]
            for campaign,event,page,days,count in data:
                db.execute("""INSERT INTO daily_campaign_events
                              (campaign,event,page_id,day,event_count)
                              VALUES (?,?,?,date('now', ?),?)""",
                           (campaign,event,page,f"-{days} days",count))
            def total(days):
                return db.execute("""SELECT COALESCE(SUM(event_count),0)
                       FROM daily_campaign_events
                       WHERE campaign LIKE 'instagram-%' AND event='landing'
                         AND day >= date('now', ?)""",(f"-{days-1} days",)).fetchone()[0]
            self.assertEqual(total(7),3)
            self.assertEqual(total(30),12)
            self.assertEqual(db.execute("SELECT SUM(event_count) FROM daily_campaign_events WHERE campaign='dortmund-01'").fetchone()[0],7)

    def test_admin_uses_only_readonly_aggregate_api_and_safe_fallback(self):
        html=(ROOT/"traffic.html").read_text(encoding="utf-8")
        js=(ROOT/"js/traffic-admin.js").read_text(encoding="utf-8")
        worker=(ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")
        for key in ("7","30","profile","story","reel"):
            self.assertIn(f"data-instagram-{key}",html)
        self.assertIn("getCampaigns(7).catch",js)
        self.assertIn("getCampaigns(30).catch",js)
        self.assertIn('data?.instagram_attribution_version !== 1',js)
        self.assertIn('week ? formatNumber(week.total) : "–"',js)
        self.assertIn('month ? formatNumber(month.total) : "–"',js)
        self.assertIn("INSTAGRAM_CAMPAIGN_IDS",worker)
        self.assertIn("instagram_attribution_version:1",worker)
        self.assertIn('event !== "landing"',worker)
        self.assertIn("prefetch|prerender",worker)
        self.assertIn("botManagement?.verifiedBot",worker)
        self.assertNotIn('method: "POST"',js)
        self.assertIn('noindex,nofollow,noarchive',html)
        self.assertIn('v=instagram-216',html)
        version = hashlib.sha256((ROOT/"js/stats.js").read_bytes()).hexdigest()[:16]
        for page in ("index.html", "detail.html", "kita.html", "stats.html", "traffic.html"):
            self.assertIn('js/stats.js?v='+version, (ROOT/page).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
