const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");
const searchForm = document.querySelector("[data-search-form]");
const searchInput = document.querySelector("#site-search");
const headerSearch = document.querySelector("[data-header-search]");
const gallery = document.querySelector("[data-gallery]");
const categoryButtons = [...document.querySelectorAll("[data-filter]")];
const resultCount = document.querySelector("[data-result-count]");
const totalCount = document.querySelector("[data-total-count]");
const emptyState = document.querySelector("[data-empty-state]");
const loadMoreButton = document.querySelector("[data-load-more]");
const rankingRoot = document.querySelector("[data-ranking-root]");
const rankingTabs = [...document.querySelectorAll("[data-ranking-tab]")];
const rankingDescription = document.querySelector("[data-ranking-description]");
const rankingSections = new Map(
  [...document.querySelectorAll("[data-ranking-section]")].map((section)=>[section.dataset.rankingSection,section])
);

const CATALOG_PAGE_SIZE = 20;
const RANKING_DESCRIPTIONS = {
  trending: "In den letzten 7 Tagen besonders oft gedruckt.",
  popular: "Nach den meisten A4-Druckaktionen.",
};

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
let catalogEntries = null;
let visibleLimit = CATALOG_PAGE_SIZE;

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

function updateCatalogCounts(entries = null) {
  const cards = Array.isArray(entries) ? [] : currentCards();
  const categories = Array.isArray(entries)
    ? entries.map((entry) => entry.category)
    : cards.map((card) => card.dataset.category);
  const counts = new Map();

  categories.forEach((value) => {
    const category = normalize(value ?? "");
    if (!category) return;
    counts.set(category, (counts.get(category) || 0) + 1);
  });

  categoryButtons.forEach((button) => {
    const category = normalize(button.dataset.filter ?? "");
    const value = button.querySelector("[data-category-count]");
    if (value) value.textContent = String(counts.get(category) || 0);
  });

  if (totalCount) totalCount.textContent = String(Array.isArray(entries) ? entries.length : cards.length);
}

function updateCount(totalMatches) {
  if (resultCount) {
    resultCount.textContent = `${totalMatches} ${totalMatches === 1 ? "Malvorlage" : "Malvorlagen"}`;
  }
  if (emptyState) {
    emptyState.hidden = totalMatches !== 0;
  }
}

function matchesFilters(titleValue, categoryValue) {
  const query = normalize(searchInput?.value ?? "");
  const title = normalize(titleValue ?? "");
  const category = normalize(categoryValue ?? "");
  const categoryLabel = normalize(CATEGORY_LABELS[category] || category);
  const matchesQuery = !query || title.includes(query) || category.includes(query) || categoryLabel.includes(query);
  const matchesCategory = !activeCategory || category === activeCategory;
  return matchesQuery && matchesCategory;
}

function renderCatalog() {
  if (!gallery || !Array.isArray(catalogEntries)) return;

  const matches = catalogEntries.filter((entry) => matchesFilters(entry.title, entry.category));
  const visibleEntries = matches.slice(0, visibleLimit);
  const fragment = document.createDocumentFragment();

  visibleEntries.forEach((entry) => {
    fragment.append(createCatalogCard(entry));
  });

  gallery.replaceChildren(fragment);
  updateCount(matches.length);

  if (loadMoreButton) {
    loadMoreButton.hidden = visibleEntries.length >= matches.length;
  }
}

