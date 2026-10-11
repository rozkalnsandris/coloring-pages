"""Source-integration contract: old browser GET and new browser POST coexist."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = r"""
const fs = require("node:fs");
const vm = require("node:vm");
const {webcrypto, createHash} = require("node:crypto");
const id = "v2-" + "a".repeat(64);
const legacy = "legacy-browser-12345";
const victimHash = createHash("sha256").update(id).digest("hex");
const legacyHash = createHash("sha256").update(legacy).digest("hex");
const db = {prepare(sql) { return {bind(...args) {
  return {first:async()=>{
    if(sql.includes("SELECT print_count, like_count")) return {like_count:3, print_count:5};
    if(sql.includes("SELECT 1 AS liked")) return args[1] === victimHash || args[1] === legacyHash ? {liked:1} : null;
    throw Error("unexpected DB read");
  }};
}}}};
const source = fs.readFileSync("cloudflare/stats-worker.js","utf8")
  .replace("export default {", "globalThis.testWorker = {");
const context = {URL, Request, Response, TextEncoder, crypto:webcrypto};
vm.runInNewContext(source, context);
async function run(url,init) {
  const response = await context.testWorker.fetch(new Request(url,init),{DB:db,PUBLIC_ORIGIN:"https://coloring.rozkalns.net"});
  return {status:response.status,headers:Object.fromEntries(response.headers),body:await response.json()};
}
(async()=>{
 const old = await run("https://coloring.rozkalns.net/api/stats/page?page_id=p1&visitor_id="+legacy);
 const anon = await run("https://coloring.rozkalns.net/api/stats/page?page_id=p1");
 const posted = await run("https://coloring.rozkalns.net/api/stats/page",{
   method:"POST",headers:{"origin":"https://coloring.rozkalns.net","sec-fetch-site":"same-origin","content-type":"application/json"},
   body:JSON.stringify({page_id:"p1",visitor_id:id})
 });
 const rejected = await run("https://coloring.rozkalns.net/api/stats/page?page_id=p1&visitor_id="+legacy,{
   headers:{"sec-fetch-site":"cross-site"}
 });
 console.log(JSON.stringify({old,anon,posted,rejected}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""

class PageStatusCompatibilityTests(unittest.TestCase):
    def test_old_get_new_post_and_no_credential_in_anonymous_get(self):
        if not shutil.which("node"):
            self.skipTest("node required")
        result = subprocess.run(["node", "-e", JS], cwd=ROOT, capture_output=True,
                                text=True, check=True)
        data = json.loads(result.stdout)
        self.assertEqual(data["old"]["status"], 200)
        self.assertTrue(data["old"]["body"]["liked"])
        self.assertEqual(data["old"]["headers"]["cache-control"], "no-store")
        self.assertEqual(data["anon"]["body"]["liked"], False)
        self.assertEqual(data["posted"]["status"], 200)
        self.assertTrue(data["posted"]["body"]["liked"])
        self.assertEqual(data["rejected"]["status"], 403)
