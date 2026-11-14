(() => {
  "use strict";
  // One UI renderer for the homepage, category routes, and topic landings.
  // Controllers own data, filtering and route-specific URL semantics only.
  const ages = [["", "Alle Altersgruppen"], ["3-6", "3–6 Jahre"], ["4-8", "4–8 Jahre"]];
  const difficulties = [
    ["", "Alle Schwierigkeitsgrade"], ["easy", "Einfach"],
    ["normal", "Mittel"], ["detailed", "Detailliert"],
  ];
  function field(id, label, key, options) {
    const wrapper = document.createElement("div");
    wrapper.className = "metadata-filter-field";
    const labelNode = document.createElement("label");
    labelNode.htmlFor = id;
    labelNode.textContent = label;
    const select = document.createElement("select");
    select.id = id;
    select.dataset[key] = "";
    options.forEach(([value, text]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = text;
      select.append(option);
    });
    wrapper.append(labelNode, select);
    return { wrapper, select };
  }
  function mount(root, { idPrefix = "filter" } = {}) {
    if (!root) return null;
    root.className = "gallery-filter-panel";
    root.dataset.galleryFilterPanel = "";
    root.setAttribute("role", "group");
    root.setAttribute("aria-label", "Malvorlagen filtern");
    const fields = document.createElement("div");
    fields.className = "metadata-filters gallery-filter-fields";
    const topicField = field(idPrefix + "-topic", "Thema", "filterTopic", [
      ["", "Alle Themen"],
    ]);
    const ageField = field(idPrefix + "-age", "Alter", "filterAge", ages);
    const difficultyField = field(idPrefix + "-difficulty",
      "Schwierigkeit", "filterDifficulty", difficulties);
    const topic = topicField.select;
    const age = ageField.select;
    const difficulty = difficultyField.select;
    topic.disabled = true;
    fields.append(topicField.wrapper, ageField.wrapper, difficultyField.wrapper);

    const hint = document.createElement("p");
    hint.className = "metadata-filter-hint";
    hint.textContent = "Die Filter berücksichtigen nur vorhandene Alters- und Schwierigkeitsangaben.";
    const footer = document.createElement("div");
    footer.className = "gallery-filter-footer";
    const count = document.createElement("p");
    count.className = "metadata-filter-hint result-count";
    count.dataset.resultCount = "";
    count.setAttribute("aria-live", "polite");
    count.textContent = "0 Malvorlagen";
    const total = document.createElement("span");
    total.dataset.totalCount = "";
    total.hidden = true;
    total.textContent = "0";
    const reset = document.createElement("button");
    reset.type = "button";
    reset.className = "outline-link";
    reset.dataset.resetFilters = "";
    reset.dataset.resetAllFilters = "";
    reset.textContent = "Alle Filter zurücksetzen";
    reset.hidden = true;
    footer.append(count, total, reset);
    const context = document.createElement("p");
    context.className = "metadata-filter-hint gallery-filter-context";
    context.dataset.activeFilters = "";
    context.setAttribute("aria-label", "Weitere aktive Filter");
    context.hidden = true;
    root.replaceChildren(fields, hint, footer, context);

    function setTopics(topics, selected = "", locked = false) {
      const all = document.createElement("option");
      all.value = "";
      all.textContent = "Alle Themen";
      const choices = (Array.isArray(topics) ? topics : []).map((entry) => {
        const option = document.createElement("option");
        option.value = entry.id;
        option.textContent = entry.label;
        return option;
      });
      topic.replaceChildren(all, ...choices);
      topic.disabled = locked || choices.length === 0;
      topic.value = choices.some((option) => option.value === selected) ? selected : "";
    }
    function setValues(values = {}) {
      if ("topic" in values) topic.value = values.topic || "";
      if ("age" in values) age.value = values.age || "";
      if ("difficulty" in values) difficulty.value = values.difficulty || "";
    }
    function setCount(value) {
      const number = Math.max(0, Number(value) || 0);
      count.textContent = number + " " + (number === 1 ? "Malvorlage" : "Malvorlagen");
    }
    function setResetVisible(visible) { reset.hidden = !visible; }
    return { root, topic, age, difficulty, count, total, reset, context,
      setTopics, setValues, setCount, setResetVisible };
  }
  globalThis.AusmalGalleryFilterPanel = Object.freeze({ mount });
  // Progressive enhancement: the homepage's static panel is its no-JS
  // fallback; with JS, this exact shared renderer takes over before app.js.
  const homepage = document.querySelector("[data-gallery-filter-panel]");
  if (homepage) mount(homepage, { idPrefix: "filter" });
})();
