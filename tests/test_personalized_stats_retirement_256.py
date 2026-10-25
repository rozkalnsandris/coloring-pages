"""Functional regression for retiring personalized Stats Worker routes (#256)."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
import fs from 'node:fs';
const fixture=JSON.parse(process.argv[1]);
const source=fs.readFileSync('cloudflare/stats-worker.js','utf8');
const {default:worker}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
let dbCalls=0, limiterCalls=0;
const env={
  DB:{
    prepare(){dbCalls++;throw Error('retired route touched D1');},
    batch(){dbCalls++;throw Error('retired route touched D1');},
  },
  RATE_LIMITER:{limit(){limiterCalls++;throw Error('retired route touched limiter');}},
};
const headers=new Headers({
  origin:'https://ausmalwiese.de',
  'sec-fetch-site':'same-origin',
  'content-type':'application/json',
  cookie:'__Secure-aw-like-v1=l1-'+'a'.repeat(64),
});
const request=new Request('https://ausmalwiese.de'+fixture.path,{
  method:fixture.method,headers,
  ...(fixture.method==='GET'?{}:{body:JSON.stringify(fixture.body||{page_id:'sample',visitor_id:'legacy-id'})}),
});
const response=await worker.fetch(request,env);
console.log(JSON.stringify({status:response.status,data:await response.json(),dbCalls,limiterCalls}));
"""


class PersonalizedRouteRetirementTests(unittest.TestCase):
    def request(self, path, method="GET", body=None):
        result=subprocess.run(
            ["node","--input-type=module","-e",HARNESS,json.dumps(
                {"path":path,"method":method,"body":body}
            )],
            cwd=ROOT,text=True,capture_output=True,timeout=10,check=False,
        )
        self.assertEqual(result.returncode,0,result.stderr[-2000:])
        return json.loads(result.stdout)

    def assert_retired(self, result):
        self.assertEqual(result["status"],410)
        self.assertEqual(result["data"],{"error":"legacy_personalized_api_retired"})
        self.assertEqual(result["dbCalls"],0)
        self.assertEqual(result["limiterCalls"],0)

    def test_legacy_post_like_and_print_are_gone(self):
        self.assert_retired(self.request(
            "/api/stats/like","POST",{"page_id":"sample","visitor_id":"legacy-id"}
        ))
        self.assert_retired(self.request(
            "/api/stats/print","POST",{"page_id":"sample","visitor_id":"legacy-id"}
        ))

    def test_page_visitor_recognition_is_retired(self):
        self.assert_retired(self.request(
            "/api/stats/page?page_id=sample&visitor_id=legacy-id"
        ))

    def test_cookie_state_creation_and_choice_are_retired_without_d1(self):
        for path,method,body in (
            ("/api/stats/like/session","GET",None),
            ("/api/stats/like/state?page_id=sample","GET",None),
            ("/api/stats/like/consent","POST",{"accept":True,"version":1}),
            ("/api/stats/like/choice","POST",{"page_id":"sample","liked":True}),
        ):
            with self.subTest(path=path):
                self.assert_retired(self.request(path,method,body))

    def test_erasure_paths_remain_in_source(self):
        source=(ROOT/"cloudflare/stats-worker.js").read_text(encoding="utf-8")
        self.assertIn('path==="/api/stats/erase-likes"',source)
        self.assertIn('"/api/stats/like/forget"',source)
        self.assertIn("DELETE FROM likes WHERE visitor_hash",source)


if __name__ == "__main__":
    unittest.main()
