"""End-to-end browser regression for deletion-only legacy v2 credentials.

Runs both real JS modules in a minimal Node VM DOM with mocked localStorage
and API. The old v2 token must never be accepted for normal Like/Print writes.
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
const vm = require("node:vm"), fs = require("node:fs");
const scenario = JSON.parse(process.argv[1]);
const KEY = "coloring-pages-consent-v1", ID = "coloring-pages-visitor-v1";
const v2 = "v2-" + "a".repeat(64), v3 = "v3-" + "b".repeat(64);
const stored = new Map();
const first = scenario === "first";
const initial = {
  version:1, like:scenario !== "print_only", print:true,
  decided_at:"2026-10-12T10:00:00.000Z"
};
if (!first) stored.set(KEY, JSON.stringify(initial));
stored.set(ID, scenario === "weak" ? "legacy-client-123" :
  scenario === "v3" ? v3 : v2);
let idReads = 0, calls = [], idReadsBefore = 0;
const elements = [], events = {};
function El() {
  this.hidden = false; this.disabled = false; this.checked = false;
  this.textContent = ""; this.listeners = {}; this.selectors = new Map();
  this.classList = {add(){},remove(){}};
}
El.prototype.setAttribute = function(){};
El.prototype.focus = function(){};
El.prototype.append = function(){};
El.prototype.querySelector = function(k) {
  if (!this.selectors.has(k)) this.selectors.set(k,new El());
  return this.selectors.get(k);
};
El.prototype.addEventListener = function(k, fn) {this.listeners[k]=fn;};
const document = {
  activeElement:{focus(){}},
  body:{append(){},classList:{add(){},remove(){}}},
  createElement(){const el=new El();elements.push(el);return el;},
  dispatchEvent(){},
  addEventListener(k,fn){events[k]=fn}
};
const localStorage = {
  getItem(k) {
    if(k===ID) {
      idReads++;
      if(scenario==="blocked") throw Error("storage read blocked");
    }
    return stored.get(k) || null;
  },
  setItem(k,v){stored.set(k,String(v));},
  removeItem(k){stored.delete(k);}
};
const response = (data,status=200) =>
  ({ok:status>=200&&status<300,status,async json(){return data;}});
async function fetch(path, options={}) {
  const body=JSON.parse(options.body || "{}");
  calls.push({path,method:options.method,body});
  if (path === "/api/stats/erase-likes") {
    return scenario==="failed" ? response({error:"offline"},503) : response({ok:true});
  }
  if (path === "/api/stats/credential") {
    return response(body.like || body.print
      ? {ok:true, visitor_id:v3,version:3} : {ok:true,revoked:true});
  }
  return response({error:"unexpected endpoint"},503);
}
const window = {addEventListener(){},confirm(){return true;}};
const context = {window,document,localStorage,location:{pathname:"/privacy-test",search:""},
  navigator:{},URLSearchParams,URL,fetch,Date,CustomEvent:class {
    constructor(type,options){this.type=type;this.detail=options?.detail;}
  }};
vm.runInNewContext(fs.readFileSync("js/consent.js","utf8"),context);
vm.runInNewContext(fs.readFileSync("js/stats.js","utf8"),context);
const banner=elements[0];
const proofBefore=window.ColoringStats.getErasureProof();
idReadsBefore=idReads;
(async () => {
  if (scenario === "print_only" || scenario === "legacy_print") {
    const like=banner.querySelector("[data-consent-like]");
    const print=banner.querySelector("[data-consent-print]");
    like.checked=false;print.checked=scenario==="legacy_print";
    await banner.querySelector("[data-consent-save]").listeners.click();
  } else {
    await banner.querySelector("[data-consent-deny]").listeners.click();
  }
  const after={
    consent:JSON.parse(stored.get(KEY)), visitor:stored.get(ID)||null,
    reads:idReads, proofBefore, idReadsBefore,
    calls, feedback:elements.find(x=>x.className==="privacy-erasure-feedback")?.textContent||"",
    keys:[...stored.keys()]
  };
  // No implicit retries on a later click after revocation.
  await banner.querySelector("[data-consent-erase]").listeners.click();
  console.log(JSON.stringify({...after,callsAfter: calls.length}));
})().catch(e=>{console.error(e.stack);process.exit(1);});
"""

