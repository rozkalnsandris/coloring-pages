(() => {
  "use strict";

  const ID_RE = /^\d{7}$/;
  const CATEGORY_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

  function categoriesFor(entry) {
    const primary = typeof entry?.category === "string" && CATEGORY_RE.test(entry.category) ? entry.category : "";
    const assigned = entry?.categories;
    if (Array.isArray(assigned) && assigned.length > 0 && assigned[0] === primary &&
        assigned.every((id) => typeof id === "string" && CATEGORY_RE.test(id)) &&
        new Set(assigned).size === assigned.length) {
      return assigned;
    }
    return primary ? [primary] : [];
  }

  function usable(entry) {
    const id = entry?.id;
    return typeof id === "string" && ID_RE.test(id) &&
      typeof entry.title === "string" && entry.title.trim() &&
      entry.thumb === "/media/" + id + "/thumb.webp";
  }

  function choose(catalog, limit = 4) {
    if (!Array.isArray(catalog) || !Number.isSafeInteger(limit) || limit < 1) return [];
    const selected = [];
    const selectedIds = new Set();
    const categories = new Set();
    const usableEntries = [];

    for (const entry of catalog) {
      if (!usable(entry) || selectedIds.has(entry.id)) continue;
      usableEntries.push(entry);
      const category = categoriesFor(entry)[0] || "";
      if (!category || categories.has(category)) continue;
      categories.add(category);
      selectedIds.add(entry.id);
      selected.push(entry);
      if (selected.length === limit) return selected;
    }

    for (const entry of usableEntries) {
      if (selectedIds.has(entry.id)) continue;
      selectedIds.add(entry.id);
      selected.push(entry);
      if (selected.length === limit) break;
    }
    return selected;
  }

  globalThis.AusmalDiscoveryPicks = Object.freeze({ choose });
})();
