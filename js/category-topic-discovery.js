(() => {
  "use strict";

  const ID_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  const SHA256_RE = /^[0-9a-f]{64}$/;
  const SCHEMA = "rozkalns.coloring-pages.category-topics.v1";
  const TOPIC_ROUTE_OVERRIDES = Object.freeze({
    herbst: "/herbst",
  });

  function fail(message) {
    throw new Error(message);
  }

  function validateProjection(doc, {
    categoryRevision,
    topicRevision,
    categorySha256,
    topicSha256,
    categories,
    topics,
  }) {
    const required = [
      "schema",
      "revision",
      "category_revision",
      "topic_revision",
      "category_sha256",
      "topic_sha256",
      "source_links_sha256",
      "links",
    ];

    if (!doc || typeof doc !== "object" || Array.isArray(doc) ||
        Object.keys(doc).sort().join(",") !== required.slice().sort().join(",") ||
        doc.schema !== SCHEMA ||
        !Number.isSafeInteger(doc.revision) || doc.revision < 1 ||
        !Number.isSafeInteger(doc.category_revision) || doc.category_revision < 1 ||
        !Number.isSafeInteger(doc.topic_revision) || doc.topic_revision < 1 ||
        doc.category_revision !== categoryRevision ||
        doc.topic_revision !== topicRevision ||
        typeof doc.category_sha256 !== "string" || !SHA256_RE.test(doc.category_sha256) ||
        typeof doc.topic_sha256 !== "string" || !SHA256_RE.test(doc.topic_sha256) ||
        typeof doc.source_links_sha256 !== "string" || !SHA256_RE.test(doc.source_links_sha256) ||
        doc.category_sha256 !== categorySha256 ||
        doc.topic_sha256 !== topicSha256 ||
        !Array.isArray(doc.links) || doc.links.length > 512) {
      fail("invalid category-topic projection");
    }

    const categoryIds = new Set(categories.map((item) => item.id));
    const topicById = new Map(topics.map((item) => [item.id, item]));
    const byCategory = new Map();
    let previous = "";

    for (const row of doc.links) {
      if (!row || typeof row !== "object" || Array.isArray(row) ||
          Object.keys(row).sort().join(",") !== "category,topic" ||
          typeof row.category !== "string" || !ID_RE.test(row.category) ||
          typeof row.topic !== "string" || !ID_RE.test(row.topic) ||
          !categoryIds.has(row.category) || !topicById.has(row.topic)) {
        fail("invalid category-topic link");
      }

      const topic = topicById.get(row.topic);
      if ((topic.kind === "seasonal") !== (row.category === "jahreszeiten")) {
        fail("incompatible category-topic link");
      }

      const key = `${row.category}\u0000${row.topic}`;
      if (previous && key <= previous) fail("unordered or duplicate category-topic link");
      previous = key;

      if (!byCategory.has(row.category)) byCategory.set(row.category, []);
      byCategory.get(row.category).push(topic);
    }

    return byCategory;
  }

  function topicHref(topicId) {
    return TOPIC_ROUTE_OVERRIDES[topicId] ||
      `index.html?topic=${encodeURIComponent(topicId)}#neu`;
  }

  function hasDedicatedTopicRoute(topicId) {
    return Object.prototype.hasOwnProperty.call(TOPIC_ROUTE_OVERRIDES, topicId);
  }

  globalThis.AusmalCategoryDiscovery = Object.freeze({
    schema: SCHEMA,
    validateProjection,
    topicHref,
    hasDedicatedTopicRoute,
  });
})();
