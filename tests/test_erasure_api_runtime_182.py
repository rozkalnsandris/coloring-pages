"""Worker erasure outcomes with mocked D1; no LIVE data."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class ErasureApiRuntime(unittest.TestCase):
    def test_fail_closed(self):
        if not shutil.which("node"):
            self.skipTest("Node.js unavailable")
        harness=r"""
const fs=require("node:fs"),vm=require("node:vm");
const src=fs.readFileSync("cloudflare/stats-worker.js","utf8");
if(src.split("export default {").length!==2)throw Error("unexpected Worker export");
const box={Request,Response,Headers,URL,URLSearchParams,TextEncoder,Uint8Array,
  crypto:require("node:crypto").webcrypto};
vm.runInNewContext(src.replace("export default {","globalThis.worker = {"),box);
const proof="v3-"+"a".repeat(64),token="l1-"+"b".repeat(64),origin="https://ausmalwiese.de";
async function attempt(kind,rows,cross=false,valid=false){
  let batches=0;
  const env={RATE_LIMITER:{limit:async()=>({success:true})},DB:{
    prepare(sql){return {bind(){return {first:async()=>valid?{valid:1}:null}}}},
    batch:async()=>{batches++;if(kind==="throw")throw Error("D1 failure");return rows}
  }};
  const cookie=kind==="cookie",path=cookie?"/api/stats/like/forget":"/api/stats/erase-legacy-v3";
  const headers={"Content-Type":"application/json","Origin":cross?"https://example.org":origin,
    "Sec-Fetch-Site":"same-origin"};
  if(cookie)headers.cookie="__Secure-aw-like-v1="+token;
  const req=new Request(origin+path,{method:"POST",headers,
    body:JSON.stringify(cookie?{confirm:true}:{visitor_id:proof})});
  try{
    const response=await box.worker.fetch(req,env);
    return {status:response.status,body:await response.json(),batches};
  }catch(e){return {status:"rejected",batches}};
}
(async()=>{
 const ok=(a,b)=>[{success:true,meta:{changes:a}},{success:true,meta:{changes:b}}];
 const results={
   both:await attempt("v3",ok(2,1)),
   credentialOnly:await attempt("v3",ok(0,1)),
   none:await attempt("v3",ok(0,0)),
   missing:await attempt("v3",[{success:true,meta:{}},{success:true,meta:{changes:1}}]),
   nullMeta:await attempt("v3",[{success:true,meta:{changes:null}},{success:true,meta:{changes:1}}]),
   failed:await attempt("v3",[{success:false,meta:{changes:1}},{success:true,meta:{changes:1}}]),
   thrown:await attempt("throw",[]),
   crossOrigin:await attempt("v3",ok(1,1),true),
   expiredCookie:await attempt("cookie",ok(1,1)),
   invalidForget:await attempt("cookie",ok(1,0),false,true),
   validForget:await attempt("cookie",ok(1,1),false,true)
 };
 process.stdout.write(JSON.stringify(results));
})().catch(e=>{process.stderr.write(e.stack);process.exit(1)});
"""
        run=subprocess.run(["node","-e",harness],cwd=ROOT,check=True,
                           text=True,capture_output=True,timeout=20)
        d=json.loads(run.stdout)
        self.assertEqual((d["both"]["status"],d["both"]["body"]["likes_deleted"]),(200,2))
        self.assertTrue(d["both"]["body"]["credential_revoked"])
        self.assertEqual((d["credentialOnly"]["status"],d["credentialOnly"]["body"]["likes_deleted"]),(200,0))
        self.assertTrue(d["credentialOnly"]["body"]["credential_revoked"])
        self.assertEqual(d["none"]["status"],404)
        for case in ("missing","nullMeta","failed"):
            with self.subTest(case=case):
                self.assertEqual(d[case]["status"],503)
                self.assertNotIn("matched",d[case]["body"])
        self.assertEqual(d["thrown"]["status"],"rejected")
        self.assertEqual((d["crossOrigin"]["status"],d["crossOrigin"]["batches"]),(403,0))
        self.assertEqual((d["expiredCookie"]["status"],d["expiredCookie"]["batches"]),(403,0))
        self.assertEqual(d["invalidForget"]["status"],503)
        self.assertEqual(d["validForget"]["status"],200)
        self.assertTrue(d["validForget"]["body"]["revoked"])


if __name__=="__main__":
    unittest.main()
