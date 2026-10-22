"use strict";
const cards = [...document.querySelectorAll("[data-calendar-month]")];
const menuButton = document.querySelector(".menu-button");
const mobileNav = document.querySelector("#mobile-nav");
const ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,79}$/i;

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
function addMovableTheme(month, title, topic, terms) {
  const card = cards.find((item) => Number(item.dataset.calendarMonth) === month);
  if (!card) return;
  const row = document.createElement("li");
  row.className = "calendar-event";
  row.dataset.calendarTopic = topic;
  row.dataset.terms = terms;
  const label = document.createElement("strong");
  label.textContent = title;
  const status = document.createElement("span");
  status.dataset.calendarResult = "";
  status.textContent = "Vorlagen werden geprüft …";
  row.append(label, status);
  card.querySelector(".calendar-events").append(row);
}
function normalize(text) {
  return String(text || "").toLocaleLowerCase("de-DE").normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "").replaceAll("ß", "ss").trim();
}
function matchingEntry(entries, row, topics) {
  const topic = row.dataset.calendarTopic;
  const fallbacks = (row.dataset.terms || "").split("|").filter(Boolean);
  const terms = [...(topics.get(topic)?.legacy_terms || []), ...fallbacks]
    .filter((term) => typeof term === "string").map(normalize).filter(Boolean);
  return entries.find((entry) => {
    if (!entry || !ID_PATTERN.test(String(entry.id || "")) ||
        typeof entry.title !== "string" || !entry.title.trim() || !entry.thumb) return false;
    if (Array.isArray(entry.topics)) return entry.topics.includes(topic);
    const text = normalize(entry.title + " " + (typeof entry.character === "string" ? entry.character : ""));
    return terms.some((term) => text.includes(term));
  });
}
function setResult(row, entry, unavailable = false) {
  const target = row.querySelector("[data-calendar-result]");
  if (!target) return;
  if (!entry) {
    target.textContent = unavailable ? "Katalog gerade nicht verfügbar." : "Noch keine passende Vorlage.";
    return;
  }
  const link = document.createElement("a");
  link.href = "detail.html?id=" + encodeURIComponent(String(entry.id));
  link.textContent = "Vorlage ansehen: " + entry.title;
  target.replaceChildren(link);
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
          .filter((topic) => typeof topic?.id === "string").map((topic) => [topic.id, topic]));
      }
    }
    document.querySelectorAll("[data-calendar-topic]").forEach((row) =>
      setResult(row, matchingEntry(entries, row, topics)));
  } catch {
    document.querySelectorAll("[data-calendar-topic]").forEach((row) => setResult(row, null, true));
  }
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
const label = document.querySelector("[data-calendar-year]");
if (label) label.textContent = "Themen für " + today.year;
cards.forEach((card) => {
  const active = Number(card.dataset.calendarMonth) === today.month;
  card.classList.toggle("is-current", active);
  if (active) card.querySelector("h2")?.setAttribute("aria-current", "true");
});
// No hard-coded date: Rosenmontag is Easter - 48 days, Easter varies by year.
addMovableTheme(movableMonth(today.year, 48), "Fasching", "fasching", "fasching|karneval|clown|kostüm");
addMovableTheme(movableMonth(today.year, 0), "Ostern", "ostern", "ostern|osterhase|osterei");
initMenu();
populateCalendar();
