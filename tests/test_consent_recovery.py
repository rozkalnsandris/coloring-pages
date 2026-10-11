"""Behavioral browser harness: consent withdrawal, explicit retry and bounded recovery."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
const vm=require("node:vm"),fs=require("node:fs");
const KEY="coloring-pages-consent-v1",ID="coloring-pages-visitor-v1",
      PENDING="coloring-pages-erasure-pending-v1",proof="v2-"+"f".repeat(64);
const scenario=JSON.parse(process.argv[1]);
const stored=new Map();
const hasConsent=()=>JSON.stringify({version:1,like:true,print:true,decided_at:"2026-10-11T00:00:00Z"});
if(scenario!=="expired"){stored.set(KEY,hasConsent());stored.set(ID,proof);}
else{stored.set(KEY,JSON.stringify({version:1,like:false,print:true,decided_at:"2026-10-11T00:00:00Z"}));
stored.set(PENDING,JSON.stringify({visitor_id:proof,expires_at:Date.now()-10}));}
let idReads=0,requestCalls=0,success=false;
function boot(){
 const created=[],handlers={},docHandlers={};
 function El(){this.hidden=false;this.disabled=false;this.checked=false;this.textContent="";this.listeners={};this.selectors=new Map();this.classList={add(){},remove(){}};}
 El.prototype.setAttribute=function(){};
 El.prototype.focus=function(){};
 El.prototype.append=function(){};
 El.prototype.querySelector=function(key){if(!this.selectors.has(key))this.selectors.set(key,new El());return this.selectors.get(key);};
 El.prototype.addEventListener=function(name,fn){this.listeners[name]=fn;};
 const document={
   activeElement:{focus(){}},
   body:{append(){},classList:{add(){},remove(){}}},
   createElement(){const el=new El();created.push(el);return el;},
   dispatchEvent(event){docHandlers[event.type]?.(event);},
   addEventListener(name,fn){docHandlers[name]=fn;}
 };
 const localStorage={
   getItem(key){if(key===ID)idReads++;return stored.has(key)?stored.get(key):null;},
   setItem(key,value){stored.set(key,String(value));},
   removeItem(key){stored.delete(key);}
 };
 const window={
   addEventListener(name,fn){handlers[name]=fn;},
   confirm(){return true;},
   ColoringStats:{
     getErasureProof(){
       const c=JSON.parse(stored.get(KEY)||"null");
       return c?.like ? (stored.get(ID)||"") : "";
     },
     async eraseLikesWithProof(value) {
       if(value!==proof)throw Error("bad erasure proof");
       requestCalls++;
       if(!success)throw Error("offline");
       return {ok:true};
     }
   }
 };
 const context={document,window,localStorage,Date,CustomEvent:class{constructor(type,init){this.type=type;this.detail=init?.detail;}}};
 vm.runInNewContext(fs.readFileSync("js/consent.js","utf8"),context);
 const banner=created[0],retry=created.find(x=>x.textContent==="Löschung erneut versuchen");
 return {banner,retry,created,handlers};
}
(async()=>{
 let one=boot();
 if(scenario!=="expired")await one.banner.querySelector("[data-consent-deny]").listeners.click();
 const before={
  consent:JSON.parse(stored.get(KEY)),
  oldId:stored.has(ID),
  pending:stored.has(PENDING),
  retryVisible:!one.retry.hidden,
  attempts:requestCalls,
  expiresIn:stored.has(PENDING)?JSON.parse(stored.get(PENDING)).expires_at-Date.now():0
 };
 one=boot(); // new page load: pending recovery must not be silently replayed
 const afterReload={attempts:requestCalls,retryVisible:!one.retry.hidden};
 if(scenario!=="expired"){success=true;await one.retry.listeners.click();}
 console.log(JSON.stringify({before,afterReload,after:{
  attempts:requestCalls,pending:stored.has(PENDING),like:JSON.parse(stored.get(KEY)).like,
  print:JSON.parse(stored.get(KEY)).print},idReads}));
})().catch(err=>{console.error(err.stack);process.exit(1)});
"""

class ConsentRecoveryIntegrationTests(unittest.TestCase):
    def run_case(self, scenario):
        if not shutil.which("node"):
            self.skipTest("node required")
        result = subprocess.run(["node", "-e", HARNESS, json.dumps(scenario)],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_failure_retains_only_short_lived_erasure_proof_and_manual_retry(self):
        out=self.run_case("failed")
        self.assertFalse(out["before"]["consent"]["like"])
        self.assertFalse(out["before"]["consent"]["print"])
        self.assertFalse(out["before"]["oldId"])
        self.assertTrue(out["before"]["pending"])
        self.assertTrue(out["before"]["retryVisible"])
        self.assertGreater(out["before"]["expiresIn"],0)
        self.assertLessEqual(out["before"]["expiresIn"],86400000)
        self.assertEqual(out["before"]["attempts"],1)
        self.assertEqual(out["afterReload"]["attempts"],1)
        self.assertTrue(out["afterReload"]["retryVisible"])
        self.assertEqual(out["after"]["attempts"],2)
        self.assertFalse(out["after"]["pending"])
        self.assertFalse(out["after"]["like"])

    def test_expired_credential_is_discarded_without_network_request(self):
        out=self.run_case("expired")
        self.assertFalse(out["before"]["pending"])
        self.assertFalse(out["before"]["retryVisible"])
        self.assertEqual(out["after"]["attempts"],0)
        self.assertTrue(out["after"]["print"])
