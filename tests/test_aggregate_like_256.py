"""Execute the actual Worker route against an offline SQLite-backed D1 adapter.

No Cloudflare access. The adapter models documented transactional batch behavior;
it does not certify real D1 deployment or the global effectiveness of rate limits.
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r"""
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
const fixture = JSON.parse(process.argv[1]);
const source = fs.readFileSync('cloudflare/stats-worker.js','utf8');
const {default:worker} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const queries = [], limits = [];
let batches = 0;
const sqlite = `
import json,os,sqlite3,sys
db=sqlite3.connect(os.environ['CP_TEST_DB'])
db.row_factory=sqlite3.Row
statements=json.load(sys.stdin)
results=[]
try:
 with db:
  for stmt in statements:
   cur=db.execute(stmt['sql'],stmt['args'])
   rows=[dict(row) for row in cur.fetchall()] if cur.description else []
   results.append({'success':True,'meta':{'changes':max(0,cur.rowcount)},'results':rows})
 print(json.dumps(results))
finally:
 db.close()
`;
const env = {DB:{
  prepare(sql) {return {bind(...args) {return {sql,args};}};},
  async batch(statements) {
    batches++;
    queries.push(...statements);
    if (fixture.dbMode === 'throw') throw Error('private-database-detail');
    const p = spawnSync(process.env.CP_TEST_PYTHON,['-c',sqlite],{
      input:JSON.stringify(statements),encoding:'utf8',env:process.env});
    if (p.status !== 0) throw Error('private-database-detail');
    const result = JSON.parse(p.stdout);
    if (fixture.dbMode === 'missing') return undefined;
    if (fixture.dbMode === 'partial') return result.slice(0,1);
    if (fixture.dbMode === 'failed') result[0].success=false;
    if (fixture.dbMode === 'unknownChanges') delete result[0].meta.changes;
    if (fixture.dbMode === 'emptyRows') result[1].results=[];
    if (fixture.dbMode === 'badCount') result[1].results[0].like_count=-1;
    return result;
  },
}};
if (!fixture.noLimiter) env.RATE_LIMITER = {async limit({key}) {
  limits.push(key);
  if (fixture.limitError) throw Error('private-limiter-detail');
  return {success:fixture.limited !== true};
}};
const host=fixture.host || 'https://ausmalwiese.de';
const headers = new Headers({
  'origin':host,'sec-fetch-site':'same-origin','content-type':'application/json',
  'CF-Connecting-IP':'192.0.2.5',...fixture.headers,
});
for (const name of fixture.removeHeaders || []) headers.delete(name);
const method=fixture.method || 'POST';
let body=fixture.raw === undefined ? JSON.stringify(fixture.body || {page_id:'sample'}) : fixture.raw;
if (fixture.stream) {
  const bytes=new TextEncoder().encode(body);
  body=new ReadableStream({start(controller) {
    for(let i=0;i<bytes.length;i+=13) controller.enqueue(bytes.slice(i,i+13));
    controller.close();
  }});
}
const request=new Request(host + '/api/stats/like-aggregate' + (fixture.query || ''),{
  method,headers,...(method==='GET'?{}:{body,duplex:'half'}),
});
const response=await worker.fetch(request,env);
console.log(JSON.stringify({status:response.status,data:await response.json(),
  headers:Object.fromEntries(response.headers),queries,limits,batches}));
