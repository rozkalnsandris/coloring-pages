"use strict";

const assert = require("node:assert/strict");

(async () => {
  await import("../js/topic-registry.js");
  const api = globalThis.AusmalTopicRegistry;
  assert.ok(api, "topic registry helper must register globally");

  const fixture = {
    schema: "rozkalns.coloring-pages.topics.v2",
    revision: 2,
    topics: [
      {
        id: "bauernhof",
        label: "Bauernhof",
        icon: "🚜",
        kind: "evergreen",
        legacy_terms: ["bauernhof", "traktor"],
      },
      {
        id: "weihnachten",
        label: "Weihnachten",
        icon: "🎄",
        kind: "seasonal",
        active_from: "11-20",
        active_to: "12-26",
        legacy_terms: ["weihnacht", "rentier"],
      },
    ],
  };

  assert.deepEqual(api.parse(fixture).map((topic) => topic.id), ["bauernhof", "weihnachten"]);
  assert.equal(api.toMap(fixture).get("bauernhof").legacy_terms[1], "traktor");

  assert.throws(
    () => api.parse({ ...fixture, schema: "rozkalns.coloring-pages.topics.v1" }),
    /invalid topic registry/
  );
  assert.throws(
    () => api.parse({ ...fixture, revision: 0 }),
    /invalid topic registry/
  );
  assert.throws(
    () => api.parse({ ...fixture, topics: [...fixture.topics, { ...fixture.topics[0] }] }),
    /invalid topic registry/
  );
  assert.throws(
    () => api.parse({
      ...fixture,
      topics: [{ ...fixture.topics[1], active_from: "13-01" }],
    }),
    /invalid topic registry/
  );

  console.log("UI/UX #511 topics v2 registry parser: PASS");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
