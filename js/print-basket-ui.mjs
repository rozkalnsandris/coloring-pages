import { addBasketActivity, removeBasketActivity } from "./print-basket-selection.mjs";
import { restoreStoredBasket, writeStoredBasketIds } from "./print-basket-storage.mjs";

const MAX_SHEETS = 5;
const CARD_SELECTOR = ".coloring-card";
const TOGGLE_SELECTOR = "[data-basket-toggle]";

let catalog = [];
let catalogById = new Map();
let basket = { ids: [], pages: [], sheetCount: 0, droppedIds: [] };
let summary = null;
let status = null;
let observer = null;

function detailIdFromCard(card) {
  const link = card.querySelector('a[href*="detail.html"]');
  if (!link) return "";
  try {
    const url = new URL(link.getAttribute("href"), window.location.href);
    if (url.origin !== window.location.origin || !url.pathname.endsWith("/detail.html")) return "";
    return url.searchParams.get("id") || "";
  } catch {
    return "";
  }
}

function pageCount(entry) {
  return Array.isArray(entry?.pages) && entry.pages.length > 0 ? entry.pages.length : 1;
}

function makeStatusRegion() {
  const node = document.createElement("p");
  node.className = "sr-only";
  node.dataset.basketStatus = "";
  node.setAttribute("role", "status");
  node.setAttribute("aria-live", "polite");
  document.body.append(node);
  return node;
}

function makeSummary() {
  const header = document.querySelector(".header-inner");
  if (!header) return null;

  // Keep the indicator inside its true flex parent, not in the header grid.
  const actions = header.querySelector(".header-actions");
  if (!actions) return null;

  const root = document.createElement("div");
  root.className = "basket-summary";
  root.dataset.basketSummary = "";
  root.setAttribute("aria-live", "polite");

  const longLabel = document.createElement("span");
  longLabel.className = "basket-summary-long";
  longLabel.textContent = "Meine Drucksammlung";

  const shortLabel = document.createElement("span");
  shortLabel.className = "basket-summary-short";
  shortLabel.textContent = "Sammlung";
  shortLabel.setAttribute("aria-hidden", "true");

  const count = document.createElement("strong");
  count.dataset.basketCount = "";

  root.append(longLabel, shortLabel, count);
  const menu = actions.querySelector(".menu-button");
  if (menu) actions.insertBefore(root, menu);
  else actions.append(root);
  return root;
}

function announce(message) {
  if (!status) return;
  status.textContent = "";
  queueMicrotask(() => { status.textContent = message; });
}

function syncSummary() {
  if (!summary) return;
  const count = summary.querySelector("[data-basket-count]");
  if (count) count.textContent = basket.sheetCount + "/" + MAX_SHEETS + " Seiten";
  summary.setAttribute(
    "aria-label",
    "Meine Drucksammlung (" + basket.sheetCount + "/" + MAX_SHEETS + " Seiten)"
  );
}

function syncButton(button) {
  const id = button.dataset.basketToggle || "";
  const entry = catalogById.get(id);
  const selected = basket.ids.includes(id);
  button.setAttribute("aria-pressed", String(selected));
  button.textContent = selected ? "Entfernen" : "Hinzufügen";
  if (entry) {
    const sheets = pageCount(entry);
    button.setAttribute(
      "aria-label",
      "Drucksammlung: " + entry.title + " (" + sheets + (sheets === 1 ? " Seite)" : " Seiten)")
    );
  }
}

function syncButtons() {
  document.querySelectorAll(TOGGLE_SELECTOR).forEach(syncButton);
}

function createToggle(id, detail = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = detail ? "basket-toggle basket-toggle-detail" : "basket-toggle";
  button.dataset.basketToggle = id;
  syncButton(button);
  return button;
}

function enhanceCards() {
  document.querySelectorAll(CARD_SELECTOR).forEach((card) => {
    if (card.querySelector(TOGGLE_SELECTOR)) return;
    const id = detailIdFromCard(card);
    if (!id || !catalogById.has(id)) return;
    card.append(createToggle(id));
  });
}

function enhanceDetail() {
  const actions = document.querySelector(".detail-actions");
  if (!actions || actions.querySelector(TOGGLE_SELECTOR)) return;
  const id = new URLSearchParams(window.location.search).get("id") || "";
  if (!catalogById.has(id)) return;
  actions.append(createToggle(id, true));
}

function setUnavailable(message) {
  if (summary) {
    summary.classList.add("is-unavailable");
    summary.setAttribute("aria-label", "Drucksammlung nicht verfügbar");
    const count = summary.querySelector("[data-basket-count]");
    if (count) count.textContent = "nicht verfügbar";
  }
  document.querySelectorAll(TOGGLE_SELECTOR).forEach((button) => {
    button.disabled = true;
  });
  announce(message);
}

function commitBasket(next, message) {
  try {
    writeStoredBasketIds(next.ids);
  } catch {
    setUnavailable("Die Drucksammlung ist in diesem Tab nicht verfügbar.");
    return false;
  }
  basket = next;
  syncSummary();
  syncButtons();
  announce(message);
  return true;
}

function handleToggle(button) {
  const id = button.dataset.basketToggle || "";
  const entry = catalogById.get(id);
  if (!entry) {
    announce("Diese Vorlage ist gerade nicht für die Drucksammlung verfügbar.");
    return;
  }

  const selected = basket.ids.includes(id);
  const next = selected
    ? removeBasketActivity(basket.ids, id, catalog)
    : addBasketActivity(basket.ids, id, catalog);

  if (!selected && !next.ok) {
    if (next.reason === "limit") {
      announce("Maximal 5 Druckseiten. Entferne zuerst eine Vorlage aus der Drucksammlung.");
    } else {
      announce("Diese Vorlage ist gerade nicht für die Drucksammlung verfügbar.");
    }
    return;
  }

  const message = selected
    ? entry.title + " wurde aus der Drucksammlung entfernt."
    : entry.title + " wurde zur Drucksammlung hinzugefügt.";
  commitBasket(next, message);
}

document.addEventListener("click", (event) => {
  const button = event.target.closest(TOGGLE_SELECTOR);
  if (!button || button.disabled) return;
  handleToggle(button);
});

async function start() {
  summary = makeSummary();
  status = makeStatusRegion();

  try {
    const response = await fetch("/catalog.json", { cache: "no-store", credentials: "same-origin" });
    if (!response.ok) throw new Error("catalog unavailable");
    const payload = await response.json();
    if (!Array.isArray(payload)) throw new Error("invalid catalog");
    catalog = payload;

    const counts = new Map();
    for (const entry of catalog) {
      if (typeof entry?.id === "string") counts.set(entry.id, (counts.get(entry.id) || 0) + 1);
    }
    catalogById = new Map(
      catalog
        .filter((entry) => entry && typeof entry.id === "string" && typeof entry.title === "string" && counts.get(entry.id) === 1)
        .map((entry) => [entry.id, entry])
    );

    basket = restoreStoredBasket(catalog);
    syncSummary();
    enhanceCards();
    enhanceDetail();

    if (basket.droppedIds.length) {
      announce("Nicht mehr verfügbare Vorlagen wurden aus der Drucksammlung entfernt.");
    }

    observer = new MutationObserver(() => {
      // Only add missing controls; writing labels here would retrigger the observer.
      enhanceCards();
      enhanceDetail();
    });
    observer.observe(document.body, { childList: true, subtree: true });
  } catch {
    setUnavailable("Die Drucksammlung ist gerade nicht verfügbar. Du kannst weiterhin Vorlagen ansehen und einzeln drucken.");
  }
}

start();
