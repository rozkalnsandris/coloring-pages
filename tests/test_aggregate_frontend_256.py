"""Run the real browser client without persistent storage or network access."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
const fs = require('node:fs'), vm = require('node:vm');
const f = JSON.parse(process.argv[1]), calls = [], timers = [];
let storageReads = 0, aborted = 0;
function client() {
  const document = {referrer:''};
  Object.defineProperty(document, 'cookie', {get(){storageReads++; throw Error('cookie forbidden');}});
  const ctx = {
    window:{}, document, URL, URLSearchParams, AbortController,
    location:new URL('https://ausmalwiese.de/stats.html?campaign=dortmund-01'),
    performance:{getEntriesByType:()=>[]}, navigator:{},
    setTimeout(fn){timers.push(fn);return timers.length;}, clearTimeout(){},
    fetch(url, options) {
      calls.push({url, credentials:options.credentials, method:options.method || 'GET',
                  body:options.body ? JSON.parse(options.body) : null});
      if (url.endsWith('/print-aggregate')) {
        if(f.mode==='print-sync') throw Error('synchronous telemetry failure');
        return Promise.reject(Error('offline print telemetry'));
      }
      const isLike = url.endsWith('/like-aggregate');
      if(isLike && f.mode==='timeout') return new Promise((resolve,reject)=>{
        options.signal.addEventListener('abort',()=>{aborted++;reject(Error('aborted'));});
      });
      if(isLike && f.mode==='network') return Promise.reject(Error('connection lost'));
      let data = {page_id:'sample',like_count:isLike?5:4,print_count:2,liked:true};
      if(isLike) data.reacted=true;
      if(f.mode==='bad-read' && !isLike) data.like_count='4';
      if(isLike && f.mode==='wrong-page') data.page_id='other';
      if(isLike && f.mode==='bad-count') data.like_count='5';
      if(isLike && f.mode==='zero') data.like_count=0;
      if(isLike && f.mode==='unconfirmed') data.reacted=false;
      return Promise.resolve({ok:!(isLike && f.mode==='http'),
        status:isLike?(f.mode==='http'?503:f.mode==='wrong-status'?200:201):200,
        json:async()=>{if(isLike && f.mode==='json') throw Error('invalid JSON');return data;},
      });
    },
  };
  for(const key of ['localStorage','sessionStorage','indexedDB','crypto']) {
    Object.defineProperty(ctx,key,{get(){storageReads++;throw Error('identity forbidden');}});
  }
  vm.runInNewContext(fs.readFileSync('js/stats.js','utf8'),ctx);
  return ctx.window.ColoringStats;
}
(async()=>{
  const api=client();
  let read, readFailed=false, success=false;
  try {read=await api.getPage('sample');} catch {readFailed=true;}
  const first=api.addLike('sample').then(v=>{success=v.reacted;},()=>{});
  await api.addLike('sample').catch(()=>{}); // while first request is in flight
  if(f.mode==='timeout') timers[0]();
  await first;
  await api.addLike('sample').catch(()=>{}); // after success or an uncertain result
  api.trackPrint('sample');
  await api.getOverview(); // internal Access-protected reads retain credentials
  if(f.reload) await client().addLike('sample');
  await new Promise(setImmediate);
  console.log(JSON.stringify({calls,read,readFailed,success,storageReads,aborted}));
})().catch(e=>{console.error(e);process.exit(1);});
"""


