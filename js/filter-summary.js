(() => {
  "use strict";

  const resultCount = document.querySelector("[data-result-count]");
  const activeFilters = document.querySelector("[data-active-filters]");
  const resetButton = document.querySelector("[data-reset-all-filters]");
  const searchInput = document.querySelector("#site-search");
  const ageFilter = document.querySelector("[data-filter-age]");
  const difficultyFilter = document.querySelector("[data-filter-difficulty]");
  const topicFilter = document.querySelector("[data-filter-topic]");

  function selectedCategoryLabel(categoryId) {
    const candidates = Array.from(document.querySelectorAll("[data-filter], [data-collection-filter]"));
    const match = candidates.find((item) => (item.dataset.filter || item.dataset.collectionFilter || "") === categoryId);
    if (!match) return categoryId;
    const label = match.querySelector(".category-subtopic-label, .category-group-name");
    return (label || match).textContent.trim();
  }

  function activeCategoryId() {
    const fromUrl = new URLSearchParams(location.search).get("category");
    if (fromUrl) return fromUrl;
    const active = Array.from(document.querySelectorAll("[data-filter], [data-collection-filter]")).find((item) => item.classList.contains("is-active"));
    return active ? (active.dataset.filter || active.dataset.collectionFilter || "") : "";
  }

  function labels() {
    const values = [];
    const query = searchInput ? searchInput.value.trim() : "";
    if (query) values.push("Suche: „" + query + "“");
    const category = activeCategoryId();
    if (category) values.push("Kategorie: " + selectedCategoryLabel(category));
    return values;
  }

  function render() {
    const values = labels();
    if (activeFilters) {
      activeFilters.textContent = values.join(" · ");
      activeFilters.hidden = values.length === 0;
    }
    const hasApplied = Boolean(values.length || topicFilter?.value ||
      ageFilter?.value || difficultyFilter?.value);
    if (resetButton) resetButton.hidden = !hasApplied;
  }

  searchInput?.addEventListener("input", render);
  ageFilter?.addEventListener("change", render);
  difficultyFilter?.addEventListener("change", render);
  topicFilter?.addEventListener("change", render);
  window.addEventListener("popstate", () => queueMicrotask(render));
  document.addEventListener("click", () => queueMicrotask(render));
  if (resultCount) new MutationObserver(render).observe(resultCount, {childList:true, characterData:true, subtree:true});
  render();
})();
