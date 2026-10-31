const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");
const searchForm = document.querySelector("[data-search-form]");
const searchInput = document.querySelector("#site-search");
const ageFilter = document.querySelector("[data-filter-age]");
const difficultyFilter = document.querySelector("[data-filter-difficulty]");
const surpriseButton = document.querySelector("[data-surprise-button]");
const surpriseStatus = document.querySelector("[data-surprise-status]");
const headerSearch = document.querySelector("[data-header-search]");
const gallery = document.querySelector("[data-gallery]");
const categoryButtons = [...document.querySelectorAll("[data-filter], [data-collection-filter]")];
const resultCount = document.querySelector("[data-result-count]");
const totalCount = document.querySelector("[data-total-count]");
const emptyState = document.querySelector("[data-empty-state]");
const loadMoreButton = document.querySelector("[data-load-more]");
const rankingRoot = document.querySelector("[data-ranking-root]");
const rankingStatus = document.querySelector("[data-ranking-status]");
const rankingTabs = [...document.querySelectorAll("[data-ranking-tab]")];
const rankingDescription = document.querySelector("[data-ranking-description]");
const topicExplorer = document.querySelector("[data-topic-explorer]");
const topicList = document.querySelector("[data-topic-list]");
const topicClear = document.querySelector("[data-topic-clear]");
const rankingSections = new Map(
  [...document.querySelectorAll("[data-ranking-section]")].map((section)=>[section.dataset.rankingSection,section])
);

const CATALOG_PAGE_SIZE = 20;
const AGE_FILTER_VALUES = new Set(["3-6", "4-8"]);
const RANKING_DESCRIPTIONS = {
  trending: "In den letzten 7 Tagen besonders oft gedruckt.",
  popular: "Nach den meisten A4-Druckaktionen.",
};

const CORE_CATEGORY_IDS = ["tiere", "fahrzeuge", "alphabet", "lernen", "figuren", "jahreszeiten"];
let runtimeCategoryIds = new Set();
const CATEGORY_LABELS = {
  tiere: "Tiere",
  fahrzeuge: "Fahrzeuge",
  alphabet: "Alphabet",
  lernen: "Lernen",
  figuren: "Figuren & Helden",
  jahreszeiten: "Jahreszeiten & Feste",
  seasonal: "Jahreszeiten & Feste",
  "essen-natur": "Essen & Natur",
};

const DISCOVERY_COLLECTION_TOPICS = {
  "essen-natur": new Set(["obst", "gemuese", "blumen", "bauernhof"]),
};

function categoryButtonId(button) {
  return normalize(button?.dataset.filter ?? button?.dataset.collectionFilter ?? "");
}

const DIFFICULTY_LABELS = {
  easy: "Einfach",
  normal: "Mittel",
  detailed: "Detailliert",
};

let activeCategory = "";
let activeTopic = "";
let topicRegistry = [];
let catalogEntries = null;
let visibleLimit = CATALOG_PAGE_SIZE;
let catalogIssueText = "";

// URL only stores explicit catalogue facet values; other parameters (including
// campaign) and fragments are preserved. History back/forward restores controls.
function readMetadataFiltersFromUrl() {
  if (!ageFilter && !difficultyFilter) return;
  const params = new URLSearchParams(location.search);
  const age = params.get("age");
  const difficulty = params.get("difficulty");
  if (ageFilter) ageFilter.value = AGE_FILTER_VALUES.has(age) ? age : "";
  if (difficultyFilter) difficultyFilter.value = DIFFICULTY_LABELS[difficulty] ? difficulty : "";
}

function readTopicFilterFromUrl() {
  const requested = normalize(new URLSearchParams(location.search).get("topic"));
  const known = new Set(topicRegistry.map((topic) => topic.id));
  activeTopic = known.has(requested) ? requested : "";
}

function syncCatalogFilterUrl() {
  const url = new URL(location.href);
  if (ageFilter?.value) url.searchParams.set("age", ageFilter.value);
  else url.searchParams.delete("age");
  if (difficultyFilter?.value) url.searchParams.set("difficulty", difficultyFilter.value);
  else url.searchParams.delete("difficulty");
  if (activeTopic) url.searchParams.set("topic", activeTopic);
  else url.searchParams.delete("topic");
  if (activeCategory && runtimeCategoryIds.has(activeCategory)) url.searchParams.set("category", activeCategory);
  else url.searchParams.delete("category");
  const next = url.pathname + url.search + url.hash;
  const now = location.pathname + location.search + location.hash;
  if (next !== now) history.pushState(null, "", next);
}

