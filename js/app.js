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
  tiere: "Tiere",
  fahrzeuge: "Fahrzeuge",
  alphabet: "Alphabet",
  lernen: "Lernen",
  figuren: "Figuren & Helden",
  jahreszeiten: "Jahreszeiten & Feste",
  seasonal: "Jahreszeiten & Feste",
};

const DIFFICULTY_LABELS = {
  easy: "Einfach",
  normal: "Mittel",
  detailed: "Detailliert",
};

let activeCategory = "";

// Keep both menus in sync on direct links, anchor navigation and browser Back/Forward.
function updateNavigation(hash = window.location.hash) {
  if (!gallery) return;
  const section = hash === "#ueber-uns" ? "#ueber-uns"
    : ["#kategorien", "#neu"].includes(hash) ? "#kategorien" : "#hero";
  document.querySelectorAll(".desktop-nav a, .mobile-nav a").forEach((link) => {
    const active = link.getAttribute("href") === section;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}

window.addEventListener("hashchange", () => updateNavigation());
window.addEventListener("pageshow", () => updateNavigation());
document.querySelectorAll(".desktop-nav a, .mobile-nav a").forEach((link) => {
  link.addEventListener("click", () => updateNavigation(link.hash));
});
updateNavigation();

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
    const categoryLabel = normalize(CATEGORY_LABELS[category] || category);
    const matchesQuery = !query || title.includes(query) || category.includes(query) || categoryLabel.includes(query);
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

function entryPageCount(entry) {
  return Array.isArray(entry.pages) && entry.pages.length > 0
    ? entry.pages.length
    : 1;
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

  const pageCount = entryPageCount(entry);
  if (pageCount > 1) {
    badges.append(createBadge(`${pageCount} Seiten`, "pages-badge"));
  }

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
  function setMenuOpen(open) {
    menuButton.setAttribute("aria-expanded", String(open));
    mobileNav.hidden = !open;
    const label = menuButton.querySelector(".sr-only");
    if (label) label.textContent = open ? "Menü schließen" : "Menü öffnen";
  }

  menuButton.addEventListener("click", () => {
    const expanded = menuButton.getAttribute("aria-expanded") === "true";
    setMenuOpen(!expanded);
  });

  mobileNav.addEventListener("click", (event) => {
    const link = event.target.closest("a");
    if (link) {
      setMenuOpen(false);
      // Do not leave keyboard focus inside the now-hidden menu.
      if (link.hash && link.pathname === window.location.pathname) {
        const target = document.getElementById(link.hash.slice(1));
        target?.setAttribute("tabindex", "-1");
        target?.focus({ preventScroll: true });
      }
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !mobileNav.hidden) {
      setMenuOpen(false);
      menuButton.focus();
    }
  });
}

headerSearch?.addEventListener("click", () => {
  searchInput?.focus();
});

searchForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  applyFilters();
  updateNavigation("#neu");
  document.querySelector("#neu")?.scrollIntoView({ block: "start" });
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
    updateNavigation("#neu");
    document.querySelector("#neu")?.scrollIntoView({ block: "start" });
  });
});

document.querySelector("[data-reset-filters]")?.addEventListener("click", () => {
  activeCategory = "";
  if (searchInput) searchInput.value = "";
  categoryButtons.forEach((button) => {
    button.classList.remove("is-active");
    button.setAttribute("aria-pressed", "false");
  });
  applyFilters();
});

if (gallery) {
  applyFilters();
  hydrateCatalog();
}
