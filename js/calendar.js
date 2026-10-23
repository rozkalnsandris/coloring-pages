"use strict";

const panels = [...document.querySelectorAll("[data-calendar-month]")];
const monthButtons = [...document.querySelectorAll("[data-calendar-select]")];
const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");
const ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,79}$/i;
const STRICT_EXPLICIT_TOPICS = new Set([
  "fasching", "ostern", "muttertag", "sankt-martin", "advent", "nikolaus", "weihnachten"
]);
const MONTH_NAMES = [
  "", "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember"
];

function berlinYearMonth(instant = new Date()) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Berlin", year: "numeric", month: "numeric"
  }).formatToParts(instant);
  return {
    year: Number(parts.find((part) => part.type === "year").value),
    month: Number(parts.find((part) => part.type === "month").value)
  };
}

function easterUtc(year) {
  const a = year % 19, b = Math.floor(year / 100), c = year % 100;
  const d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4), k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = (h + l - 7 * m + 114) % 31 + 1;
  return new Date(Date.UTC(year, month - 1, day));
}

function movableMonth(year, daysBeforeEaster) {
  const date = easterUtc(year);
  date.setUTCDate(date.getUTCDate() - daysBeforeEaster);
  return date.getUTCMonth() + 1;
}

function createTopicSection(title, topic) {
  const row = document.createElement("article");
  row.className = "calendar-topic";
  row.dataset.calendarTopic = topic;

  const heading = document.createElement("div");
  heading.className = "calendar-topic-heading";

  const icon = document.createElement("span");
  icon.className = "calendar-topic-icon";
  icon.dataset.calendarIcon = "";
  icon.setAttribute("aria-hidden", "true");

  const copy = document.createElement("div");
  const name = document.createElement("h3");
  name.textContent = title;
  const count = document.createElement("p");
  count.dataset.calendarCount = "";
  count.textContent = "Malvorlagen werden geladen …";
  copy.append(name, count);

  const all = document.createElement("a");
  all.className = "outline-link";
  all.dataset.calendarAll = "";
  all.hidden = true;
  all.href = "index.html?topic=" + encodeURIComponent(topic) + "#neu";
  all.append(document.createTextNode("Alle " + title + "-Ausmalbilder "), document.createTextNode("→"));

  const results = document.createElement("div");
  results.className = "calendar-preview-strip";
  results.dataset.calendarResults = "";
  results.setAttribute("aria-label", title + " Malvorlagen");

  const empty = document.createElement("p");
  empty.className = "calendar-topic-empty";
  empty.dataset.calendarEmpty = "";
  empty.hidden = true;
  empty.textContent = "Noch keine passenden Malvorlagen veröffentlicht.";

  heading.append(icon, copy, all);
  row.append(heading, results, empty);
  return row;
}

function addMovableTheme(month, title, topic) {
  const panel = panels.find((item) => Number(item.dataset.calendarMonth) === month);
  if (!panel || panel.querySelector('[data-calendar-topic="' + topic + '"]')) return;
  panel.querySelector(".calendar-topic-list")?.append(createTopicSection(title, topic));
}

function normalize(text) {
  return String(text || "").toLocaleLowerCase("de-DE").normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "").replaceAll("ß", "ss").trim();
}

function entryIsUsable(entry) {
  return Boolean(entry && ID_PATTERN.test(String(entry.id || "")) &&
    typeof entry.title === "string" && entry.title.trim() && entry.thumb);
}

function legacyTopicMatch(entry, topic, registryTopic) {
  if (STRICT_EXPLICIT_TOPICS.has(topic) || !Array.isArray(registryTopic?.legacy_terms)) return false;
  const haystack = normalize(String(entry.title || "") + " " + String(entry.character || ""));
  return registryTopic.legacy_terms
    .filter((term) => typeof term === "string")
    .map(normalize)
    .filter(Boolean)
    .some((term) => haystack.includes(term));
}

function matchingEntries(entries, topic, registryTopic) {
  return entries.filter((entry) => {
    if (!entryIsUsable(entry)) return false;
    if (Array.isArray(entry.topics)) return entry.topics.includes(topic);
    return legacyTopicMatch(entry, topic, registryTopic);
  });
}

function createPreviewCard(entry) {
  const card = document.createElement("article");
  card.className = "calendar-preview-card";

  const imageLink = document.createElement("a");
  imageLink.className = "calendar-preview-image";
  imageLink.href = "detail.html?id=" + encodeURIComponent(String(entry.id));
  imageLink.setAttribute("aria-label", entry.title + " ansehen");

  const image = document.createElement("img");
  image.src = entry.thumb;
  image.alt = entry.title;
  image.loading = "lazy";
  image.decoding = "async";
  imageLink.append(image);

  const titleLink = document.createElement("a");
  titleLink.className = "calendar-preview-title";
  titleLink.href = imageLink.href;
  titleLink.textContent = entry.title;

  card.append(imageLink, titleLink);
  return card;
}

