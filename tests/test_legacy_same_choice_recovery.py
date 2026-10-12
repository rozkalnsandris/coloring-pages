"""Browser regression: same-value legacy choices must have a safe upgrade path."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = r"""
const vm = require("node:vm"),fs=require("node:fs");
const scenario=process.argv[1];
const KEY="coloring-pages-consent-v1",ID="coloring-pages-visitor-v1";
const v2="v2-"+"a".repeat(64),v2b="v2-"+"d".repeat(64),v2c="v2-"+"e".repeat(64),v3="v3-"+"b".repeat(64);
const initial={version:1,like:true,print:true,decided_at:"2026-10-11T11:00:00Z"};
const stored=new Map(), calls=[], els=[], events={};let reads=0,confirms=0;
if(scenario!=="first")stored.set(KEY,JSON.stringify({
 ...initial,like:scenario==="print_only"?false:true
}));
stored.set(ID,scenario==="v3"?v3:scenario.startsWith("weak")?"not-a-credential":v2);
function El(){this.hidden=false;this.disabled=false;this.checked=false;this.textContent="";this.className="";this.listeners={};this.selectors=new Map();this.classList={add(){},remove(){}};}
El.prototype.setAttribute=function(){};
El.prototype.focus=function(){};
El.prototype.append=function(){};
El.prototype.addEventListener=function(name,fn){this.listeners[name]=fn;};
El.prototype.querySelector=function(q){if(!this.selectors.has(q))this.selectors.set(q,new El());return this.selectors.get(q);};
const document={activeElement:{focus(){}},body:{append(){},classList:{add(){},remove(){}}},createElement(){const e=new El();els.push(e);return e;},dispatchEvent(e){events[e.type]?.(e);},addEventListener(k,fn){events[k]=fn}};
const localStorage={getItem(k){if(k===ID){reads++;if(scenario==="blocked")throw Error("blocked");}return stored.get(k)||null;},setItem(k,v){stored.set(k,String(v));},removeItem(k){stored.delete(k);}};
const response=(data,status=200)=>({ok:status>=200&&status<300,status,async json(){return data;}});
async function fetch(path,opt={}){
  const body=JSON.parse(opt.body||"{}");calls.push({path,body,method:opt.method});
  if(path==="/api/stats/erase-likes"){
    if(scenario==="erase_fail"
       || (scenario==="two_second_fail" && body.visitor_id===v2b)
       || (scenario==="two_first_fail" && body.visitor_id===v2)
       || (scenario==="three_Afail_Bsuccess_A" && body.visitor_id===v2)
       || (scenario==="three_Afail_Bsuccess_C" && body.visitor_id===v2)
       || (scenario==="three_Asuccess_Bfail_A" && body.visitor_id===v2b)
       || scenario==="many_proofs_capacity")
      return response({error:"unavailable"},503);
    if(scenario==="two_second_network" && body.visitor_id===v2b)
      throw Error("network response ambiguous");
    if(scenario==="race")stored.set(ID,v3);
    return response({ok:true});
  }
  if(path==="/api/stats/credential")return response({ok:true,visitor_id:v3,version:3});
  if(path.startsWith("/api/stats/page?"))return response({page_id:"1234567",liked:false});
  return response({error:"unexpected"},503);
}
const window={addEventListener(){},confirm(){confirms++;return !scenario.endsWith("cancel");}};
const ctx={window,document,localStorage,location:{pathname:"/privacy-test",search:""},navigator:{},URLSearchParams,URL,fetch,Date,CustomEvent:class{constructor(type,opt){this.type=type;this.detail=opt?.detail;}}};
vm.runInNewContext(fs.readFileSync("js/consent.js","utf8"),ctx);
vm.runInNewContext(fs.readFileSync("js/stats.js","utf8"),ctx);
const banner=els[0];const e=()=>els.find(v=>v.className==="privacy-erasure-feedback");
const snapshot=()=>({id:stored.get(ID)||null,consent:stored.get(KEY)?JSON.parse(stored.get(KEY)):null,visible:!banner.hidden,confirms,reads,calls:calls.map(v=>({...v})),erasure:e()?.textContent||"",err:banner.querySelector("[data-consent-error]").textContent});
(async()=>{
 if(scenario==="first"){
   await banner.querySelector("[data-consent-deny]").listeners.click();
 } else {
   if(scenario.startsWith("weak")||scenario==="same_accept"||scenario==="same_cancel"||scenario==="erase_fail"||scenario==="race"){
     await window.ColoringStats.getPage("1234567");
   }
   if(scenario==="same_save"||scenario==="weak_save"||scenario==="print_only") {
     await banner.querySelector("[data-consent-settings]").listeners.click();
     await banner.querySelector("[data-consent-save]").listeners.click();
   } else await banner.querySelector("[data-consent-accept]").listeners.click();
 }
 const first=snapshot();
 let second=null;
 if(scenario.startsWith("two_") || scenario.startsWith("three_")){
   // Another tab presents a different v2 token in the SAME JS page session.
   stored.set(ID,v2b);
   await window.ColoringStats.getPage("1234567");
   await banner.querySelector("[data-consent-accept]").listeners.click();
   second=snapshot();
   if(scenario==="two_second_fail" || scenario==="two_second_network")
     await banner.querySelector("[data-consent-accept]").listeners.click();
 }
 let third=null;
 if(scenario.startsWith("three_")){
   // Reappearance of A after B, or an independent third credential C.
   stored.set(ID,scenario==="three_Afail_Bsuccess_C"?v2c:v2);
   await window.ColoringStats.getPage("1234567");
   await banner.querySelector("[data-consent-accept]").listeners.click();
   third=snapshot();
   if(scenario==="three_Afail_Bsuccess_A")
     await banner.querySelector("[data-consent-accept]").listeners.click();
 }
 if(scenario==="many_proofs_capacity"){
   // All ambiguous: at 32 proofs the 33rd MUST be blocked, not evicted.
   for(let i=1;i<=33;i++){
     stored.set(ID,"v2-"+i.toString(16).padStart(64,"0"));
     await window.ColoringStats.getPage("1234567");
     await banner.querySelector("[data-consent-accept]").listeners.click();
   }
   third=snapshot();
 }
 if(scenario==="erase_fail")await banner.querySelector("[data-consent-accept]").listeners.click();
 console.log(JSON.stringify({first,second,third,final:snapshot()}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""
class LegacySameChoiceTests(unittest.TestCase):
    def scenario(self,name):
        if not shutil.which("node"):self.skipTest("Node required")
        p=subprocess.run(["node","-e",JS,name],cwd=ROOT,text=True,capture_output=True,check=True)
        return json.loads(p.stdout)
    def test_v2_same_accept_erases_once_then_issues_v3(self):
        x=self.scenario("same_accept")["first"]
        self.assertEqual([c["path"] for c in x["calls"] if "page?" not in c["path"]],
                         ["/api/stats/erase-likes","/api/stats/credential"])
        self.assertEqual(x["calls"][-2]["body"],{"visitor_id":"v2-"+"a"*64})
        self.assertEqual(x["id"],"v3-"+"b"*64)
        self.assertEqual(x["confirms"],1)
        self.assertIn("bestätigt",x["erasure"])
    def test_v2_same_save_is_explicit_new_consent(self):
        x=self.scenario("same_save")["first"]
        self.assertEqual([c["path"] for c in x["calls"]],
                         ["/api/stats/erase-likes","/api/stats/credential"])
        self.assertTrue(x["consent"]["like"])
        self.assertEqual(x["id"],"v3-"+"b"*64)
    def test_cancel_preserves_legacy_proof_without_write(self):
        x=self.scenario("same_cancel")["first"]
        self.assertEqual(x["id"],"v2-"+"a"*64)
        self.assertEqual([c for c in x["calls"] if "page?" not in c["path"]],[])
        self.assertTrue(x["consent"]["like"])
        self.assertTrue(x["visible"])
    def test_uncertain_erase_never_auto_retries_or_issues(self):
        x=self.scenario("erase_fail")
        self.assertEqual([c["path"] for c in x["final"]["calls"] if "page?" not in c["path"]],
                         ["/api/stats/erase-likes"])
        self.assertEqual(x["final"]["id"],"v2-"+"a"*64)
        self.assertIn("nicht bestätigt",x["first"]["erasure"])
        self.assertTrue(x["first"]["visible"])
    def test_weak_legacy_accept_warns_without_any_erase(self):
        x=self.scenario("weak_accept")["first"]
        self.assertEqual([c["path"] for c in x["calls"] if "page?" not in c["path"]],
                         ["/api/stats/credential"])
        self.assertEqual(x["id"],"v3-"+"b"*64)
        self.assertIn("nicht bestätigt",x["erasure"])
        self.assertEqual(x["confirms"],1)
    def test_weak_save_same_flags_issues_v3(self):
        x=self.scenario("weak_save")["first"]
        self.assertEqual([c["path"] for c in x["calls"] if "page?" not in c["path"]],
                         ["/api/stats/credential"])
        self.assertEqual(x["id"],"v3-"+"b"*64)
    def test_weak_cancel_preserves_old_state(self):
        x=self.scenario("weak_cancel")["first"]
        self.assertEqual(x["id"],"not-a-credential")
        self.assertEqual([c for c in x["calls"] if "page?" not in c["path"]],[])
        self.assertTrue(x["visible"])
    def test_legacy_print_only_does_not_read_like_proof(self):
        x=self.scenario("print_only")["first"]
        self.assertEqual([c["path"] for c in x["calls"]],["/api/stats/credential"])
        self.assertFalse(x["consent"]["like"])
    def test_unavailable_storage_does_not_activate(self):
        x=self.scenario("blocked")["first"]
        self.assertEqual(x["calls"],[])
        self.assertEqual(x["id"],"v2-"+"a"*64)
        self.assertTrue(x["visible"])
    def test_cross_tab_change_does_not_overwrite_new_token(self):
        x=self.scenario("race")["first"]
        self.assertEqual(x["id"],"v3-"+"b"*64)
        self.assertEqual([c["path"] for c in x["calls"] if "page?" not in c["path"]],
                         ["/api/stats/erase-likes"])
        self.assertIn("nicht bestätigt",x["erasure"])
    def test_two_distinct_proofs_cannot_share_erasure_confirmation(self):
        x=self.scenario("two_success")
        requests=[c for c in x["final"]["calls"] if "page?" not in c["path"]]
        self.assertEqual([c["path"] for c in requests],
                         ["/api/stats/erase-likes","/api/stats/credential",
                          "/api/stats/erase-likes","/api/stats/credential"])
        self.assertEqual(requests[0]["body"],{"visitor_id":"v2-"+"a"*64})
        self.assertEqual(requests[2]["body"],{"visitor_id":"v2-"+"d"*64})
        self.assertEqual(x["second"]["id"],"v3-"+"b"*64)
        self.assertEqual(x["second"]["confirms"],2)
        self.assertIn("bestätigt",x["second"]["erasure"])

    def test_ambiguous_second_proof_never_inherits_first_success(self):
        for kind in ("two_second_fail","two_second_network"):
            with self.subTest(kind=kind):
                x=self.scenario(kind)
                req=[c for c in x["final"]["calls"] if "page?" not in c["path"]]
                self.assertEqual([c["path"] for c in req],
                                 ["/api/stats/erase-likes","/api/stats/credential",
                                  "/api/stats/erase-likes"])
                self.assertEqual(req[-1]["body"],{"visitor_id":"v2-"+"d"*64})
                self.assertEqual(x["second"]["id"],"v2-"+"d"*64)
                self.assertIn("nicht bestätigt",x["second"]["erasure"])
                self.assertNotIn("Alte Likes gelöscht",x["second"]["erasure"])
                self.assertEqual(x["second"]["calls"],x["final"]["calls"])
                self.assertIn("nicht bestätigt",x["final"]["err"])

    def test_other_proof_may_succeed_after_first_failed(self):
        x=self.scenario("two_first_fail")
        req=[c for c in x["final"]["calls"] if "page?" not in c["path"]]
        self.assertEqual([c["path"] for c in req],
                         ["/api/stats/erase-likes","/api/stats/erase-likes",
                          "/api/stats/credential"])
        self.assertEqual(req[0]["body"],{"visitor_id":"v2-"+"a"*64})
        self.assertEqual(req[1]["body"],{"visitor_id":"v2-"+"d"*64})
        self.assertEqual(x["second"]["id"],"v3-"+"b"*64)
        self.assertIn("bestätigt",x["second"]["erasure"])

    def test_failed_A_then_successful_B_never_allows_second_A_post(self):
        x=self.scenario("three_Afail_Bsuccess_A")
        req=[c for c in x["final"]["calls"] if "page?" not in c["path"]]
        self.assertEqual([c["path"] for c in req],
                         ["/api/stats/erase-likes","/api/stats/erase-likes",
                          "/api/stats/credential"])
        self.assertEqual([c["body"]["visitor_id"] for c in req if c["path"].endswith("erase-likes")],
                         ["v2-"+"a"*64,"v2-"+"d"*64])
        self.assertEqual(x["third"]["id"],"v2-"+"a"*64)
        self.assertEqual(x["third"]["calls"],x["final"]["calls"])
        self.assertIn("nicht bestätigt",x["third"]["err"])
        self.assertTrue(x["third"]["visible"])

    def test_confirmed_A_after_ambiguous_B_never_resubmits_either(self):
        x=self.scenario("three_Asuccess_Bfail_A")
        req=[c for c in x["final"]["calls"] if "page?" not in c["path"]]
        self.assertEqual([c["path"] for c in req],
                         ["/api/stats/erase-likes","/api/stats/credential",
                          "/api/stats/erase-likes","/api/stats/credential"])
        self.assertEqual([c["body"]["visitor_id"] for c in req if c["path"].endswith("erase-likes")],
                         ["v2-"+"a"*64,"v2-"+"d"*64])
        self.assertEqual(x["third"]["id"],"v3-"+"b"*64)
        self.assertIn("bestätigt",x["third"]["erasure"])

    def test_distinct_third_proof_works_after_ambiguous_first(self):
        x=self.scenario("three_Afail_Bsuccess_C")
        req=[c for c in x["final"]["calls"] if "page?" not in c["path"]]
        self.assertEqual([c["path"] for c in req],
                         ["/api/stats/erase-likes","/api/stats/erase-likes",
                          "/api/stats/credential","/api/stats/erase-likes",
                          "/api/stats/credential"])
        self.assertEqual([c["body"]["visitor_id"] for c in req if c["path"].endswith("erase-likes")],
                         ["v2-"+"a"*64,"v2-"+"d"*64,"v2-"+"e"*64])
        self.assertEqual(x["third"]["id"],"v3-"+"b"*64)

    def test_proof_record_cap_fails_closed_without_eviction(self):
        x=self.scenario("many_proofs_capacity")
        req=[c for c in x["final"]["calls"] if c["path"].endswith("erase-likes")]
        self.assertEqual(len(req),32)
        self.assertEqual(len(x["final"]["calls"]),32)
        self.assertEqual(x["third"]["id"],"v2-"+format(33,"064x"))
        self.assertIn("Zu viele Löschanfragen",x["third"]["err"])
        self.assertTrue(x["third"]["visible"])

    def test_first_refusal_still_never_reads_id(self):
        x=self.scenario("first")["first"]
        self.assertEqual(x["reads"],0)
        self.assertEqual(x["calls"],[])
        self.assertFalse(x["consent"]["like"])
if __name__=="__main__":unittest.main()
