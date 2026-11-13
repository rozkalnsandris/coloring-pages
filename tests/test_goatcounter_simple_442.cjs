"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const source = fs.readFileSync(path.join(__dirname, "../js/goatcounter-simple.js"), "utf8");

function nodeEl() {
  return {
    hidden: true,
    addEventListener(name, fn) { this[name] = fn; },
  };
}

function mount({choice="", pathname="/", search="", hostname="ausmalwiese.de", referrer=""}={}) {
  const loaded=[];
  const dispatched=[];
  const storage=new Map();
  if (choice) storage.set("ausmalwiese.analytics-consent.v1", choice);
  const tag={getAttribute(k){return k === "data-goatcounter-simple" ? "consent" : null;}};
  const panel=nodeEl(), allow=nodeEl(), deny=nodeEl(), settings=nodeEl();
  const page={
    referrer,
    querySelector(s) {
      return ({
        "script[data-goatcounter-simple]": tag,
        "[data-analytics-consent]": panel,
        "[data-analytics-allow]": allow,
        "[data-analytics-deny]": deny,
        "[data-analytics-settings]": settings,
      })[s] || null;
    },
    createElement(){return {addEventListener(name,fn){this[name]=fn;}};},
    head:{append(e){loaded.push(e);}},
  };
  const origin="https://" + hostname;
  const location={hostname,pathname,search,origin};
  const window={
    location,
    localStorage:{
      getItem(k){return storage.has(k) ? storage.get(k) : null;},
      setItem(k,v){storage.set(k,String(v));},
    },
  };
  vm.runInNewContext(source,{window,document:page,location,URL,URLSearchParams});
  function activate(filter=false){
    assert.equal(loaded.length,1);
    window.goatcounter.get_data=(data)=>({...data,q:location.search});
    window.goatcounter.count=(data)=>dispatched.push(window.goatcounter.get_data(data));
    window.goatcounter.filter=()=>filter;
    loaded[0].load();
  }
  return {window,loaded,dispatched,storage,panel,allow,deny,settings,activate};
}

{
  const x=mount();
  assert.equal(x.loaded.length,0, "No external analytics before consent");
  assert.equal(x.panel.hidden,false);
  assert.equal(x.settings.hidden,true);
  assert.equal(x.window.goatcounter,undefined);
  x.deny.click();
  assert.equal(x.storage.get("ausmalwiese.analytics-consent.v1"),"denied");
  assert.equal(x.loaded.length,0, "Deny must never load count.v5.js");
  assert.equal(x.panel.hidden,true);
  assert.equal(x.settings.hidden,false);
}
{
  const x=mount({choice:"denied"});
  assert.equal(x.loaded.length,0);
  assert.equal(x.panel.hidden,true);
  x.settings.click();
  assert.equal(x.panel.hidden,false, "Preference must be reopenable");
}
{
  const x=mount({referrer:"https://example.org/sensitive?token=hello"});
  x.allow.click();
  assert.equal(x.storage.get("ausmalwiese.analytics-consent.v1"),"granted");
  assert.equal(x.loaded.length,1);
  assert.equal(x.loaded[0].src,"https://gc.zgo.at/count.v5.js");
  assert.equal(x.loaded[0].integrity,"sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ");
  assert.equal(x.window.goatcounter.endpoint,"https://ausmalwiese.de/count");
  x.activate();
  assert.equal(x.dispatched.length,1);
  assert.equal(x.dispatched[0].path,"/");
  assert.equal(x.dispatched[0].referrer,"https://example.org");
  assert.equal(x.dispatched[0].q,"");
}
{
  const x=mount({choice:"granted",pathname:"/detail.html",search:"?id=1234567&private=redacted",referrer:"https://other.com/foo?email=test"});
  assert.equal(x.loaded.length,0, "No analytics request before a valid detail event");
  x.window.GoatCounterSimple.detail("bad-id","Ignored");
  assert.equal(x.loaded.length,0);
  x.window.GoatCounterSimple.detail("1234567","Hund mit Hut");
  assert.equal(x.loaded.length,1);
  x.activate();
  assert.equal(x.dispatched.length,1);
  assert.equal(x.dispatched[0].path,"/ausmalbild/1234567");
  assert.equal(x.dispatched[0].title,"Hund mit Hut");
  assert.equal(x.dispatched[0].referrer,"https://other.com");
  assert.equal(x.dispatched[0].q,"");
}
{
  const x=mount({choice:"granted",pathname:"/detail.html",search:"?utm_source=instagram&utm_medium=social&utm_campaign=profile"});
  x.window.GoatCounterSimple.detail("7654321","Katze");
  x.activate();
  assert.equal(x.dispatched[0].referrer,"Instagram profile");
  assert.equal(x.dispatched[0].q,"?utm_source=instagram&utm_medium=social&utm_campaign=profile");
}
{
  const x=mount({choice:"granted",search:"?utm_source=instagram&utm_medium=social&utm_campaign=story&utm_campaign=private&token=secret"});
  x.activate();
  assert.equal(x.dispatched[0].q,"");
  assert.ok(!JSON.stringify(x.dispatched[0]).includes("secret"));
}
{
  const x=mount({choice:"granted",pathname:"/kita",search:"?private=redacted"});
  assert.equal(x.loaded.length,1, "Kita hub must queue only after prior consent");
  x.activate();
  assert.equal(x.dispatched.length,1);
  assert.equal(x.dispatched[0].path,"/kita");
  assert.equal(x.dispatched[0].title,"Kita & Vorschule");
  assert.equal(x.dispatched[0].q,"");
  assert.ok(!JSON.stringify(x.dispatched[0]).includes("redacted"));
}
{
  const x=mount({choice:"granted",pathname:"/kita/herbst"});
  assert.equal(x.loaded.length,1);
  x.activate();
  assert.equal(x.dispatched[0].path,"/kita/herbst");
  assert.equal(x.dispatched[0].title,"Herbst – 5 Aktivitäten");
}
{
  const x=mount({choice:"granted",pathname:"/kita/private"});
  assert.equal(x.loaded.length,0, "Kita-like paths outside the exact allowlist must not track");
  x.window.GoatCounterSimple.kita("/kita?private=x");
  assert.equal(x.loaded.length,0);
}
{
  const x=mount({pathname:"/kita"});
  assert.equal(x.loaded.length,0, "Kita must not load external analytics before consent");
  x.allow.click();
  assert.equal(x.loaded.length,1);
  x.activate();
  assert.equal(x.dispatched[0].path,"/kita");
}
{
  const x=mount({choice:"granted",hostname:"preview.ausmalwiese.de"});
  assert.equal(x.loaded.length,0, "Only production hosts may initialize analytics");
  assert.equal(x.window.GoatCounterSimple,undefined);
}
console.log("goatcounter-simple #442 consent: PASS");