function renderTopic(row, entries, topics) {
  const topic = row.dataset.calendarTopic;
  const registryTopic = topics.get(topic);
  const matches = matchingEntries(entries, topic, registryTopic);
  const count = row.querySelector("[data-calendar-count]");
  const results = row.querySelector("[data-calendar-results]");
  const empty = row.querySelector("[data-calendar-empty]");
  const all = row.querySelector("[data-calendar-all]");
  const icon = row.querySelector("[data-calendar-icon]");

  if (icon) icon.textContent = registryTopic?.icon || "✦";
  if (count) count.textContent = matches.length + (matches.length === 1 ? " Malvorlage" : " Malvorlagen");
  if (results) results.replaceChildren(...matches.map(createPreviewCard));
  if (empty) empty.hidden = matches.length !== 0;
  if (all) all.hidden = matches.length === 0;
  row.classList.remove("is-unavailable");
}

function renderUnavailable(row) {
  const count = row.querySelector("[data-calendar-count]");
  const results = row.querySelector("[data-calendar-results]");
  const empty = row.querySelector("[data-calendar-empty]");
  const all = row.querySelector("[data-calendar-all]");
  if (count) count.textContent = "Katalog gerade nicht verfügbar.";
  if (results) results.replaceChildren();
  if (empty) empty.hidden = true;
  if (all) all.hidden = true;
  row.classList.add("is-unavailable");
}

async function populateCalendar() {
  try {
    const [catalogResponse, topicsResponse] = await Promise.all([
      fetch("catalog.json", { cache: "no-store" }),
      fetch("/topics.json", { cache: "no-store" }).catch(() => null)
    ]);
    if (!catalogResponse.ok) throw new Error("catalog unavailable");
    const entries = await catalogResponse.json();
    if (!Array.isArray(entries)) throw new Error("invalid catalog");

    let topics = new Map();
    if (topicsResponse?.ok) {
      const registry = await topicsResponse.json().catch(() => null);
      if (registry?.schema === "rozkalns.coloring-pages.topics.v1" && Array.isArray(registry.topics)) {
        topics = new Map(registry.topics
          .filter((topic) => typeof topic?.id === "string")
          .map((topic) => [topic.id, topic]));
      }
    }

    document.querySelectorAll("[data-calendar-topic]").forEach((row) => renderTopic(row, entries, topics));
  } catch {
    document.querySelectorAll("[data-calendar-topic]").forEach(renderUnavailable);
  }
}

function selectMonth(month, { focus = false } = {}) {
  panels.forEach((panel) => {
    const selected = Number(panel.dataset.calendarMonth) === month;
    panel.classList.toggle("is-selected", selected);
    panel.hidden = !selected;
  });

  monthButtons.forEach((button) => {
    const selected = Number(button.dataset.calendarSelect) === month;
    button.setAttribute("aria-selected", String(selected));
    button.tabIndex = selected ? 0 : -1;
    if (selected && focus) button.focus();
  });
}

function initMonthNavigation(currentMonth) {
  monthButtons.forEach((button) => {
    const month = Number(button.dataset.calendarSelect);
    button.classList.toggle("is-current", month === currentMonth);
    button.addEventListener("click", () => selectMonth(month));
    button.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      const index = monthButtons.indexOf(button);
      let next = index;
      if (event.key === "ArrowLeft") next = (index - 1 + monthButtons.length) % monthButtons.length;
      if (event.key === "ArrowRight") next = (index + 1) % monthButtons.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = monthButtons.length - 1;
      event.preventDefault();
      selectMonth(Number(monthButtons[next].dataset.calendarSelect), { focus: true });
    });
  });
  selectMonth(currentMonth);
  monthButtons.find((button) => Number(button.dataset.calendarSelect) === currentMonth)
    ?.scrollIntoView({ inline: "center", block: "nearest" });
}

function initMenu() {
  if (!menuButton || !mobileNav) return;
  const setOpen = (open) => {
    mobileNav.hidden = !open;
    menuButton.setAttribute("aria-expanded", String(open));
    const label = menuButton.querySelector(".sr-only");
    if (label) label.textContent = open ? "Menü schließen" : "Menü öffnen";
  };
  menuButton.addEventListener("click", () => setOpen(mobileNav.hidden));
  mobileNav.addEventListener("click", (event) => {
    if (event.target.closest("a")) setOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !mobileNav.hidden) {
      setOpen(false);
      menuButton.focus();
    }
  });
}

const today = berlinYearMonth();
const yearLabel = document.querySelector("[data-calendar-year]");
const currentLabel = document.querySelector("[data-calendar-current-label]");
if (yearLabel) yearLabel.textContent = "Themen für " + today.year;
if (currentLabel) currentLabel.textContent = "Aktuell: " + MONTH_NAMES[today.month];

addMovableTheme(movableMonth(today.year, 48), "Fasching", "fasching");
addMovableTheme(movableMonth(today.year, 0), "Ostern", "ostern");
initMonthNavigation(today.month);
initMenu();
populateCalendar();