function syncMetadataFilterUrl() {
  syncCatalogFilterUrl();
}

function matchesMetadata(age, difficulty) {
  return (!ageFilter?.value || age === ageFilter.value) &&
    (!difficultyFilter?.value || difficulty === difficultyFilter.value);
}


function updateSurpriseButton(message = "") {
  if (surpriseButton) surpriseButton.disabled = !Array.isArray(catalogEntries) || catalogEntries.length === 0;
  if (surpriseStatus) {
    surpriseStatus.textContent = message;
    surpriseStatus.hidden = !message;
  }
}

surpriseButton?.addEventListener("click", () => {
  // Reuse the same published entries and detail URL contract as gallery cards.
  if (!Array.isArray(catalogEntries) || !catalogEntries.length) return;
  const selected = catalogEntries[Math.floor(Math.random() * catalogEntries.length)];
  if (selected) window.location.assign(detailHref(selected.id));
});

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

function readCategoryFilterFromUrl() {
  const requested = new URLSearchParams(location.search).get("category") || "";
  activeCategory = runtimeCategoryIds.has(requested) ? requested : "";
}

async function loadCategoryRegistry() {
  const response = await fetch("/categories.json", { cache: "no-store" });
  if (!response.ok) throw new Error("managed categories unavailable");
  const doc = await response.json();
  if (!doc || doc.schema !== "rozkalns.coloring-pages.categories.v2" ||
    !Number.isSafeInteger(doc.revision) || doc.revision < 1 ||
    !Array.isArray(doc.categories) || doc.categories.length < CORE_CATEGORY_IDS.length ||
    doc.categories.length > 64 ||
    Object.keys(doc).sort().join(",") !== "categories,revision,schema") {
    throw new Error("invalid managed category registry");
  }
  const ids = new Set();
  const labels = new Map();
  for (const item of doc.categories) {
    if (!item || Object.keys(item).sort().join(",") !== "id,label" ||
      typeof item.id !== "string" ||
      !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.id) || item.id.length > 48 ||
      ["essen-natur", "seasonal"].includes(item.id) ||
      typeof item.label !== "string" || item.label.length < 1 || item.label.length > 80 ||
      item.label !== item.label.trim() || item.label !== item.label.normalize("NFC") ||
      /[\x00-\x1f\x7f]/.test(item.label) || ids.has(item.id)) {
      throw new Error("invalid managed category entry");
    }
    ids.add(item.id);
    labels.set(item.id, item.label);
  }
  if (!CORE_CATEGORY_IDS.every((id, i) => doc.categories[i].id === id)) {
    throw new Error("missing structural categories");
  }
  runtimeCategoryIds = ids;
  for (const [id, label] of labels) CATEGORY_LABELS[id] = label;
  const browser = document.querySelector(".category-browser");
  if (!browser) return;
  browser.querySelectorAll("[data-runtime-category]").forEach((item) => item.remove());
  for (const item of doc.categories.slice(CORE_CATEGORY_IDS.length)) {
    const link = document.createElement("a");
    link.className = "category-group category-group-vehicles category-direct";
    link.href = `index.html?category=${encodeURIComponent(item.id)}#neu`;
    link.dataset.runtimeCategory = item.id;
    link.dataset.filter = item.id;
    const copy = document.createElement("span");
    copy.className = "category-group-copy";
    const title = document.createElement("span");
    title.className = "category-group-name";
    title.textContent = item.label;
    copy.append(title);
    const arrow = document.createElement("span");
    arrow.className = "category-direct-arrow";
    arrow.setAttribute("aria-hidden", "true");
    arrow.textContent = "→";
    link.append(copy, arrow);
    browser.append(link);
    categoryButtons.push(link);
  }
}

