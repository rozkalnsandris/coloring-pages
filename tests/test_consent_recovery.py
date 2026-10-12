"""Behavioral regression: consent revocation uses one deletion attempt, no retry token."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
const vm=require("node:vm"),fs=require("node:fs");
const KEY="coloring-pages-consent-v1",ID="coloring-pages-visitor-v1",
      proof="v2-"+"f".repeat(64);
const scenario=JSON.parse(process.argv[1]);
const stored=new Map();
const granted=JSON.stringify({version:1,like:true,print:true,decided_at:"2026-10-11T00:00:00Z"});
const printOnly=JSON.stringify({version:1,like:false,print:true,decided_at:"2026-10-11T00:00:00Z"});
if(scenario!=="first"){stored.set(KEY,scenario==="print_only"?printOnly:granted);stored.set(ID,proof);}
let idReads=0,erasureCalls=0;
function boot(){
 const created=[],handlers={},events={};
 function El(){this.hidden=false;this.disabled=false;this.checked=false;this.textContent="";this.listeners={};this.selectors=new Map();this.classList={add(){},remove(){}};}
 El.prototype.setAttribute=function(){};
 El.prototype.focus=function(){};
 El.prototype.append=function(){};
 El.prototype.querySelector=function(key){if(!this.selectors.has(key))this.selectors.set(key,new El());return this.selectors.get(key);};
 El.prototype.addEventListener=function(event,cb){this.listeners[event]=cb;};
 const document={
   activeElement:{focus(){}},
   body:{append(){},classList:{add(){},remove(){}}},
   createElement(){const el=new El();created.push(el);return el;},
   dispatchEvent(){},
   addEventListener(name,cb){events[name]=cb;}
 };
 const localStorage={
   getItem(key){if(key===ID)idReads++;return stored.get(key)||null;},
   setItem(key,value){stored.set(key,String(value));},
   removeItem(key){stored.delete(key);}
 };
 const window={
   addEventListener(name,cb){handlers[name]=cb;},
   confirm(){return true;},
   ColoringStats:{
     getErasureProof(){idReads++;return JSON.parse(stored.get(KEY)||"null")?.like ? stored.get(ID)||"" : "";},
     async eraseLikesWithProof(value){
       if(value!==proof)throw Error("bad credential");
       erasureCalls++;
       if(scenario==="failed")throw Error("offline");
       return {ok:true};
     }
   }
 };
 const context={document,window,localStorage,Date,CustomEvent:class{constructor(type){this.type=type}}};
 vm.runInNewContext(fs.readFileSync("js/consent.js","utf8"),context);
 return {banner:created[0],feedback:created.find(x=>x.className==="privacy-erasure-feedback"),created};
}
(async()=>{
 const first=boot();
 await first.banner.querySelector("[data-consent-deny]").listeners.click();
 const after={consent:JSON.parse(stored.get(KEY)),hasId:stored.has(ID),calls:erasureCalls,idReads,feedback:first.created.find(x=>x.className==="privacy-erasure-feedback")?.textContent||""};
 boot();
 console.log(JSON.stringify({after,reloadedCalls:erasureCalls,keys:[...stored.keys()]}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""
class ConsentWithdrawalTests(unittest.TestCase):
    def run_case(self, scenario):
        if not shutil.which("node"):
            self.skipTest("node required")
        p=subprocess.run(["node","-e",HARNESS,json.dumps(scenario)],cwd=ROOT,capture_output=True,text=True,check=True)
        return json.loads(p.stdout)

    def test_confirmed_deletion_removes_id_without_creating_retry_data(self):
        x=self.run_case("success")
        self.assertFalse(x["after"]["consent"]["like"])
        self.assertFalse(x["after"]["consent"]["print"])
        self.assertFalse(x["after"]["hasId"])
        self.assertEqual(x["after"]["calls"],1)
        self.assertEqual(x["reloadedCalls"],1)
        self.assertEqual(x["keys"],["coloring-pages-consent-v1"])
        self.assertIn("bestätigt",x["after"]["feedback"])

    def test_failed_deletion_reports_uncertainty_without_storing_proof(self):
        x=self.run_case("failed")
        self.assertFalse(x["after"]["hasId"])
        self.assertEqual(x["after"]["calls"],1)
        self.assertEqual(x["reloadedCalls"],1)
        self.assertEqual(x["keys"],["coloring-pages-consent-v1"])
        self.assertIn("nicht bestätigt",x["after"]["feedback"])

    def test_no_like_consent_never_reads_identifier_for_erasure(self):
        for mode in ("first","print_only"):
            with self.subTest(mode=mode):
                x=self.run_case(mode)
                self.assertEqual(x["after"]["calls"],0)
                self.assertEqual(x["after"]["idReads"],0)
