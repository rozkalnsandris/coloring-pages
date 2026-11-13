"use strict";

const assert = require("node:assert/strict");
require("../js/category-topic-discovery.js");

const api = globalThis.AusmalCategoryDiscovery;
assert.ok(api, "discovery helper must register globally");

const categories = [
  { id: "tiere", label: "Tiere" },
  { id: "fahrzeuge", label: "Fahrzeuge" },
  { id: "alphabet", label: "Alphabet" },
  { id: "lernen", label: "Lernen" },
  { id: "figuren", label: "Figuren" },
  { id: "jahreszeiten", label: "Jahreszeiten & Feste" },
  { id: "orte", label: "Orte" },
];
const topics = [
  { id: "bauernhof", label: "Bauernhof", icon: "🚜", kind: "evergreen" },
  { id: "wald", label: "Wald", icon: "🌲", kind: "evergreen" },
  { id: "herbst", label: "Herbst", icon: "🍂", kind: "seasonal" },
];
const hashes = {
  categoryRevision: 2,
  topicRevision: 2,
  categorySha256: "a".repeat(64),
  topicSha256: "b".repeat(64),
  categories,
  topics,
};

function projection(links) {
  return {
    schema: "rozkalns.coloring-pages.category-topics.v1",
    revision: 3,
    category_revision: 2,
    topic_revision: 2,
    category_sha256: "a".repeat(64),
    topic_sha256: "b".repeat(64),
    source_links_sha256: "c".repeat(64),
    links,
  };
}

const linked = api.validateProjection(projection([
  { category: "jahreszeiten", topic: "herbst" },
  { category: "lernen", topic: "wald" },
  { category: "orte", topic: "wald" },
  { category: "tiere", topic: "bauernhof" },
]), hashes);

assert.deepEqual(linked.get("lernen").map((topic) => topic.id), ["wald"]);
assert.deepEqual(linked.get("orte").map((topic) => topic.id), ["wald"]);
assert.deepEqual(linked.get("tiere").map((topic) => topic.id), ["bauernhof"]);
assert.equal(linked.has("fahrzeuge"), false, "zero-topic category stays empty");
assert.equal(api.topicHref("wald"), "index.html?topic=wald#neu");
assert.equal(api.topicHref("herbst"), "/herbst");
assert.equal(api.hasDedicatedTopicRoute("herbst"), true);
assert.equal(api.hasDedicatedTopicRoute("wald"), false);

assert.throws(() => api.validateProjection(projection([
  { category: "tiere", topic: "missing" },
]), hashes), /invalid category-topic link/);

assert.throws(() => api.validateProjection(projection([
  { category: "tiere", topic: "herbst" },
]), hashes), /incompatible category-topic link/);

assert.throws(() => api.validateProjection(projection([
  { category: "tiere", topic: "bauernhof" },
  { category: "tiere", topic: "bauernhof" },
]), hashes), /unordered or duplicate/);

assert.throws(() => api.validateProjection({
  ...projection([{ category: "tiere", topic: "bauernhof" }]),
  topic_sha256: "d".repeat(64),
}, hashes), /invalid category-topic projection/);

console.log("Managed Category-Topic discovery #507: PASS");