function normalizeTopicText(value) {
  return normalize(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replaceAll("ß", "ss");
}

function parseMonthDay(value) {
  const match = /^(\\d{2})-(\\d{2})$/.exec(String(value || ""));
  if (!match) return null;
  const month = Number(match[1]);
  const day = Number(match[2]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  return month * 100 + day;
}

function topicIsCurrent(topic, date = new Date()) {
  const start = parseMonthDay(topic.active_from);
  const end = parseMonthDay(topic.active_to);
  if (!start || !end) return false;
  const current = (date.getMonth() + 1) * 100 + date.getDate();
  return start <= end ? current >= start && current <= end : current >= start || current <= end;
}

// Explicit membership is optional; legacy entries retain their single category.
// Invalid catalogue metadata never creates new category matches.
function entryCategoryIds(entry) {
  const primary = normalize(entry?.category);
  const assigned = entry?.categories;
  if (Array.isArray(assigned) && assigned.length > 0 && assigned[0] === primary &&
    assigned.every((id) => typeof id === "string" && runtimeCategoryIds.has(id)) &&
    new Set(assigned).size === assigned.length) return assigned;
  return runtimeCategoryIds.has(primary) ? [primary] : [];
}

function entryTopicIds(entry) {
  const known = new Set(topicRegistry.map((topic) => topic.id));
  if (Array.isArray(entry?.topics)) {
    return [...new Set(entry.topics.map((value) => normalize(value)).filter((value) => known.has(value)))];
  }

  const haystack = normalizeTopicText(`${entry?.title || ""} ${entry?.character || ""}`);
  if (!haystack) return [];
  return topicRegistry
    .filter((topic) => Array.isArray(topic.legacy_terms) && topic.legacy_terms.some((term) => haystack.includes(normalizeTopicText(term))))
    .map((topic) => topic.id);
}

function topicCounts(entries) {
  const counts = new Map();
  entries.forEach((entry) => {
    entryTopicIds(entry).forEach((topicId) => counts.set(topicId, (counts.get(topicId) || 0) + 1));
  });
  return counts;
}

function updateTopicButtons() {
  document.querySelectorAll("[data-topic-chip]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.topicChip === activeTopic));
  });
  if (topicClear) topicClear.hidden = !activeTopic;
  renderTopicExplorer();
}

function selectTopic(topicId, { toggle = true } = {}) {
  activeTopic = toggle && activeTopic === topicId ? "" : topicId;
  syncCatalogFilterUrl();
  updateTopicButtons();
  applyFilters();
  updateNavigation("#neu");
  document.querySelector("#neu")?.scrollIntoView({ block: "start" });
  document.querySelector("#gallery-title")?.focus({ preventScroll: true });
}

function createTopicButton(topic) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "topic-chip";
  button.dataset.topicChip = topic.id;
  button.setAttribute("aria-pressed", "false");

  if (topic.icon) {
    const icon = document.createElement("span");
    icon.className = "topic-chip-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = topic.icon;
    button.append(icon);
  }
  button.append(document.createTextNode(topic.label));
  button.addEventListener("click", () => selectTopic(topic.id));
  return button;
}

// The homepage starts with broad categories. Only a chosen topic is shown
// beside the results; secondary choices stay inside their parent disclosure.
function renderTopicExplorer() {
  const topic = topicRegistry.find((candidate) => candidate.id === activeTopic);
  if (topicExplorer) topicExplorer.hidden = !topic;
  if (topicList) {
    const button = topic ? createTopicButton(topic) : null;
    if (button) button.setAttribute("aria-pressed", "true");
    topicList.replaceChildren(...(button ? [button] : []));
  }
  const heading = document.querySelector("#gallery-title");
  if (heading) heading.textContent = topic ? `${topic.label} – Malvorlagen` : "Neue Malvorlagen";
}

// Native links still work before hydration and for new-tab/modified clicks.
document.querySelectorAll("[data-browse-topic]").forEach((link) => {
  link.addEventListener("click", (event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const id = link.dataset.browseTopic;
    if (!Array.isArray(catalogEntries) || !topicRegistry.some((topic) => topic.id === id)) return;
    event.preventDefault();
    activeCategory = "";
    selectTopic(id, { toggle: false });
  });
});

async function loadTopicRegistry() {
  try {
    const response = await fetch("/topics.json", { cache: "no-store" });
    if (!response.ok) throw new Error("topic registry unavailable");
    const payload = await response.json();
    if (payload?.schema !== "rozkalns.coloring-pages.topics.v1" || !Array.isArray(payload.topics)) {
      throw new Error("invalid topic registry");
    }
    topicRegistry = payload.topics.filter((topic) =>
      topic && typeof topic.id === "string" && typeof topic.label === "string" && ["seasonal", "evergreen"].includes(topic.kind)
    );
  } catch {
    topicRegistry = [];
    if (topicExplorer) topicExplorer.hidden = true;
  }
}

function currentCards() {
  return [...document.querySelectorAll(".coloring-card")];
}

