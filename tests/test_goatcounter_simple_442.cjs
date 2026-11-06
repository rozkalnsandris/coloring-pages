"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const source = fs.readFileSync(path.join(__dirname, "../js/goatcounter-simple.js"), "utf8");

function mount({enabled="off", pathname="/", search="", hostname="ausmalwiese.de", referrer=""}={}) {
  const loaded=[];
  const dispatched=[];
  const el={getAttribute(k){return k === "data-goatcounter-simple" ? enabled : null;}};
  const page={
    referrer,
    querySelector(s){return s === "script[data-goatcounter-simple]" ? el : null;},
    createElement(){return {addEventListener(name,fn){this[name]=fn;}};},
    head:{append(e){loaded.push(e);}},
  };
  const origin="https://" + hostname;
  const location={hostname,pathname,search,origin};
  const window={location};
  vm.runInNewContext(source,{window,document:page,location,URL,URLSearchParams});
  function activate(filter=false){
    assert.equal(loaded.length,1);
    // Pinned count.v5.js merges raw location.search as q independently of path.
    window.goatcounter.get_data=(data)=>({...data,q:location.search});
    window.goatcounter.count=(data)=>dispatched.push(window.goatcounter.get_data(data));
    window.goatcounter.filter=()=>filter;
    loaded[0].load();
  }
  return {window,loaded,dispatched,activate};
}

{
  const x=mount();
  assert.equal(x.loaded.length,0, "Default off must load no external script");
  assert.equal(x.window.goatcounter,undefined);
}
{
  const x=mount({enabled:"enabled",hostname:"preview.ausmalwiese.de"});
  assert.equal(x.loaded.length,0, "Only production hosts may count");
}
{
  const x=mount({enabled:"enabled",referrer:"https://example.org/sensitive?token=hello"});
  assert.equal(x.dispatched.length,0, "Pending event must wait for count.js");
  assert.equal(x.loaded[0].src,"https://gc.zgo.at/count.v5.js");
  assert.equal(x.loaded[0].integrity,"sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ");
  assert.equal(x.window.goatcounter.endpoint,"https://ausmalwiese.de/count");
  assert.equal(x.window.goatcounter.no_onload,true);
  x.activate();
  assert.equal(x.dispatched.length,1);
  assert.equal(x.dispatched[0].path,"/");
  assert.equal(x.dispatched[0].referrer,"https://example.org");
  assert.equal(x.dispatched[0].q,"");
  x.window.GoatCounterSimple.home();
  assert.equal(x.dispatched.length,1, "No duplicate home hits");
}
{
  const x=mount({enabled:"enabled",pathname:"/detail.html",search:"?id=1234567&private=redacted",referrer:"https://other.com/foo?email=test"});
  x.window.GoatCounterSimple.detail("bad-id","Ignored");
  x.window.GoatCounterSimple.detail("1234567","Hund mit Hut");
  x.activate();
  assert.equal(x.dispatched.length,1);
  assert.equal(x.dispatched[0].path,"/ausmalbild/1234567");
  assert.equal(x.dispatched[0].title,"Hund mit Hut");
  assert.equal(x.dispatched[0].referrer,"https://other.com");
  assert.equal(x.dispatched[0].q,"", "Never forward detail IDs or private URL parameters");
  x.window.GoatCounterSimple.detail("7654321","Ignored twice");
  assert.equal(x.dispatched.length,1);
}
{
  const x=mount({enabled:"enabled",pathname:"/detail.html",search:"?utm_source=instagram&utm_medium=social&utm_campaign=reel"});
  x.window.GoatCounterSimple.detail("7654321","Katze");
  x.activate(true);
  assert.equal(x.dispatched.length,0,"Respect GoatCounter's bot/owner filtering");
}
{
  const x=mount({enabled:"enabled",pathname:"/detail.html",search:"?utm_source=instagram&utm_medium=social&utm_campaign=profile"});
  x.window.GoatCounterSimple.detail("7654321","Katze");
  x.activate();
  assert.equal(x.dispatched[0].referrer,"Instagram profile");
  assert.equal(x.dispatched[0].q,"?utm_source=instagram&utm_medium=social&utm_campaign=profile");
}
{
  const x=mount({enabled:"enabled",search:"?id=1234567&utm_source=instagram&utm_medium=social&utm_campaign=reel&email=private"});
  x.activate();
  assert.equal(x.dispatched.length,1);
  assert.equal(x.dispatched[0].referrer,"Instagram reel");
  assert.equal(x.dispatched[0].q,"?utm_source=instagram&utm_medium=social&utm_campaign=reel");
  assert.ok(!JSON.stringify(x.dispatched[0]).includes("private"));
}
{
  const x=mount({enabled:"enabled",search:"?utm_source=instagram&utm_medium=social&utm_campaign=story&utm_campaign=private&token=secret"});
  x.activate();
  assert.equal(x.dispatched[0].q,"", "Duplicate campaign keys must not be forwarded");
  assert.ok(!JSON.stringify(x.dispatched[0]).includes("secret"));
}
{
  const x=mount({enabled:"enabled",search:"?utm_campaign=private&token=secret"});
  x.activate();
  assert.equal(x.dispatched[0].q,"", "Unknown campaigns must not be forwarded");
}
{
  const x=mount({enabled:"enabled",search:"?utm_source=instagram&utm_medium=social&utm_campaign=story"});
  x.loaded[0].load(); // Missing official get_data(): fail closed without a hit.
  assert.equal(x.dispatched.length,0);
}
console.log("goatcounter-simple #442: PASS");