"""


class AggregateLikeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'stats.sqlite'
        self.db = sqlite3.connect(self.path)
        self.db.executescript((ROOT / 'cloudflare/stats-schema.sql').read_text())

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def request(self, **fixture):
        self.db.commit()
        env = dict(os.environ, CP_TEST_DB=str(self.path), CP_TEST_PYTHON=sys.executable)
        result = subprocess.run(
            ['node', '--input-type=module', '-e', HARNESS, json.dumps(fixture)],
            cwd=ROOT, env=env, text=True, capture_output=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        return json.loads(result.stdout)

    def scalar(self, query):
        return self.db.execute(query).fetchone()[0]

    def test_new_page_and_repeated_reactions_are_totals_not_unique_people(self):
        first = self.request()
        self.assertEqual(first['status'], 201)
        self.assertEqual(first['data'], {
            'page_id':'sample', 'reacted':True, 'like_count':1, 'print_count':0,
        })
        self.assertEqual(self.request()['data']['like_count'], 2)
        self.assertEqual(self.scalar('SELECT count(*) FROM likes'), 0)
        self.assertEqual(self.scalar('SELECT count(*) FROM like_cookie_sessions'), 0)
        self.assertNotIn('set-cookie', first['headers'])
        self.assertEqual(first['headers']['cache-control'], 'no-store')
        self.assertEqual(first['limits'], ['aggregate-like:192.0.2.5'])
        self.assertEqual([q['args'] for q in first['queries']], [['sample'], ['sample']])

    def test_existing_active_archived_and_print_totals_survive(self):
        self.db.execute("INSERT INTO likes(page_id,visitor_hash) VALUES ('sample','legacy')")
        self.db.execute("UPDATE page_stats SET print_count=7 WHERE page_id='sample'")
        self.db.execute("INSERT INTO archived_like_totals VALUES ('sample',4)")
        result = self.request(headers={'cookie':'__Secure-aw-like-v1=untrusted'})
        self.assertEqual(result['data']['like_count'], 6)
        self.assertEqual(result['data']['print_count'], 7)
        self.assertEqual(self.scalar('SELECT count(*) FROM likes'), 1)
        self.assertEqual(self.scalar('SELECT like_count FROM archived_like_totals'), 4)
        self.db.execute("DELETE FROM likes WHERE visitor_hash='legacy'")
        self.assertEqual(self.scalar('SELECT like_count FROM page_stats'), 1)
        self.assertNotIn('untrusted', json.dumps(result))

    def test_all_three_hosts_require_exact_same_origin_json(self):
        for host in ('https://ausmalwiese.de','https://www.ausmalwiese.de',
                     'https://coloring.rozkalns.net'):
            with self.subTest(host=host):
                self.assertEqual(self.request(host=host)['status'], 201)
        for fixture in (
            {'host':'https://evil.example'},
            {'headers':{'origin':'https://www.ausmalwiese.de'}},
            {'headers':{'sec-fetch-site':'cross-site'}},
            {'headers':{'content-type':'text/plain'}},
            {'removeHeaders':['origin']},
            {'removeHeaders':['sec-fetch-site']},
        ):
            with self.subTest(fixture=fixture):
                result = self.request(**fixture)
                self.assertEqual(result['status'], 403)
                self.assertEqual(result['batches'], 0)
        self.assertEqual(self.request(method='GET')['status'], 404)

    def test_invalid_bodies_and_identifiers_never_reach_d1(self):
        for body in ({'page_id':'sample','visitor_id':'old-id'},
                     {'page_id':'sample','liked':True}, {'other':'sample'},
                     {'page_id':''}, {'page_id':'a'*81},
                     {'page_id':"sample'; DROP TABLE likes;--"}, [1], 'sample'):
            with self.subTest(body=body):
                result = self.request(body=body)
                self.assertEqual(result['status'], 400)
                self.assertEqual(result['batches'], 0)
        for fixture in ({'raw':'null'}, {'raw':'{'}, {'raw':''},
                        {'raw':' '*257+'{"page_id":"sample"}','stream':True},
                        {'headers':{'content-length':'257'}},
                        {'headers':{'content-length':'invalid'}},
                        {'query':'?visitor_id=old-id'}):
            with self.subTest(fixture=fixture):
                result = self.request(**fixture)
                self.assertEqual(result['status'], 400)
                self.assertEqual(result['queries'], [])

    def test_missing_or_failed_abuse_control_is_fail_closed(self):
        for fixture, status in (({'noLimiter':True},503),
                                ({'removeHeaders':['CF-Connecting-IP']},503),
                                ({'limited':True},429), ({'limitError':True},503)):
            with self.subTest(fixture=fixture):
                result = self.request(**fixture)
                self.assertEqual(result['status'], status)
                self.assertEqual(result['batches'], 0)
                self.assertNotIn('private-', json.dumps(result['data']))

    def test_unknown_db_outcome_is_not_success_or_automatically_retried(self):
        for mode in ('throw','missing','partial','failed','unknownChanges','emptyRows','badCount'):
            with self.subTest(mode=mode):
                result = self.request(dbMode=mode)
                self.assertEqual(result['status'], 503)
                self.assertEqual(result['data'], {'error':'like_unconfirmed'})
                self.assertEqual(result['batches'], 1)

    def test_failed_read_in_transaction_rolls_back_increment(self):
        self.db.execute("INSERT INTO page_stats VALUES ('sample',7,8,datetime('now'))")
        self.db.execute('DROP TABLE archived_like_totals')
        result = self.request()
        self.assertEqual(result['status'], 503)
        self.assertEqual(self.scalar('SELECT like_count FROM page_stats'), 8)


if __name__ == '__main__':
    unittest.main()