function updateCatalogCounts(entries = null) {
  const cards = Array.isArray(entries) ? [] : currentCards();
  const memberships = Array.isArray(entries)
    ? entries.map(entryCategoryIds)
    : cards.map((card) => card.dataset.categories ? card.dataset.categories.split(",") : [card.dataset.category]);
  const counts = new Map();

  memberships.forEach((categories) => {
    new Set(categories.map((value) => normalize(value))).forEach((category) => {
      if (category) counts.set(category, (counts.get(category) || 0) + 1);
    });
  });

  categoryButtons.forEach((button) => {
    const category = categoryButtonId(button);
    const value = button.querySelector("[data-category-count]");
    if (!value) return;
    const collectionTopics = DISCOVERY_COLLECTION_TOPICS[category];
    if (Array.isArray(entries) && collectionTopics) {
      value.textContent = String(entries.filter((entry) =>
        entryTopicIds(entry).some((topicId) => collectionTopics.has(topicId))
      ).length);
      return;
    }
    value.textContent = String(counts.get(category) || 0);
  });

  if (totalCount) totalCount.textContent = String(Array.isArray(entries) ? entries.length : cards.length);
}

function updateCount(totalMatches) {
  if (resultCount) {
    resultCount.textContent = `${totalMatches} ${totalMatches === 1 ? "Malvorlage" : "Malvorlagen"}`;
  }
  if (emptyState) {
    emptyState.textContent = catalogIssueText || "Keine passenden Malvorlagen gefunden.";
    emptyState.hidden = totalMatches !== 0;
  }
}

function matchesFilters(titleValue, categoryValues, topicValues = [], ageValue = "", difficultyValue = "") {
  const query = normalize(searchInput?.value ?? "");
  const title = normalize(titleValue ?? "");
  const categories = (Array.isArray(categoryValues) ? categoryValues : [categoryValues]).map(normalize).filter(Boolean);
  const matchesQuery = !query || title.includes(query) || categories.some((id) =>
    id.includes(query) || normalize(CATEGORY_LABELS[id] || id).includes(query));
  const collectionTopics = DISCOVERY_COLLECTION_TOPICS[activeCategory];
  const matchesCategory = !activeCategory ||
    (collectionTopics
      ? topicValues.some((topicId) => collectionTopics.has(topicId))
      : categories.includes(activeCategory));
  const matchesTopic = !activeTopic || topicValues.includes(activeTopic);
  return matchesQuery && matchesCategory && matchesTopic && matchesMetadata(ageValue, difficultyValue);
}