function applyFilters({ resetLimit = true } = {}) {
  if (Array.isArray(catalogEntries)) {
    if (resetLimit) visibleLimit = CATALOG_PAGE_SIZE;
    renderCatalog();
    return;
  }

  let visible = 0;
  currentCards().forEach((card) => {
    const show = matchesFilters(card.dataset.title, card.dataset.category);
    card.hidden = !show;
    if (show) visible += 1;
  });

  updateCount(visible);
  if (loadMoreButton) loadMoreButton.hidden = true;
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

function formatMetric(value) {
  return new Intl.NumberFormat("de-DE",{notation:"compact",maximumFractionDigits:1}).format(Number(value)||0);
}
function createMetricRow(stats) {
  const row=document.createElement("div"); row.className="card-metrics";
  const likes=document.createElement("span");
  likes.setAttribute("aria-label",`${Number(stats?.like_count||0)} Likes`);
  likes.textContent=`♥ ${formatMetric(stats?.like_count)}`;
  const prints=document.createElement("span");
  prints.setAttribute("aria-label",`${Number(stats?.print_count||0)} Druckaktionen`);
  prints.textContent=`🖨 ${formatMetric(stats?.print_count)}`;
  row.append(likes,prints); return row;
}
function detailHref(pageId) {
  const params = new URLSearchParams({id:String(pageId)});
  if (new URLSearchParams(location.search).get("campaign") === "dortmund-01") {
    params.set("campaign","dortmund-01");
  }
  return `detail.html?${params.toString()}`;
}

function createCatalogCard(entry, stats = null) {
  const card = document.createElement("article");
  card.className = "coloring-card";
  card.dataset.title = entry.title || "";
  card.dataset.category = entry.category || "";

  const previewLink = document.createElement("a");
  previewLink.className = "preview-image";
  previewLink.href = detailHref(entry.id);
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

  card.append(previewLink,heading);
  if (stats) card.append(createMetricRow(stats));
  card.append(badges);
  return card;
}

function setRankingTab(kind, {focus = false} = {}) {
  const panel = rankingSections.get(kind);
  const button = rankingTabs.find((candidate) => candidate.dataset.rankingTab === kind);
  if (!panel || !button || button.hidden) return;

  rankingTabs.forEach((candidate) => {
    const selected = candidate.dataset.rankingTab === kind;
    candidate.classList.toggle("is-active", selected);
    candidate.setAttribute("aria-selected", String(selected));
    candidate.tabIndex = selected ? 0 : -1;
  });
  rankingSections.forEach((candidate, candidateKind) => {
    candidate.hidden = candidateKind !== kind;
  });
  if (rankingDescription) {
    rankingDescription.textContent = RANKING_DESCRIPTIONS[kind] || "";
  }
  if (focus) button.focus();
}

function renderRanking(kind, entries, statsItems) {
  const section=rankingSections.get(kind);
  const target=section?.querySelector(`[data-ranking-gallery="${kind}"]`);
  if (!section || !target || !Array.isArray(statsItems)) return false;
  const byId=new Map(entries.map((entry)=>[String(entry.id),entry]));
  const cards=statsItems.map((stats)=>{
    const entry=byId.get(String(stats.page_id));
    return entry ? createCatalogCard(entry,stats) : null;
  }).filter(Boolean);
  if (!cards.length) return false;
  target.replaceChildren(...cards);
  return true;
}

rankingTabs.forEach((button) => {
  button.addEventListener("click", () => setRankingTab(button.dataset.rankingTab));
  button.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const available = rankingTabs.filter((candidate) => !candidate.hidden);
    if (!available.length) return;

    const currentIndex = Math.max(0, available.indexOf(button));
    let nextIndex = currentIndex;
    if (event.key === "ArrowLeft") nextIndex = (currentIndex - 1 + available.length) % available.length;
    if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % available.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = available.length - 1;

    event.preventDefault();
    setRankingTab(available[nextIndex].dataset.rankingTab, {focus: true});
  });
});

async function hydrateRankings(entries) {
  if (!window.ColoringStats?.getRankings) return;
  try {
    const data=await window.ColoringStats.getRankings(6);
    const available = new Map([
      ["trending", renderRanking("trending",entries,data.trending)],
      ["popular", renderRanking("popular",entries,data.popular)],
    ]);
    rankingTabs.forEach((button) => {
      button.hidden = !available.get(button.dataset.rankingTab);
    });
    const initialKind = available.get("trending")
      ? "trending"
      : available.get("popular")
        ? "popular"
        : "";
    if (!initialKind || !rankingRoot) return;
    rankingRoot.hidden=false;
    setRankingTab(initialKind);
  } catch {}
}
async function hydrateCatalog() {
  if (!gallery) return;

  try {
    const response = await fetch("catalog.json", { cache: "no-store" });
    if (!response.ok) return;

    const catalog = await response.json();
    if (!Array.isArray(catalog) || catalog.length === 0) return;

    const entries = catalog.filter((entry) => entry && entry.id && entry.title && entry.thumb);
    if (!entries.length) return;

    catalogEntries = entries;
    visibleLimit = CATALOG_PAGE_SIZE;
    updateCatalogCounts(catalogEntries);
    renderCatalog();
    await hydrateRankings(catalogEntries);
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

loadMoreButton?.addEventListener("click", () => {
  if (!Array.isArray(catalogEntries)) return;
  visibleLimit += CATALOG_PAGE_SIZE;
  renderCatalog();
});

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
  updateCatalogCounts();
  applyFilters();
  hydrateCatalog();
}
