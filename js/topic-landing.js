const page = document.body;
const topicId = String(page?.dataset.topicPage || "");
const topicLabel = String(page?.dataset.topicLabel || "");
const gallery = document.querySelector("[data-topic-gallery]");
const status = document.querySelector("[data-topic-status]");
const total = document.querySelector("[data-topic-total]");
const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");

const DIFFICULTY_LABELS = { easy: "Einfach", normal: "Mittel", detailed: "Detailliert" };

function entryTopicIds(entry) {
  if (!Array.isArray(entry?.topics)) return [];
  return [...new Set(entry.topics
    .map((value) => String(value || "").trim().toLocaleLowerCase("de"))
    .filter((value) => /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value)))];
}

async function requireManagedTopic() {
  const response = await fetch("/topics.json", { cache: "no-store" });
  if (!response.ok) throw new Error("topic registry unavailable");
  const payload = await response.json();
  if (!["rozkalns.coloring-pages.topics.v1", "rozkalns.coloring-pages.topics.v2"].includes(payload?.schema) || !Array.isArray(payload?.topics)) {
    throw new Error("invalid topic registry");
  }
  const topic = payload.topics.find((candidate) => candidate && candidate.id === topicId && typeof candidate.label === "string");
  if (!topic) throw new Error("topic unavailable");
  return topic;
}

function createBadge(label, className) {
  const badge = document.createElement("span");
  badge.textContent = label;
  badge.className = className;
  return badge;
}

function createCard(entry) {
  const card = document.createElement("article");
  card.className = "coloring-card";
  const href = `/detail.html?id=${encodeURIComponent(String(entry.id))}`;

  const previewLink = document.createElement("a");
  previewLink.className = "preview-image";
  previewLink.href = href;
  previewLink.setAttribute("aria-label", `${entry.title} ansehen`);
  const image = document.createElement("img");
  image.src = entry.thumb;
  image.alt = entry.title || "Malvorlage";
  image.loading = "lazy";
  previewLink.append(image);

  const heading = document.createElement("h3");
  const headingLink = document.createElement("a");
  headingLink.href = href;
  headingLink.textContent = entry.title;
  heading.append(headingLink);

  const badges = document.createElement("div");
  badges.className = "badges";
  if (entry.age === "3-6" || entry.age === "4-8") {
    badges.append(createBadge(`${entry.age} Jahre`, entry.age === "4-8" ? "age age-older" : "age"));
  }
  if (DIFFICULTY_LABELS[entry.difficulty]) {
    const className = entry.difficulty === "easy" ? "easy" : entry.difficulty === "detailed" ? "detailed" : "medium";
    badges.append(createBadge(DIFFICULTY_LABELS[entry.difficulty], className));
  }
  if (Array.isArray(entry.pages) && entry.pages.length > 1) {
    badges.append(createBadge(`${entry.pages.length} Seiten`, "pages-badge"));
  }

  card.append(previewLink, heading);
  if (badges.childElementCount) card.append(badges);
  return card;
}

async function hydrateTopicLanding() {
  if (!topicId || !gallery) return;
  try {
    await requireManagedTopic();
    const response = await fetch("/catalog.json", { cache: "no-store" });
    if (!response.ok) throw new Error("catalog unavailable");
    const catalog = await response.json();
    if (!Array.isArray(catalog)) throw new Error("invalid catalog");

    const entries = catalog.filter((entry) =>
      entry && entry.id && entry.title && entry.thumb && entryTopicIds(entry).includes(topicId)
    );
    const fragment = document.createDocumentFragment();
    entries.forEach((entry) => fragment.append(createCard(entry)));
    gallery.replaceChildren(fragment);
    if (total) total.textContent = String(entries.length);

    if (status) {
      status.textContent = entries.length
        ? `Alle aktuell veröffentlichten ${topicLabel || "Themen"}-Malvorlagen werden angezeigt.`
        : "Zurzeit sind keine veröffentlichten Herbst-Malvorlagen verfügbar.";
      status.hidden = entries.length > 0;
    }
  } catch {
    if (status) {
      status.textContent = "Die vollständige Herbst-Auswahl konnte gerade nicht geladen werden. Die direkt angezeigten Motive bleiben verfügbar.";
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
menuButton?.addEventListener("click", () => setMenuOpen(menuButton.getAttribute("aria-expanded") !== "true"));
mobileNav?.addEventListener("click", (event) => { if (event.target.closest("a")) setMenuOpen(false); });
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && mobileNav && !mobileNav.hidden) {
    setMenuOpen(false);
    menuButton?.focus();
  }
});

hydrateTopicLanding();
