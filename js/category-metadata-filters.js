(() => {
  "use strict";

  const AGE_VALUES = new Set(["3-6", "4-8"]);
  const DIFFICULTY_VALUES = new Set(["easy", "normal", "detailed"]);

  function read(search = "") {
    const params = new URLSearchParams(search);
    const age = params.get("age");
    const difficulty = params.get("difficulty");
    return {
      age: AGE_VALUES.has(age) ? age : "",
      difficulty: DIFFICULTY_VALUES.has(difficulty) ? difficulty : "",
    };
  }

  function matches(entry, filters = {}) {
    return (!filters.age || entry?.age === filters.age) &&
      (!filters.difficulty || entry?.difficulty === filters.difficulty);
  }

  function hasActive(filters = {}) {
    return Boolean(filters.age || filters.difficulty);
  }

  function applyToUrl(url, filters = {}) {
    if (filters.age && AGE_VALUES.has(filters.age)) url.searchParams.set("age", filters.age);
    else url.searchParams.delete("age");
    if (filters.difficulty && DIFFICULTY_VALUES.has(filters.difficulty)) {
      url.searchParams.set("difficulty", filters.difficulty);
    } else {
      url.searchParams.delete("difficulty");
    }
    return url;
  }

  globalThis.AusmalCategoryMetadataFilters = Object.freeze({
    read,
    matches,
    hasActive,
    applyToUrl,
  });
})();
