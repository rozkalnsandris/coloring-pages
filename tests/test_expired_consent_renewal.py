"""Browser flow tests: v3 expiry must never silently renew a credential."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HARNESS=r"""
const vm=require("vm"),fs=require("fs"),scenario=process.argv[1];
const CK="coloring-pages-consent-v1",ID="coloring-pages-visitor-v1";
const expired="v3-"+"a".repeat(64),newId="v3-"+"b".repeat(64),legacy="v2-"+"c".repeat(64);
const values=new Map(),calls=[],els=[],listeners={};let reads=0;
if(scenario!=="denied")values.set(CK,JSON.stringify({version:1,like:true,print:true,decided_at:"2026-10-12T01:00:00Z"}));
if(!["denied","missing"].includes(scenario))values.set(ID,scenario==="legacy"?legacy:expired);
function El(){this.hidden=false;this.disabled=false;this.checked=false;this.textContent="";this.className="";this.listeners={};this.selectors=new Map();this.classList={add(){},remove(){}};}
El.prototype.setAttribute=function(){};
El.prototype.focus=function(){};
El.prototype.append=function(){};
El.prototype.addEventListener=function(e,f){this.listeners[e]=f};
El.prototype.querySelector=function(e){if(!this.selectors.has(e))this.selectors.set(e,new El());return this.selectors.get(e)};
const doc={activeElement:{focus(){}},body:{append(){},classList:{add(){},remove(){}}},createElement(){const e=new El();els.push(e);return e},dispatchEvent(e){listeners[e.type]?.(e)},addEventListener(e,f){listeners[e]=f}};
const store={getItem(k){if(k===ID)reads++;return values.get(k)||null},setItem(k,v){values.set(k,String(v))},removeItem(k){values.delete(k)}};
const response=(status,v)=>({ok:status>=200&&status<300,status,async json(){return v}});
async function fetch(url,opt={}){
 const body=opt.body?JSON.parse(opt.body):{};calls.push({url,body,keepalive:!!opt.keepalive});
 if(url.endsWith("/credential"))return response(200,{ok:true,visitor_id:newId});
 if(url.includes("/page?"))return response(200,{liked:false,print_count:2,like_count:1});
 if(url.endsWith("/page")||url.endsWith("/like")||url.endsWith("/print")){
   if(scenario==="race")values.set(ID,newId);
   return response(scenario==="other403"?403:scenario==="failure"?503:403,{error:scenario==="other403"?"forbidden":scenario==="failure"?"unavailable":"credential_expired"});
 }
 return response(200,{ok:true});
}
const context={window:{addEventListener(){},confirm(){return true}},document:doc,localStorage:store,
 location:{pathname:"/privacy-test",search:""},fetch,URLSearchParams,URL,navigator:{},Date,
 CustomEvent:class{constructor(type,opt){this.type=type;this.detail=opt?.detail}}};
vm.runInNewContext(fs.readFileSync("js/consent.js","utf8"),context);
vm.runInNewContext(fs.readFileSync("js/stats.js","utf8"),context);
const banner=els[0],flush=async()=>{for(let i=0;i<10;i++)await Promise.resolve()};
const take=()=>({id:values.get(ID)||null,consent:values.get(CK)||null,
 shown:!banner.hidden,err:banner.querySelector("[data-consent-error]").textContent,
 calls:[...calls],reads,allows:context.window.ColoringConsent.allows("like")});
(async()=>{
 if(["page","denied","race","other403","failure","legacy"].includes(scenario)){
   await context.window.ColoringStats.getPage("1234567").catch(()=>{});
 } else if(scenario==="print"){context.window.ColoringStats.trackPrint("1234567");await flush();}
 else await context.window.ColoringStats.toggleLike("1234567").catch(()=>{});
 const before=take();
 if(scenario==="page"){
   await banner.querySelector("[data-consent-accept]").listeners.click();
   await flush();
 }
 console.log(JSON.stringify({before,after:take()}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""
class ExpiredV3ConsentTests(unittest.TestCase):
    def run_case(self,scenario):
        if not shutil.which("node"):self.skipTest("node required")
        p=subprocess.run(["node","-e",HARNESS,scenario],cwd=ROOT,text=True,capture_output=True,check=True)
        return json.loads(p.stdout)
    def test_expiry_removes_consent_and_requires_explicit_optin(self):
        o=self.run_case("page");a,b=o["before"],o["after"]
        self.assertIsNone(a["id"]);self.assertIsNone(a["consent"])
        self.assertTrue(a["shown"]);self.assertFalse(a["allows"])
        self.assertIn("erneut",a["err"])
        self.assertEqual([v["url"] for v in a["calls"]],["/api/stats/page","/api/stats/page?page_id=1234567"])
        self.assertEqual([v["url"] for v in b["calls"]].count("/api/stats/credential"),1)
        self.assertEqual(b["id"],"v3-"+"b"*64)
        self.assertIsNotNone(b["consent"])
        self.assertFalse(b["shown"])
    def test_like_expiry_stops_any_token_reissue(self):
        a=self.run_case("like")["before"]
        self.assertIsNone(a["id"]);self.assertTrue(a["shown"])
        self.assertEqual([v["url"] for v in a["calls"]],["/api/stats/like"])
    def test_print_expiry_is_observable_and_does_not_block_print(self):
        a=self.run_case("print")["before"]
        self.assertTrue(a["shown"]);self.assertIsNone(a["id"])
        self.assertEqual([v["url"] for v in a["calls"]],["/api/stats/print"])
        self.assertTrue(a["calls"][0]["keepalive"])
    def test_missing_id_cannot_auto_issue(self):
        a=self.run_case("missing")["before"]
        self.assertTrue(a["shown"]);self.assertIsNone(a["consent"])
        self.assertEqual(a["calls"],[])
    def test_legacy_v2_is_not_silently_destroyed(self):
        a=self.run_case("legacy")["before"]
        self.assertEqual(a["id"],"v2-"+"c"*64)
        self.assertIsNotNone(a["consent"]);self.assertTrue(a["shown"])
        self.assertEqual([v["url"] for v in a["calls"]],["/api/stats/page?page_id=1234567"])
    def test_stale_expiry_response_does_not_clear_new_token(self):
        a=self.run_case("race")["before"]
        self.assertEqual(a["id"],"v3-"+"b"*64)
        self.assertIsNotNone(a["consent"]);self.assertFalse(a["shown"])
    def test_unrelated_403_and_server_failure_are_not_expiry(self):
        for mode in ("other403","failure"):
            with self.subTest(mode=mode):
                a=self.run_case(mode)["before"]
                self.assertEqual(a["id"],"v3-"+"a"*64)
                self.assertIsNotNone(a["consent"])
                self.assertFalse(a["shown"])
    def test_refusal_does_not_read_identifier(self):
        a=self.run_case("denied")["before"]
        self.assertEqual(a["reads"],0)
        self.assertEqual([v["url"] for v in a["calls"]],["/api/stats/page?page_id=1234567"])
if __name__=="__main__":unittest.main()
