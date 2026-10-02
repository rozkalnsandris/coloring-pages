const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");
const searchForm = document.querySelector("[data-search-form]");
const searchInput = document.querySelector("#site-search");
const headerSearch = document.querySelector("[data-header-search]");
const cards = [...document.querySelectorAll(".coloring-card")];
const categoryButtons = [...document.querySelectorAll("[data-filter]")];
const resultCount = document.querySelector("[data-result-count]");
const emptyState = document.querySelector("[data-empty-state]");

let activeCategory = "";

function normalize(value) {
  return value.trim().toLocaleLowerCase("de");
}

function applyFilters() {
  const query = normalize(searchInput?.value ?? "");
  let visible = 0;

  cards.forEach((card) => {
    const title = normalize(card.dataset.title ?? "");
    const category = card.dataset.category ?? "";
    const matchesQuery = !query || title.includes(query) || normalize(category).includes(query);
    const matchesCategory = !activeCategory || category === activeCategory;
    const show = matchesQuery && matchesCategory;

    card.hidden = !show;
    if (show) visible += 1;
  });

  if (resultCount) {
    resultCount.textContent = `${visible} ${visible === 1 ? "Malvorlage" : "Malvorlagen"}`;
  }

  if (emptyState) {
    emptyState.hidden = visible !== 0;
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
    const category = button.dataset.filter ?? "";
    activeCategory = activeCategory === category ? "" : category;

    categoryButtons.forEach((candidate) => {
      const selected = candidate.dataset.filter === activeCategory;
      candidate.classList.toggle("is-active", selected);
      candidate.setAttribute("aria-pressed", String(selected));
    });

    applyFilters();
    document.querySelector("#neu")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

if (cards.length) applyFilters();
