const page = document.body;
const category = String(page?.dataset.categoryPage || "");
const categoryLabel = String(page?.dataset.categoryLabel || "");
const categoryTopics = new Set(
  String(page?.dataset.categoryTopics || "").split(",").map((value) => value.trim()).filter(Boolean)
);
let topicRegistry = [];
let categoryEntries = [];
let activeCategoryTopic = "";
const MAX_CATEGORY_TOPICS = 8;
const gallery = document.querySelector("[data-category-gallery]");
const status = document.querySelector("[data-category-status]");
const total = document.querySelector("[data-category-total]");
const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");

const DIFFICULTY_LABELS = {
  easy: "Einfach",
  normal: "Mittel",
  detailed: "Detailliert",
};

function normalizeTopicText(value) {
  return String(value || "").trim().toLocaleLowerCase("de")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "").replaceAll("ß", "ss");
}
function entryCategoryIds(entry) {
  const primary = String(entry?.category || "");
  const assigned = entry?.categories;
  if (Array.isArray(assigned) && assigned.length > 0 && assigned[0] === primary &&
    assigned.every((id) => typeof id === "string" && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id)) &&
    new Set(assigned).size === assigned.length) return assigned;
  return primary ? [primary] : [];
}

function entryTopicIds(entry) {
  const known = new Set(topicRegistry.map((topic) => topic.id));
  if (Array.isArray(entry?.topics)) {
    return [...new Set(entry.topics.map((value) => String(value || "").trim().toLocaleLowerCase("de")).filter((value) => known.has(value)))];
  }
  const haystack = normalizeTopicText(`${entry?.title || ""} ${entry?.character || ""}`);
  if (!haystack) return [];
  return topicRegistry.filter((topic) =>
    Array.isArray(topic.legacy_terms) && topic.legacy_terms.some((term) => haystack.includes(normalizeTopicText(term)))
  ).map((topic) => topic.id);
}
async function loadTopicRegistry() {
  try {
    const response = await fetch("/topics.json", { cache: "no-store" });
    if (!response.ok) throw new Error("topic registry unavailable");
    const payload = await response.json();
    if (payload?.schema !== "rozkalns.coloring-pages.topics.v1" || !Array.isArray(payload.topics)) throw new Error("invalid topic registry");
    topicRegistry = payload.topics.filter((topic) => topic && typeof topic.id === "string" && typeof topic.label === "string");
  } catch (error) {
    topicRegistry = [];
    if (categoryTopics.size) throw error;
  }
}

function categoryTopicCandidates(entries) {
  const counts = new Map();
  entries.forEach((entry) => {
    entryTopicIds(entry).forEach((topicId) => counts.set(topicId, (counts.get(topicId) || 0) + 1));
  });

  if (categoryTopics.size) {
    return [...categoryTopics]
      .map((topicId) => topicRegistry.find((topic) => topic.id === topicId))
      .filter((topic) => topic && (counts.get(topic.id) || 0) > 0)
      .map((topic) => ({ ...topic, count: counts.get(topic.id) || 0 }));
  }

  const kind = category === "jahreszeiten" ? "seasonal" : "evergreen";
  return topicRegistry
    .filter((topic) => topic.kind === kind && (counts.get(topic.id) || 0) > 0)
    .map((topic) => ({ ...topic, count: counts.get(topic.id) || 0 }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "de"))
    .slice(0, MAX_CATEGORY_TOPICS);
}

function ensureCategoryTopicFilter(entries) {
  const section = document.querySelector(".category-results .container");
  const heading = section?.querySelector(".section-heading");
  if (!section || !heading) return;

  const topics = categoryTopicCandidates(entries);
  const shouldShow = categoryTopics.size ? topics.length > 0 : topics.length > 1;
  let root = section.querySelector("[data-category-topic-filter]");

  if (!shouldShow) {
    activeCategoryTopic = "";
    root?.remove();
    return;
  }

  if (!topics.some((topic) => topic.id === activeCategoryTopic)) activeCategoryTopic = "";

  if (!root) {
    root = document.createElement("div");
    root.className = "category-topic-filter";
    root.dataset.categoryTopicFilter = "";

    const label = document.createElement("p");
    label.className = "category-topic-filter-label";
    label.textContent = "Themen";

    const strip = document.createElement("div");
    strip.className = "category-topic-strip";
    strip.setAttribute("role", "group");
    strip.setAttribute("aria-label", "Malvorlagen nach Thema filtern");

    root.append(label, strip);
    heading.after(root);
  }

  const strip = root.querySelector(".category-topic-strip");
  if (!strip) return;

  const makeButton = (id, label, count, icon = "") => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category-topic-chip";
    button.dataset.categoryTopic = id;
    button.setAttribute("aria-pressed", String(activeCategoryTopic === id));

    if (icon) {
      const iconNode = document.createElement("span");
      iconNode.className = "category-topic-icon";
      iconNode.textContent = icon;
      iconNode.setAttribute("aria-hidden", "true");
      button.append(iconNode);
    }

    const text = document.createElement("span");
    text.textContent = label;

    const badge = document.createElement("span");
    badge.className = "category-topic-count";
    badge.textContent = String(count);
    badge.setAttribute("aria-hidden", "true");

    button.append(text, badge);
    button.addEventListener("click", () => {
      activeCategoryTopic = id;
      ensureCategoryTopicFilter(categoryEntries);
      renderCategoryEntries(categoryEntries);
    });
    return button;
  };

  const allButton = makeButton("", "Alle", entries.length);
  allButton.setAttribute("aria-pressed", String(activeCategoryTopic === ""));
  strip.replaceChildren(
    allButton,
    ...topics.map((topic) => makeButton(topic.id, topic.label, topic.count, topic.icon))
  );
}

