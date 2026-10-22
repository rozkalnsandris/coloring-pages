const page = document.body;
const category = String(page?.dataset.categoryPage || "");
const categoryLabel = String(page?.dataset.categoryLabel || "");
const categoryTopics = new Set(
  String(page?.dataset.categoryTopics || "").split(",").map((value) => value.trim()).filter(Boolean)
);
let topicRegistry = [];
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
  if (!categoryTopics.size) return;
  const response = await fetch("/topics.json", { cache: "no-store" });
  if (!response.ok) throw new Error("topic registry unavailable");
  const payload = await response.json();
  if (payload?.schema !== "rozkalns.coloring-pages.topics.v1" || !Array.isArray(payload.topics)) throw new Error("invalid topic registry");
  topicRegistry = payload.topics.filter((topic) => topic && typeof topic.id === "string" && typeof topic.label === "string");
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
      if (entry.category === category) return true;
      return categoryTopics.size > 0 && entryTopicIds(entry).some((topicId) => categoryTopics.has(topicId));
    });
    const fragment = document.createDocumentFragment();
    entries.forEach((entry) => fragment.append(createCard(entry)));
    gallery.replaceChildren(fragment);
    if (total) total.textContent = String(entries.length);
    if (status) {
      status.textContent = entries.length
        ? entries.length + " " + (entries.length === 1 ? "Malvorlage" : "Malvorlagen") + " in " + categoryLabel + "."
        : "Zurzeit sind in dieser Kategorie keine Malvorlagen verfügbar.";
      status.hidden = entries.length > 0;
    }
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