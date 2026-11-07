import test from "node:test";
import assert from "node:assert/strict";
import { loadLegacyIdAliases, translateLegacyBasketIds, validateLegacyIdAliases } from "../js/legacy-id-aliases.mjs";
function doc(aliases=[{old_id:"legacy-1",new_id:"1234567"}]) { return {schema:"rozkalns.coloring-pages.legacy-id-aliases.v1",issue:457,source_catalog_sha256:"a".repeat(64),source_catalog_count:10,source_legacy_count:aliases.length,source_plan_manifest_sha256:"b".repeat(64),aliases_sha256:"c".repeat(64),aliases}; }
const one=(id)=>({id,title:"x",print:`/media/${id}/print.png`});
test("alias maps before pruning only when new target exists",()=>{assert.deepEqual(translateLegacyBasketIds(["legacy-1"],[one("legacy-1")],doc()),{ids:["legacy-1"],changed:false});assert.deepEqual(translateLegacyBasketIds(["legacy-1"],[one("1234567")],doc()),{ids:["1234567"],changed:true});});
test("old and new stored together deduplicate",()=>{assert.deepEqual(translateLegacyBasketIds(["legacy-1","1234567","keep-1"],[one("1234567"),one("keep-1")],doc()),{ids:["1234567","keep-1"],changed:true});});
test("unknown aliases and duplicate target catalogue IDs stay fail-closed",()=>{assert.deepEqual(translateLegacyBasketIds(["unknown"],[one("1234567")],doc()),{ids:["unknown"],changed:false});assert.deepEqual(translateLegacyBasketIds(["legacy-1"],[one("1234567"),one("1234567")],doc()),{ids:["legacy-1"],changed:false});});
test("malformed alias documents are rejected",()=>{const bad=[{...doc(),source_legacy_count:2},doc([{old_id:"1234567",new_id:"7654321"}]),doc([{old_id:"../x",new_id:"1234567"}]),doc([{old_id:"legacy-1",new_id:"123"}]),doc([{old_id:"legacy-1",new_id:"1234567"},{old_id:"legacy-1",new_id:"7654321"}]),doc([{old_id:"legacy-1",new_id:"1234567"},{old_id:"legacy-2",new_id:"1234567"}])];for(const value of bad) assert.throws(()=>validateLegacyIdAliases(value),TypeError);});
test("404 means pre-cutover compatibility is inactive",async()=>{assert.equal(await loadLegacyIdAliases(async()=>({status:404,ok:false})),null);});
test("non-404 fetch failure is not treated as empty aliases",async()=>{await assert.rejects(loadLegacyIdAliases(async()=>({status:503,ok:false})),/unavailable/);});
