"use strict";

const assert = require("node:assert/strict");
require("../js/search.js");

const search = globalThis.AusmalSearch;
assert.ok(search, "search helper must register globally");

assert.equal(search.normalizeGerman("Schäferhund"), "schaeferhund");
assert.equal(search.normalizeGerman("Schaeferhund"), "schaeferhund");
assert.equal(search.normalizeGerman("Fußball"), "fussball");
assert.equal(search.normalizeGerman("Gemüse"), "gemuese");

assert.equal(search.matches("Schäferhund", ["Deutscher Schaeferhund"]), true);
assert.equal(search.matches("Schaeferhund", ["Deutscher Schäferhund"]), true);
assert.equal(search.matches("bauernhof kuh", ["Kuh", "Bauernhof"]), true);
assert.equal(search.matches("bauernhof wal", ["Kuh", "Bauernhof"]), false);

const registry = [
  { id: "bauernhof", label: "Bauernhof", legacy_terms: ["traktor", "kuh", "ziege"] },
  { id: "gemuese", label: "Gemüse", legacy_terms: ["möhre", "moehre"] },
];
const farmTerms = search.topicTerms(["bauernhof"], registry);
assert.ok(farmTerms.includes("Bauernhof"));
assert.ok(farmTerms.includes("traktor"));
assert.equal(search.matches("Traktor", ["Kuh", ...farmTerms]), true);
assert.equal(search.matches("Gemüse", search.topicTerms(["gemuese"], registry)), true);
assert.equal(search.matches("Gemuese", search.topicTerms(["gemuese"], registry)), true);

console.log("Search helper #513: PASS");
