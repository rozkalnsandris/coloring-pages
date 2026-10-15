"""Cookie Like/anonymous Print browser integration (source and behavioral VM)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CookieFrontendTests(unittest.TestCase):
    def test_public_pages_load_only_new_cookie_js(self):
        for name in ("index.html","detail.html","kita.html"):
            html=(ROOT/name).read_text()
            self.assertIn("js/like-cookie-consent.js?v=cookie182-1",html)
            self.assertIn("js/stats-cookie.js?v=cookie182-1",html)
            self.assertLess(html.index("js/like-cookie-consent.js"),html.index("js/stats-cookie.js"))
            self.assertNotIn('src="js/consent.js?',html)
            self.assertNotIn('src="js/stats.js?',html)
    def test_stateless_print_and_cookie_limited_like(self):
        stats=(ROOT/"js/stats-cookie.js").read_text()
        consent=(ROOT/"js/like-cookie-consent.js").read_text()
        self.assertIn('"/print-aggregate"',stats)
        segment=stats.split("function trackPrint(pageId) {",1)[1].split("window.ColoringStats=",1)[0]
        for value in ("visitor_id","VISITOR_KEY","getVisitorId","localStorage","ColoringConsent"):
            self.assertNotIn(value,segment)
        self.assertIn('"/like/choice"',stats)
        self.assertIn('"/like/consent"',stats)
        self.assertIn('"/like/forget"',stats)
        self.assertIn('"/like/session"',stats)
        self.assertIn('data-like-accept',consent)
        self.assertIn('data-like-deny',consent)
        self.assertIn('data-like-forget',consent)
        self.assertNotIn('document.cookie',consent)
        self.assertNotIn('localStorage',consent)
        self.assertNotIn('changeCredential(',stats)
    def test_aggregate_print_posts_no_visitor_id_and_like_is_desired_state(self):
        if not shutil.which("node"):self.skipTest("node unavailable")
        script=r"""
const fs=require("fs"),vm=require("vm");
const calls=[],states=[],res=(o)=>({ok:true,status:200,async json(){return o}});
let liked=false,consented=true,prints=0;
const context={
  URLSearchParams,URL,Blob,
  location:{pathname:"/test",search:""},
  navigator:{sendBeacon:()=>false},
  window:{ColoringConsent:{allows:(s)=>s==="like"&&consented,
    syncFromServer(v){consented=v;states.push(v)}}},
  document:{dispatchEvent(){}},
  fetch:async(url,opts={})=>{
    const body=opts.body?JSON.parse(opts.body):null;
    calls.push({url,body});
    if(url.includes("/like/state"))return res({page_id:"1234567",liked,consented,like_count:liked?1:0});
    if(url.endsWith("/like/choice")){liked=body.liked;return res({page_id:"1234567",liked,like_count:liked?1:0});}
    if(url.endsWith("/like/session"))return res({consented:true});
    if(url.endsWith("/like/consent"))return res({ok:true});
    if(url.endsWith("/print-aggregate")){prints++;return res({ok:true});}
    return res({ok:true});
  }
};
vm.runInNewContext(fs.readFileSync("js/stats-cookie.js","utf8"),context);
(async()=>{
 await context.window.ColoringStats.getPage("1234567");
 const a=await context.window.ColoringStats.toggleLike("1234567");
 const b=await context.window.ColoringStats.toggleLike("1234567");
 context.window.ColoringStats.trackPrint("1234567");
 await new Promise(resolve=>setImmediate(resolve));
 console.log(JSON.stringify({a:a.liked,b:b.liked,prints,calls,states}));
})().catch(e=>{console.error(e.stack);process.exit(1)});
"""
        p=subprocess.run(["node","-e",script],cwd=ROOT,text=True,capture_output=True,check=True)
        result=json.loads(p.stdout)
        self.assertTrue(result["a"])
        self.assertFalse(result["b"])
        self.assertEqual(result["prints"],1)
        self.assertEqual([x["body"]["liked"] for x in result["calls"] if x["url"].endswith("/like/choice")],[True,False])
        self.assertEqual([x["body"] for x in result["calls"] if x["url"].endswith("/print-aggregate")],[{"page_id":"1234567"}])
        self.assertEqual(result["states"],[True])
if __name__=="__main__":unittest.main()
