// Offline API contract: executes the real Worker, never Cloudflare infrastructure.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash,webcrypto} from 'node:crypto';
import vm from 'node:vm';

if (!globalThis.crypto) globalThis.crypto=webcrypto;
const bytes=readFileSync(new URL('../cloudflare/stats-worker.js',import.meta.url));
const worker=(await import('data:text/javascript;base64,'+bytes.toString('base64'))).default;
const SITE='https://coloring.rozkalns.net';
const SECRET='offline-test-only-'+ 'x'.repeat(48);

function fakeEnv({allow=true,secret=SECRET}={}){
  const state={queries:[],writes:[],rateKeys:[],likeHashes:new Set(),allow};
  const DB={
    prepare(sql){
      return {bind(...args){
        state.queries.push({sql,args});
        return {
          async first(){
            if(sql.includes('FROM page_stats WHERE page_id'))return {print_count:4,like_count:2};
            if(sql.includes('FROM likes WHERE page_id'))
              return state.likeHashes.has(args[1])?{liked:1}:null;
            throw Error('Unexpected test SQL: '+sql);
          },
          async run(){throw Error('Unexpected test SQL write: '+sql);}
        };
      }};
    },
    async batch(statements){
      state.writes.push(...statements);
      return statements.map(()=>({success:true}));
    }
  };
  return {state,env:{
    PUBLIC_ORIGIN:SITE,VISITOR_HMAC_KEY:secret,DB,
    RATE_LIMITER:{async limit({key}){state.rateKeys.push(key);return {success:state.allow};}}
  }};
}
function makeRequest(path,{method='GET',body,origin=SITE,ip='203.0.113.10'}={}){
  const headers={'CF-Connecting-IP':ip,'Sec-Fetch-Site':'same-origin'};
  if(origin!==null)headers.Origin=origin;
  if(body!==undefined)headers['Content-Type']='application/json';
  const opts={method,headers};
  if(body!==undefined)opts.body=JSON.stringify(body);
  return new Request(SITE+path,opts);
}
async function api(env,path,options){
  const response=await worker.fetch(makeRequest(path,options),env);
  return {status:response.status,body:await response.json()};
}

