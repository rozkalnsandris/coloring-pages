(() => {
  "use strict";

  const SCHEMA = "rozkalns.coloring-pages.topics.v2";
  const ID_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

  function parseMonthDay(value) {
    const match = /^(\d{2})-(\d{2})$/.exec(String(value || ""));
    if (!match) return null;
    const month = Number(match[1]);
    const day = Number(match[2]);
    if (month < 1 || month > 12 || day < 1 || day > 31) return null;
    return month * 100 + day;
  }

  function parse(payload) {
    if (!payload || payload.schema !== SCHEMA ||
        !Number.isSafeInteger(payload.revision) || payload.revision < 1 ||
        !Array.isArray(payload.topics) || payload.topics.length < 1 || payload.topics.length > 128) {
      throw new Error("invalid topic registry");
    }

    const ids = new Set();
    for (const topic of payload.topics) {
      if (!topic || typeof topic.id !== "string" || !ID_RE.test(topic.id) ||
          ids.has(topic.id) ||
          typeof topic.label !== "string" || !topic.label.trim() ||
          typeof topic.icon !== "string" ||
          !["seasonal", "evergreen"].includes(topic.kind) ||
          !Array.isArray(topic.legacy_terms) ||
          topic.legacy_terms.some((term) => typeof term !== "string") ||
          (topic.kind === "seasonal" &&
            (!parseMonthDay(topic.active_from) || !parseMonthDay(topic.active_to)))) {
        throw new Error("invalid topic registry");
      }
      ids.add(topic.id);
    }

    return payload.topics;
  }

  function toMap(payload) {
    return new Map(parse(payload).map((topic) => [topic.id, topic]));
  }

  globalThis.AusmalTopicRegistry = Object.freeze({
    schema: SCHEMA,
    parse,
    toMap,
  });
})();
