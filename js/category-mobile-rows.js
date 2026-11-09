/* Mobile category disclosure rows: keep two equal card columns and DOM/tab order.
   With JavaScript disabled, the original native details and links remain usable. */
(() => {
  "use strict";
  const browser = document.querySelector(".category-browser");
  if (!browser || typeof window.matchMedia !== "function") return;
  const mobile = window.matchMedia("(min-width: 361px) and (max-width: 540px)");
  let rows = [];
  let lists = new Map();
  const observed = new WeakSet();

  function restore() {
    for (const [details, list] of lists) {
      if (list.parentElement !== details) details.append(list);
      details.querySelector(":scope > summary")?.removeAttribute("aria-controls");
    }
    browser.querySelectorAll(":scope > [data-category-row-panel]").forEach((panel) => panel.remove());
    browser.removeAttribute("data-category-mobile-rows");
    rows = [];
    lists = new Map();
  }

  function updateOpenPanel() {
    if (!browser.hasAttribute("data-category-mobile-rows")) return;
    // Move existing links, not clones: URL/filter handlers remain attached.
    for (const [details, list] of lists) {
      if (list.parentElement !== details) details.append(list);
    }
    for (const { cards, panel } of rows) {
      const open = cards.find((card) => card.matches("details[open]"));
      const list = open && lists.get(open);
      panel.hidden = !list;
      if (list) {
        panel.append(list);
        panel.setAttribute("aria-labelledby", open.querySelector("summary").id);
      } else {
        panel.removeAttribute("aria-labelledby");
      }
    }
  }

  function rebuild() {
    restore();
    if (!mobile.matches) return;
    const cards = [...browser.children].filter((child) => child.classList.contains("category-group"));
    const disclosed = cards.filter((card) => card.tagName === "DETAILS");
    if (disclosed.some((detail) =>
      !detail.querySelector(":scope > summary") || !detail.querySelector(":scope > .category-subtopics"))) return;
    for (let i = 0; i < cards.length; i += 2) {
      const pair = cards.slice(i, i + 2);
      const panel = document.createElement("div");
      panel.className = "category-row-topics";
      panel.id = "category-row-topics-" + (i / 2 + 1);
      panel.dataset.categoryRowPanel = String(i / 2);
      panel.setAttribute("role", "group");
      panel.hidden = true;
      pair[pair.length - 1].after(panel);
      rows.push({ cards: pair, panel });
      for (const detail of pair) {
        if (detail.tagName !== "DETAILS") continue;
        const summary = detail.querySelector(":scope > summary");
        if (!summary.id) summary.id = "category-mobile-summary-" + (i + pair.indexOf(detail) + 1);
        summary.setAttribute("aria-controls", panel.id);
        lists.set(detail, detail.querySelector(":scope > .category-subtopics"));
        if (!observed.has(detail)) {
          observed.add(detail);
          detail.addEventListener("toggle", updateOpenPanel);
        }
      }
    }
    browser.setAttribute("data-category-mobile-rows", "");
    updateOpenPanel();
  }

  // Re-pair when the trusted managed registry adds/removes runtime categories.
  const observer = new MutationObserver((mutations) => {
    if (mutations.some((mutation) =>
      [...mutation.addedNodes, ...mutation.removedNodes].some((node) =>
        node.nodeType === Node.ELEMENT_NODE && node.matches("[data-runtime-category]")))) {
      rebuild();
    }
  });
  observer.observe(browser, { childList: true });
  mobile.addEventListener("change", rebuild);
  rebuild();
})();
