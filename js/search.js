(() => {
  "use strict";

  function normalizeGerman(value) {
    return String(value ?? "")
      .trim()
      .toLocaleLowerCase("de")
      .normalize("NFC")
      .replaceAll("ä", "ae")
      .replaceAll("ö", "oe")
      .replaceAll("ü", "ue")
      .replaceAll("ß", "ss")
      .replace(/\s+/g, " ");
  }

  function tokens(value) {
    const normalized = normalizeGerman(value);
    return normalized ? normalized.split(" ") : [];
  }

  function topicTerms(topicIds, registry) {
    if (!Array.isArray(topicIds) || !Array.isArray(registry)) return [];
    const byId = new Map(registry.map((topic) => [topic?.id, topic]));
    const terms = [];
    for (const id of topicIds) {
      const topic = byId.get(id);
      if (!topic) continue;
      terms.push(topic.id, topic.label);
      if (Array.isArray(topic.legacy_terms)) terms.push(...topic.legacy_terms);
    }
    return terms.filter((value) => typeof value === "string" && value.trim());
  }

  function matches(query, fields) {
    const queryTokens = tokens(query);
    if (!queryTokens.length) return true;
    const values = Array.isArray(fields) ? fields : [fields];
    const haystack = normalizeGerman(values.filter((value) => value != null).join(" "));
    return queryTokens.every((token) => haystack.includes(token));
  }

  globalThis.AusmalSearch = Object.freeze({
    normalizeGerman,
    tokens,
    topicTerms,
    matches,
  });
})();