class LegacyErasureBrowserTests(unittest.TestCase):
    def run_case(self, scenario):
        if not shutil.which("node"):
            self.skipTest("node needed for browser regression")
        proc=subprocess.run(
            ["node","-e",HARNESS,json.dumps(scenario)],
            cwd=ROOT,text=True,capture_output=True,check=True,
        )
        return json.loads(proc.stdout)

    def test_v2_like_withdrawal_calls_erasure_exactly_once(self):
        x=self.run_case("legacy_deny")
        self.assertEqual(x["proofBefore"],"v2-"+"a"*64)
        self.assertEqual(x["idReadsBefore"],1)
        self.assertEqual(len(x["calls"]),1)
        self.assertEqual(x["calls"][0]["path"],"/api/stats/erase-likes")
        self.assertEqual(x["calls"][0]["method"],"POST")
        self.assertEqual(x["calls"][0]["body"],{"visitor_id":"v2-"+"a"*64})
        self.assertEqual(x["callsAfter"],1)
        self.assertIsNone(x["visitor"])
        self.assertFalse(x["consent"]["like"])
        self.assertFalse(x["consent"]["print"])
        self.assertIn("bestätigt",x["feedback"])

    def test_v2_to_print_only_issues_new_v3_and_erases_old_v2(self):
        x=self.run_case("legacy_print")
        self.assertEqual([c["path"] for c in x["calls"]],
                         ["/api/stats/credential","/api/stats/erase-likes"])
        self.assertEqual(x["calls"][0]["body"],{"version":1,"like":False,"print":True})
        self.assertEqual(x["calls"][1]["body"],{"visitor_id":"v2-"+"a"*64})
        self.assertEqual(x["visitor"],"v3-"+"b"*64)
        self.assertFalse(x["consent"]["like"])
        self.assertTrue(x["consent"]["print"])
        self.assertIn("bestätigt",x["feedback"])

    def test_failed_erasure_reports_uncertainty_and_never_retries(self):
        x=self.run_case("failed")
        self.assertEqual(x["callsAfter"],1)
        self.assertEqual(len(x["calls"]),1)
        self.assertIsNone(x["visitor"])
        self.assertIn("nicht bestätigt",x["feedback"])
        self.assertNotIn("coloring-pages-erasure-pending-v1",x["keys"])

    def test_missing_or_weak_legacy_id_is_not_submitted(self):
        for scenario in ("weak","blocked"):
            with self.subTest(scenario=scenario):
                x=self.run_case(scenario)
                self.assertEqual(x["calls"],[])
                self.assertIn("nicht bestätigt",x["feedback"])
                self.assertIsNone(x["visitor"])

    def test_refusal_without_like_consent_does_not_read_id(self):
        x=self.run_case("first")
        self.assertEqual(x["idReads"],0)
        self.assertEqual(x["proofBefore"],"")
        self.assertIsNone(x["visitor"])
        self.assertEqual(x["calls"],[])
        y=self.run_case("print_only")
        self.assertEqual(y["proofBefore"],"")
        self.assertEqual(y["idReadsBefore"],0)
        self.assertEqual(y["calls"],[])
        self.assertFalse(y["consent"]["like"])

    def test_v3_withdrawal_does_not_call_legacy_erase(self):
        x=self.run_case("v3")
        self.assertEqual(x["proofBefore"],"")
        self.assertEqual([c["path"] for c in x["calls"]],["/api/stats/credential"])
        self.assertEqual(x["calls"][0]["body"]["prior_id"],"v3-"+"b"*64)
        self.assertIsNone(x["visitor"])
        self.assertIn("bestätigt",x["feedback"])

if __name__ == "__main__":
    unittest.main()