class AggregateFrontendTests(unittest.TestCase):
    def run_client(self, **fixture):
        result = subprocess.run(['node', '-e', HARNESS, json.dumps(fixture)],
                                cwd=ROOT, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        return json.loads(result.stdout)

    def test_public_requests_have_no_identity_and_admin_access_is_preserved(self):
        result = self.run_client()
        self.assertEqual(result['storageReads'], 0)
        self.assertTrue(result['success'])
        self.assertEqual(result['read'], {'page_id':'sample','like_count':4,'print_count':2})
        self.assertEqual(result['calls'], [
            {'url':'/api/stats/page?page_id=sample','credentials':'omit','method':'GET','body':None},
            {'url':'/api/stats/like-aggregate','credentials':'omit','method':'POST','body':{'page_id':'sample'}},
            {'url':'/api/stats/print-aggregate','credentials':'omit','method':'POST',
             'body':{'page_id':'sample','campaign':'dortmund-01'}},
            {'url':'/api/stats/overview','credentials':'same-origin','method':'GET','body':None},
        ])

    def test_invalid_uncertain_and_timed_out_results_never_resend(self):
        for mode in ('network','http','json','wrong-page','bad-count','zero',
                     'unconfirmed','wrong-status','timeout'):
            with self.subTest(mode=mode):
                result = self.run_client(mode=mode)
                self.assertFalse(result['success'])
                self.assertEqual(sum(c['url'].endswith('/like-aggregate') for c in result['calls']), 1)
                self.assertEqual(result['storageReads'], 0)
                if mode == 'timeout':
                    self.assertEqual(result['aborted'], 1)

    def test_reload_allows_another_reaction_without_recognition(self):
        result = self.run_client(reload=True)
        self.assertEqual(sum(c['url'].endswith('/like-aggregate') for c in result['calls']), 2)
        self.assertEqual(result['storageReads'], 0)

    def test_invalid_read_is_rejected_and_print_failure_is_contained(self):
        self.assertTrue(self.run_client(mode='bad-read')['readFailed'])
        result = self.run_client(mode='print-sync')
        self.assertTrue(result['success'])
        self.assertEqual(sum(c['url'].endswith('/print-aggregate') for c in result['calls']), 1)

    def test_print_dialog_opens_even_when_telemetry_throws(self):
        harness = r"""
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('js/detail.js','utf8');
const section=source.slice(source.indexOf('printLink?.addEventListener("click"'),
                           source.indexOf('function renderLikeState('));
let click,printed=0,prevented=0;
const ctx={loadedEntryId:'sample',
  printLink:{href:'https://ausmalwiese.de/print.html?id=sample',getAttribute:()=>null,
             addEventListener:(name,fn)=>{click=fn;}},
  window:{ColoringStats:{trackPrint(){throw Error('telemetry failure');}}},
  startHtmlPrint(){printed++;},
};
vm.runInNewContext(section,ctx);
click({preventDefault(){prevented++;}});
console.log(JSON.stringify({printed,prevented}));
"""
        result = subprocess.run(['node','-e',harness], cwd=ROOT,
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertEqual(json.loads(result.stdout), {'printed':1,'prevented':1})


    def test_view_telemetry_exception_keeps_detail_and_print_available(self):
        # Execute the real detail hydration rather than only checking source text.
        harness = r"""
const fs = require('node:fs'), vm = require('node:vm');
const source = fs.readFileSync('js/detail.js','utf8');
const start = source.indexOf('async function loadDetail()');
const end = source.lastIndexOf('loadDetail();');
if (start < 0 || end <= start) throw Error('detail loader not found');
const title = {textContent:''}, description = {textContent:''}, printLink = {href:''};
const ctx = {
  console, process,
  window:{
    location:{search:'?id=sample'},
    ColoringStats:{trackView(){throw Error('blocked view telemetry');}},
  },
  document:{querySelector(){return null;},dispatchEvent(){}},
  URLSearchParams, encodeURIComponent,
  detailRoot:{setAttribute(){}}, detailTitle:title, detailDescription:description,
  detailCategory:null, detailCharacter:null, detailAge:null,
  detailDifficulty:null, detailPagesBadge:null, printLink,
  printLabel:null, pngLink:null, pngLabel:null, loadedEntryId:'',
  addVerifiedDetailCanonical(){}, markMissingDetailNoindex(){},
  entryPages(entry){return [{preview:entry.preview,print:entry.print}];},
  setAction(link,url){if(link) link.href=url;},
  renderPageSwitcher(){}, selectPage(){}, hydrateLikeState:async()=>{},
  fetch:async()=>({ok:true,json:async()=>[{
    id:'sample',title:'Beispiel',category:'tiere',age:'3-6',difficulty:'easy',
    preview:'/media/sample/preview.webp',print:'/media/sample/print.png'
  }]}),
};
vm.runInNewContext(source.slice(start,end) +
  '\nloadDetail().then(()=>console.log(JSON.stringify({title:detailTitle.textContent,' +
  'print:printLink.href,status:detailDescription.textContent}))).catch(e=>{console.error(e);process.exitCode=1;});',
  ctx);
"""
        result = subprocess.run(['node', '-e', harness], cwd=ROOT, text=True,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        data = json.loads(result.stdout)
        self.assertEqual(data['title'], 'Beispiel')
        self.assertEqual(data['print'], 'print.html?id=sample')
        self.assertIn('A4-Druck', data['status'])


if __name__ == '__main__':
    unittest.main()
