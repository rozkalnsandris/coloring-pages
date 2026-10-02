const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");
const searchForm = document.querySelector("[data-search-form]");
const searchInput = document.querySelector("#site-search");
const headerSearch = document.querySelector("[data-header-search]");
const gallery = document.querySelector("[data-gallery]");
const categoryButtons = [...document.querySelectorAll("[data-filter]")];
const resultCount = document.querySelector("[data-result-count]");
const emptyState = document.querySelector("[data-empty-state]");

const CATEGORY_LABELS = {
  rettungshunde: "Rettungshunde",
  tiere: "Tiere",
  fahrzeuge: "Fahrzeuge",
  alphabet: "Alphabet",
  lernen: "Lernen",
  jahreszeiten: "Jahreszeiten",
  seasonal: "Jahreszeiten",
};

const DIFFICULTY_LABELS = {
  easy: "Einfach",
  normal: "Mittel",
  detailed: "Detailliert",
};

let activeCategory = "";

function normalize(value) {
  return String(value || "").trim().toLocaleLowerCase("de");
}

function currentCards() {
  return [...document.querySelectorAll(".coloring-card")];
}

function updateCount(visible) {
  if (resultCount) {
    resultCount.textContent = `${visible} ${visible === 1 ? "Malvorlage" : "Malvorlagen"}`;
  }
  if (emptyState) {
    emptyState.hidden = visible !== 0;
  }
}

function applyFilters() {
  const query = normalize(searchInput?.value ?? "");
  let visible = 0;

  currentCards().forEach((card) => {
    const title = normalize(card.dataset.title ?? "");
    const category = normalize(card.dataset.category ?? "");
    const matchesQuery = !query || title.includes(query) || category.includes(query);
    const matchesCategory = !activeCategory || category === activeCategory;
    const show = matchesQuery && matchesCategory;

    card.hidden = !show;
    if (show) visible += 1;
  });

  updateCount(visible);
}

function createBadge(label, className) {
  const badge = document.createElement("span");
  badge.textContent = label;
  badge.className = className;
  return badge;
}

function createCatalogCard(entry) {
  const card = document.createElement("article");
  card.className = "coloring-card";
  card.dataset.title = entry.title || "";
  card.dataset.category = entry.category || "";

  const previewLink = document.createElement("a");
  previewLink.className = "preview-image";
  previewLink.href = `detail.html?id=${encodeURIComponent(entry.id)}`;
  previewLink.setAttribute("aria-label", `${entry.title} ansehen`);

  const image = document.createElement("img");
  image.src = entry.thumb;
  image.alt = entry.title || "Malvorlage";
  image.loading = "lazy";
  previewLink.append(image);

  const heading = document.createElement("h3");
  const headingLink = document.createElement("a");
  headingLink.href = previewLink.href;
  headingLink.textContent = entry.title;
  heading.append(headingLink);

  const badges = document.createElement("div");
  badges.className = "badges";

  const ageClass = entry.age === "4-8" ? "age age-older" : "age";
  badges.append(createBadge(`${entry.age} Jahre`, ageClass));

  const difficultyLabel = DIFFICULTY_LABELS[entry.difficulty] || entry.difficulty;
  const difficultyClass =
    entry.difficulty === "easy"
      ? "easy"
      : entry.difficulty === "detailed"
        ? "detailed"
        : "medium";
  badges.append(createBadge(difficultyLabel, difficultyClass));

  card.append(previewLink, heading, badges);
  return card;
}

async function hydrateCatalog() {
  if (!gallery) return;

  try {
    const response = await fetch("catalog.json", { cache: "no-store" });
    if (!response.ok) return;

    const catalog = await response.json();
    if (!Array.isArray(catalog) || catalog.length === 0) return;

    const fragment = document.createDocumentFragment();
    catalog.forEach((entry) => {
      if (!entry || !entry.id || !entry.title || !entry.thumb) return;
      fragment.append(createCatalogCard(entry));
    });

    if (!fragment.childNodes.length) return;

    gallery.replaceChildren(fragment);
    applyFilters();
  } catch {
    // Static fallback cards intentionally remain visible when catalog.json is unavailable.
  }
}

if (menuButton && mobileNav) {
  menuButton.addEventListener("click", () => {
    const expanded = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!expanded));
    mobileNav.hidden = expanded;

    const label = menuButton.querySelector(".sr-only");
    if (label) label.textContent = expanded ? "Menü öffnen" : "Menü schließen";
  });

  mobileNav.addEventListener("click", (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      menuButton.setAttribute("aria-expanded", "false");
      mobileNav.hidden = true;
    }
  });
}

headerSearch?.addEventListener("click", () => {
  searchInput?.focus();
});

searchForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  applyFilters();
  document.querySelector("#neu")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

searchInput?.addEventListener("input", applyFilters);

categoryButtons.forEach((button) => {
  button.setAttribute("aria-pressed", "false");
  button.addEventListener("click", () => {
    const category = normalize(button.dataset.filter ?? "");
    activeCategory = activeCategory === category ? "" : category;

    categoryButtons.forEach((candidate) => {
      const selected = normalize(candidate.dataset.filter) === activeCategory;
      candidate.classList.toggle("is-active", selected);
      candidate.setAttribute("aria-pressed", String(selected));
    });

    applyFilters();
    document.querySelector("#neu")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

if (gallery) {
  applyFilters();
  hydrateCatalog();
}