test('new POST page status is read-only and works without visitor ID',async()=>{
  const {env,state}=fakeEnv();
  const x=await api(env,'/api/stats/page',{method:'POST',body:{page_id:'1234567',visitor_id:''}});
  assert.equal(x.status,200);
  assert.deepEqual(x.body,{page_id:'1234567',print_count:4,like_count:2,liked:false});
  assert.equal(state.queries.length,1);
  assert.equal(state.writes.length,0);
});
test('new POST and legacy GET check the same Like identity',async()=>{
  const {env,state}=fakeEnv();
  const visitor='visitor-001';
  const hashed=createHash('sha256').update(visitor).digest('hex');
  state.likeHashes.add(hashed);
  const modern=await api(env,'/api/stats/page',{method:'POST',body:{page_id:'1234567',visitor_id:visitor}});
  const legacy=await api(env,'/api/stats/page?page_id=1234567&visitor_id='+visitor);
  assert.equal(modern.status,200);
  assert.equal(legacy.status,200);
  assert.deepEqual(modern.body,legacy.body);
  assert.equal(modern.body.liked,true);
  assert.deepEqual(state.queries.filter(q=>q.sql.includes('FROM likes WHERE')).map(q=>q.args[1]),[hashed,hashed]);
  assert.equal(state.writes.length,0);
});
test('page lookup rejects invalid and cross-origin POST without D1 reads',async()=>{
  const {env,state}=fakeEnv();
  assert.equal((await api(env,'/api/stats/page',{method:'POST',body:{page_id:'1234567'},origin:'https://other.example'})).status,403);
  assert.equal((await api(env,'/api/stats/page',{method:'POST',body:{page_id:'!!!'}})).status,400);
  assert.equal((await api(env,'/api/stats/page',{method:'POST',body:{page_id:'1234567',visitor_id:'x'}})).status,400);
  assert.equal(state.queries.length,0);
  assert.equal(state.writes.length,0);
});
test('new ID-free print increments only aggregate counters and uses a daily HMAC rate key',async()=>{
  const {env,state}=fakeEnv();
  const a=await api(env,'/api/stats/print',{method:'POST',body:{page_id:'1234567'}});
  assert.equal(a.status,201);
  assert.deepEqual(a.body,{ok:true});
  assert.equal(state.writes.length,2);
  assert.deepEqual(state.queries.map(q=>q.args),[['1234567'],['1234567']]);
  assert.match(state.rateKeys[0],/^print:[a-f0-9]{64}$/);
  assert.ok(!state.rateKeys[0].includes('203.0.113.'));
  const b=await api(env,'/api/stats/print',{method:'POST',body:{page_id:'1234567'}});
  assert.equal(b.status,201);
  assert.equal(state.rateKeys[0],state.rateKeys[1]);
  await api(env,'/api/stats/print',{method:'POST',body:{page_id:'1234567'},ip:'203.0.113.11'});
  assert.notEqual(state.rateKeys[0],state.rateKeys[2]);
});
test('cached old client print payload remains accepted without binding raw visitor ID to D1',async()=>{
  const {env,state}=fakeEnv();
  const x=await api(env,'/api/stats/print',{method:'POST',body:{page_id:'1234567',visitor_id:'visitor-001'}});
  assert.equal(x.status,201);
  assert.deepEqual(state.queries.map(q=>q.args),[['1234567'],['1234567']]);
  assert.match(state.rateKeys[0],/^print:[a-f0-9]{64}$/);
});
test('invalid, forbidden, unconfigured and rate-limited prints do not write D1',async()=>{
  const cases=[
    {body:{page_id:'!'},status:400},
    {body:{page_id:'1234567'},origin:'https://other.example',status:403},
    {body:{page_id:'1234567'},ip:'',status:503},
    {body:{page_id:'1234567'},secret:'short',status:503},
    {body:{page_id:'1234567'},allow:false,status:429},
  ];
  for(const c of cases){
    const {env,state}=fakeEnv({secret:c.secret,allow:c.allow});
    const x=await api(env,'/api/stats/print',{method:'POST',body:c.body,origin:c.origin,ip:c.ip});
    assert.equal(x.status,c.status);
    assert.equal(state.writes.length,0);
  }
});
test('actual browser JS reads Like state with POST and does not persist an ID for Print',async()=>{
  const source=readFileSync(new URL('../js/stats.js',import.meta.url),'utf8');
  const calls=[],storage=new Map();
  let writes=0;
  const context={
    window:{},location:{pathname:'/test-only',search:''},
    URLSearchParams,Blob,crypto:webcrypto,
    navigator:{sendBeacon(){return false;}},
    localStorage:{
      getItem(key){return storage.get(key)||null;},
      setItem(key,value){writes++;storage.set(key,value);}
    },
    fetch(url,options){
      calls.push({url,options});
      return Promise.resolve({ok:true,json:async()=>({page_id:'1234567',liked:false})});
    },
  };
  vm.runInNewContext(source,context,{filename:'js/stats.js'});
  context.window.ColoringStats.trackPrint('1234567');
  assert.equal(writes,0);
  assert.equal(calls[0].url,'/api/stats/print');
  assert.deepEqual(JSON.parse(calls[0].options.body),{page_id:'1234567'});
  storage.set('coloring-pages-visitor-v1','visitor-001');
  await context.window.ColoringStats.getPage('1234567');
  assert.equal(calls[1].url,'/api/stats/page');
  assert.equal(calls[1].options.method,'POST');
  assert.deepEqual(JSON.parse(calls[1].options.body),{page_id:'1234567',visitor_id:'visitor-001'});
  assert.equal(writes,0);
});