function renderCatalog() {
  if (!gallery || !Array.isArray(catalogEntries)) return;

  const matches = catalogEntries.filter((entry) => matchesFilters(entry.title, entryCategoryIds(entry), entryTopicIds(entry), entry.age, entry.difficulty));
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
    const show = matchesFilters(card.dataset.title, card.dataset.categories ? card.dataset.categories.split(",") : [card.dataset.category], [], card.dataset.age, card.dataset.difficulty);
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
  card.dataset.categories = entryCategoryIds(entry).join(",");

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

  // Unknown legacy metadata is not an age recommendation or difficulty rating.
  if (AGE_FILTER_VALUES.has(entry.age)) {
    const ageClass = entry.age === "4-8" ? "age age-older" : "age";
    badges.append(createBadge(`${entry.age} Jahre`, ageClass));
  }

  const difficultyLabel = DIFFICULTY_LABELS[entry.difficulty];
  if (difficultyLabel) {
    const difficultyClass = entry.difficulty === "easy" ? "easy"
      : entry.difficulty === "detailed" ? "detailed" : "medium";
    badges.append(createBadge(difficultyLabel, difficultyClass));
  }

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
  if (!panel || !button || button.disabled) return;

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
    const available = rankingTabs.filter((candidate) => !candidate.disabled);
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

function rankingsUnavailable() {
  if (rankingStatus) {
    rankingStatus.textContent = "Die Ranglisten sind gerade nicht verfügbar. Entdecke weiter unten unsere Malvorlagen.";
  }
  rankingRoot?.setAttribute("aria-busy", "false");
}

async function hydrateRankings(entries) {
  if (!window.ColoringStats?.getRankings) {
    rankingsUnavailable();
    return;
  }
  try {
    const data=await window.ColoringStats.getRankings(6);
    const available = new Map([
      ["trending", renderRanking("trending",entries,data.trending)],
      ["popular", renderRanking("popular",entries,data.popular)],
    ]);
    rankingTabs.forEach((button) => {
      button.disabled = !available.get(button.dataset.rankingTab);
    });
    const initialKind = available.get("trending")
      ? "trending"
      : available.get("popular")
        ? "popular"
        : "";
    if (!initialKind) {
      rankingsUnavailable();
      return;
    }
    setRankingTab(initialKind);
    if (rankingStatus) rankingStatus.hidden = true;
    rankingRoot?.setAttribute("aria-busy", "false");
  } catch {
    rankingsUnavailable();
  }
}
async function hydrateCatalog() {
  if (!gallery) return;

  try {
    await loadCategoryRegistry();
    readCategoryFilterFromUrl();
    await loadTopicRegistry();
    readTopicFilterFromUrl();
    const response = await fetch("catalog.json", { cache: "no-store" });
    if (!response.ok) throw new Error("catalog unavailable");

    const catalog = await response.json();
    if (!Array.isArray(catalog)) throw new Error("invalid catalog");

    const entries = catalog.filter((entry) => entry && entry.id && entry.title && entry.thumb);
    catalogIssueText = entries.length ? "" : "Zurzeit sind keine Malvorlagen verfügbar.";
    catalogEntries = entries;
    updateSurpriseButton(entries.length ? "" : "Zurzeit sind keine Malvorlagen für die Zufallsauswahl verfügbar.");
    visibleLimit = CATALOG_PAGE_SIZE;
    updateCatalogCounts(catalogEntries);
    renderTopicExplorer(catalogEntries);
    renderCatalog();
    try {
      // Editorial feature is optional; never interrupt browse/preview/print.
      window.AusmalWeekly?.render(catalogEntries);
    } catch {
      // A missing/broken optional feature must not block the catalogue.
    }
    if (entries.length) await hydrateRankings(catalogEntries);
    else rankingsUnavailable();
  } catch {
    // Never present demonstration cards as real published media on a failed load.
    catalogIssueText = "Die Malvorlagen konnten nicht geladen werden. Bitte versuche es später erneut.";
    catalogEntries = [];
    updateSurpriseButton("Die Zufallsauswahl ist gerade nicht verfügbar.");
    visibleLimit = CATALOG_PAGE_SIZE;
    updateCatalogCounts(catalogEntries);
    renderTopicExplorer(catalogEntries);
    renderCatalog();
    rankingsUnavailable();
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

[ageFilter, difficultyFilter].forEach((control) => {
  control?.addEventListener("change", () => {
    syncMetadataFilterUrl();
    applyFilters();
  });
});
window.addEventListener("popstate", () => {
  readMetadataFiltersFromUrl();
  readCategoryFilterFromUrl();
  readTopicFilterFromUrl();
  updateTopicButtons();
  applyFilters();
});

topicClear?.addEventListener("click", () => {
  activeTopic = "";
  syncCatalogFilterUrl();
  updateTopicButtons();
  applyFilters();
  document.querySelector("#gallery-title")?.focus({ preventScroll: true });
});

loadMoreButton?.addEventListener("click", () => {
  if (!Array.isArray(catalogEntries)) return;
  visibleLimit += CATALOG_PAGE_SIZE;
  renderCatalog();
});

categoryButtons.forEach((button) => {
  // Category destinations are ordinary crawlable links, not toggle buttons.
  if (button.tagName === "A") return;
  button.setAttribute("aria-pressed", "false");
  button.addEventListener("click", () => {
    const category = categoryButtonId(button);
    activeCategory = activeCategory === category ? "" : category;

    categoryButtons.forEach((candidate) => {
      const selected = categoryButtonId(candidate) === activeCategory;
      candidate.classList.toggle("is-active", selected);
      candidate.setAttribute("aria-pressed", String(selected));
    });

    applyFilters();
    updateNavigation("#neu");
    document.querySelector("#neu")?.scrollIntoView({ block: "start" });
  });
});

document.querySelectorAll("[data-reset-filters]").forEach((link) => link.addEventListener("click", () => {
  activeCategory = "";
  activeTopic = "";
  if (searchInput) searchInput.value = "";
  if (ageFilter) ageFilter.value = "";
  if (difficultyFilter) difficultyFilter.value = "";
  syncCatalogFilterUrl();
  categoryButtons.forEach((button) => {
    button.classList.remove("is-active");
    if (button.tagName !== "A") button.setAttribute("aria-pressed", "false");
  });
  updateTopicButtons();
  applyFilters();
}));

readMetadataFiltersFromUrl();

if (gallery) {
  updateCatalogCounts();
  applyFilters();
  hydrateCatalog();
}