function renderCategoryEntries(entries) {
  const activeTopic = activeCategoryTopic
    ? topicRegistry.find((topic) => topic.id === activeCategoryTopic)
    : null;
  const visibleEntries = activeTopic
    ? entries.filter((entry) => entryTopicIds(entry).includes(activeTopic.id))
    : entries;

  const fragment = document.createDocumentFragment();
  visibleEntries.forEach((entry) => fragment.append(createCard(entry)));
  gallery.replaceChildren(fragment);

  if (total) total.textContent = String(visibleEntries.length);

  const galleryTitle = document.querySelector("#category-gallery-title");
  if (galleryTitle) {
    galleryTitle.textContent = activeTopic
      ? activeTopic.label + " entdecken"
      : categoryLabel + " entdecken";
  }

  if (status) {
    const label = activeTopic?.label || categoryLabel;
    status.textContent = visibleEntries.length
      ? visibleEntries.length + " " + (visibleEntries.length === 1 ? "Malvorlage" : "Malvorlagen") + " in " + label + "."
      : "Zurzeit sind in diesem Thema keine Malvorlagen verfügbar.";
    status.hidden = visibleEntries.length > 0;
  }
}

function entryPageCount(entry) {
  return Array.isArray(entry.pages) && entry.pages.length > 0 ? entry.pages.length : 1;
}

function badge(label, className) {
  const node = document.createElement("span");
  node.textContent = label;
  node.className = className;
  return node;
}

function detailHref(id) {
  return "/detail.html?id=" + encodeURIComponent(String(id));
}

function createCard(entry) {
  const card = document.createElement("article");
  card.className = "coloring-card";

  const previewLink = document.createElement("a");
  previewLink.className = "preview-image";
  previewLink.href = detailHref(entry.id);
  previewLink.setAttribute("aria-label", entry.title + " ansehen");

  const image = document.createElement("img");
  image.src = entry.thumb;
  image.alt = entry.title;
  image.loading = "lazy";
  previewLink.append(image);

  const heading = document.createElement("h3");
  const headingLink = document.createElement("a");
  headingLink.href = previewLink.href;
  headingLink.textContent = entry.title;
  heading.append(headingLink);

  const badges = document.createElement("div");
  badges.className = "badges";
  badges.append(badge(entry.age + " Jahre", entry.age === "4-8" ? "age age-older" : "age"));
  badges.append(badge(DIFFICULTY_LABELS[entry.difficulty] || entry.difficulty, entry.difficulty === "easy" ? "easy" : entry.difficulty === "detailed" ? "detailed" : "medium"));

  const pageCount = entryPageCount(entry);
  if (pageCount > 1) badges.append(badge(pageCount + " Seiten", "pages-badge"));

  card.append(previewLink, heading, badges);
  return card;
}

async function loadCategory() {
  if (!category || !gallery) return;
  try {
    await loadTopicRegistry();
    const response = await fetch("/catalog.json", { cache: "no-store" });
    if (!response.ok) throw new Error("catalog unavailable");
    const catalog = await response.json();
    if (!Array.isArray(catalog)) throw new Error("invalid catalog");

    const entries = catalog.filter((entry) => {
      if (!(entry && entry.id && entry.title && entry.thumb)) return false;
      if (entryCategoryIds(entry).includes(category)) return true;
      return categoryTopics.size > 0 && entryTopicIds(entry).some((topicId) => categoryTopics.has(topicId));
    });
    categoryEntries = entries;
    ensureCategoryTopicFilter(entries);
    renderCategoryEntries(entries);
  } catch {
    if (status) {
      status.textContent = "Die Malvorlagen konnten nicht geladen werden. Bitte versuche es später erneut.";
      status.hidden = false;
    }
  }
}

function setMenuOpen(open) {
  if (!menuButton || !mobileNav) return;
  menuButton.setAttribute("aria-expanded", String(open));
  mobileNav.hidden = !open;
  const label = menuButton.querySelector(".sr-only");
  if (label) label.textContent = open ? "Menü schließen" : "Menü öffnen";
}

menuButton?.addEventListener("click", () => {
  setMenuOpen(menuButton.getAttribute("aria-expanded") !== "true");
});
mobileNav?.addEventListener("click", (event) => {
  if (event.target.closest("a")) setMenuOpen(false);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && mobileNav && !mobileNav.hidden) {
    setMenuOpen(false);
    menuButton?.focus();
  }
});

loadCategory();