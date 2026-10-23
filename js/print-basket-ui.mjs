import { addBasketActivity, clearBasket, expandBasketForExport, moveBasketActivity, removeBasketActivity } from "./print-basket-selection.mjs";
import { readStoredBasketIds, restoreStoredBasket, writeStoredBasketIds } from "./print-basket-storage.mjs";
import { prepareBasketPngZip } from "./print-basket-zip-fetch.mjs";
import { stageBasketZipDownloadLink } from "./print-basket-zip-link.mjs";

const MAX_SHEETS = 5;
const CARD_SELECTOR = ".coloring-card";
const TOGGLE_SELECTOR = "[data-basket-toggle]";

let catalog = [];
let catalogById = new Map();
let basket = { ids: [], pages: [], sheetCount: 0, droppedIds: [] };
let summary = null;
let dialog = null;
let status = null;
let observer = null;
let zipController = null;
let stagedZip = null;
let zipBusy = false;
let zipEpoch = 0;

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

  const root = document.createElement("button");
  root.type = "button";
  root.disabled = true;
  root.className = "basket-summary";
  root.setAttribute("aria-haspopup", "dialog");
  root.setAttribute("aria-controls", "basket-dialog");
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


function panelButton(text, action, id = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = text;
  button.dataset.basketAction = action;
  if (id) button.dataset.basketId = id;
  return button;
}


function resetZip() {
  zipEpoch++;
  zipController?.abort();
  zipController = null;
  zipBusy = false;
  if (stagedZip) {
    stagedZip.link.remove();
    stagedZip.dispose();
    stagedZip = null;
  }
  dialog?.querySelector("[data-basket-zip-link]")?.replaceChildren();
  const message = dialog?.querySelector("[data-basket-zip-status]");
  if (message) message.textContent = "";
  const prepare = dialog?.querySelector("[data-basket-zip-prepare]");
  if (prepare) prepare.disabled = basket.ids.length === 0;
  const cancel = dialog?.querySelector("[data-basket-zip-cancel]");
  if (cancel) cancel.disabled = true;
}

async function prepareZip() {
  if (!dialog?.open || zipBusy || basket.ids.length === 0) return;
  resetZip();
  const epoch = zipEpoch;
  const controller = new AbortController();
  zipController = controller;
  zipBusy = true;
  const prepare = dialog.querySelector("[data-basket-zip-prepare]");
  const cancel = dialog.querySelector("[data-basket-zip-cancel]");
  const message = dialog.querySelector("[data-basket-zip-status]");
  prepare.disabled = true;
  cancel.disabled = false;
  message.textContent = "Druckseiten werden geprüft und als ZIP vorbereitet …";

  try {
    const selectedIds = readStoredBasketIds();
    if (JSON.stringify(selectedIds) !== JSON.stringify(basket.ids)) {
      throw new Error("Selection changed in sessionStorage");
    }
    const response = await fetch("/catalog.json", {
      cache: "no-store", credentials: "omit", redirect: "error", signal: controller.signal,
    });
    if (!response.ok || response.redirected) throw new Error("Fresh catalogue unavailable");
    const catalogFresh = await response.json();
    const pages = expandBasketForExport(selectedIds, catalogFresh);
    if (pages.length !== basket.sheetCount ||
        pages.some((page, index) => page.activityId !== basket.pages[index]?.activityId ||
          page.pageIndex !== basket.pages[index]?.pageIndex ||
          page.printUrl !== basket.pages[index]?.printUrl)) {
      throw new Error("Published selection changed; review before export");
    }
    const zip = await prepareBasketPngZip(pages, {
      origin: window.location.origin, signal: controller.signal,
    });
    if (epoch !== zipEpoch || controller.signal.aborted || !dialog.open) return;
    const staged = stageBasketZipDownloadLink(zip);
    const slot = dialog.querySelector("[data-basket-zip-link]");
    if (!slot) {
      staged.dispose();
      throw new Error("ZIP destination missing");
    }
    staged.link.className = "basket-zip-download";
    slot.replaceChildren(staged.link);
    stagedZip = staged;
    message.textContent = "ZIP bereit. Mit „Als ZIP speichern“ herunterladen.";
  } catch {
    if (epoch === zipEpoch && dialog.open && !controller.signal.aborted) {
      message.textContent = "ZIP konnte nicht vorbereitet werden. Bitte Auswahl prüfen und erneut versuchen.";
    }
  } finally {
    if (epoch === zipEpoch) {
      zipBusy = false;
      zipController = null;
      prepare.disabled = basket.ids.length === 0;
      cancel.disabled = true;
    }
  }
}

function createDialog() {
  const node = document.createElement("dialog");
  node.id = "basket-dialog";
  node.className = "basket-dialog";
  node.setAttribute("aria-labelledby", "basket-dialog-title");
  const header = document.createElement("div");
  header.className = "basket-dialog-header";
  const heading = document.createElement("h2");
  heading.id = "basket-dialog-title";
  heading.textContent = "Meine Drucksammlung";
  const close = panelButton("Schließen", "close");
  close.autofocus = true;
  header.append(heading, close);
  const count = document.createElement("p");
  count.dataset.basketDialogCount = "";
  count.setAttribute("aria-live", "polite");
  const list = document.createElement("ul");
  list.dataset.basketItems = "";
  list.className = "basket-dialog-list";
  const empty = document.createElement("p");
  empty.dataset.basketEmpty = "";
  empty.textContent = "Noch keine Malvorlagen ausgewählt.";
  const clear = panelButton("Leeren", "clear");
  clear.dataset.basketClear = "";
  const printAction = panelButton("Alles drucken", "print");
  printAction.dataset.basketPrint = "";
  printAction.disabled = true; // Keep held until browser and physical A4 QA.
  printAction.setAttribute("aria-describedby", "basket-print-unavailable");
  const zipPrepare = panelButton("ZIP vorbereiten", "prepare-zip");
  zipPrepare.dataset.basketZipPrepare = "";
  zipPrepare.disabled = true;
  const zipCancel = panelButton("Abbrechen", "cancel-zip");
  zipCancel.dataset.basketZipCancel = "";
  zipCancel.disabled = true;
  const zipLink = document.createElement("div");
  zipLink.dataset.basketZipLink = "";
  const zipStatus = document.createElement("p");
  zipStatus.dataset.basketZipStatus = "";
  zipStatus.className = "basket-dialog-note";
  zipStatus.setAttribute("role", "status");
  zipStatus.setAttribute("aria-live", "polite");
  const note = document.createElement("p");
  note.id = "basket-print-unavailable";
  note.textContent = "Alles drucken ist noch nicht verfügbar.";
  note.className = "basket-dialog-note";
  node.append(header, count, list, empty, clear, printAction, zipPrepare, zipCancel, zipLink, zipStatus, note);
  document.body.append(node);

  node.addEventListener("click", (event) => {
    const button = event.target.closest("[data-basket-action]");
    if (!button || button.disabled || !node.contains(button)) return;
    const action = button.dataset.basketAction;
    const id = button.dataset.basketId;
    if (action === "close") return node.close();
    if (action === "prepare-zip") { void prepareZip(); return; }
    if (action === "cancel-zip") {
      resetZip();
      node.querySelector("[data-basket-zip-status]").textContent = "Abgebrochen.";
      return;
    }
    if (action === "clear") {
      if (basket.ids.length) commitBasket(clearBasket(), "Drucksammlung geleert.");
      return;
    }
    if (!basket.ids.includes(id)) return;
    let next = null;
    if (action === "remove") next = removeBasketActivity(basket.ids, id, catalog);
    if (action === "up" || action === "down") {
      next = moveBasketActivity(basket.ids, id, action === "up" ? -1 : 1, catalog);
    }
    if (next) commitBasket(next, action === "remove" ? "Malvorlage entfernt." : "Reihenfolge geändert.", action, id);
  });
  node.addEventListener("close", () => { resetZip(); summary?.focus(); });
  return node;
}

function renderDialog() {
  if (!dialog) return;
  const fragment = document.createDocumentFragment();
  for (const [index, id] of basket.ids.entries()) {
    const entry = catalogById.get(id);
    if (!entry) continue;
    const row = document.createElement("li");
    row.className = "basket-dialog-item";
    const thumb = entry.thumb;
    if (typeof thumb === "string" && new RegExp("^/?media/" + id + "/thumb(?:[-.][a-z0-9]+)?\\.webp$").test(thumb)) {
      const image = document.createElement("img");
      image.src = thumb.startsWith("/") ? thumb : "/" + thumb;
      image.alt = "";
      image.loading = "lazy";
      row.append(image);
    }
    const info = document.createElement("div");
    info.className = "basket-dialog-details";
    const link = document.createElement("a");
    link.href = "/detail.html?id=" + encodeURIComponent(id);
    link.textContent = entry.title;
    const sheetCount = basket.pages.filter((page) => page.activityId === id).length;
    const pages = document.createElement("span");
    pages.textContent = sheetCount + (sheetCount === 1 ? " Seite" : " Seiten");
    info.append(link, pages);
    const actions = document.createElement("div");
    actions.className = "basket-dialog-actions";
    for (const [label, action, disabled] of [
      ["Nach oben", "up", index === 0],
      ["Nach unten", "down", index === basket.ids.length - 1],
      ["Entfernen", "remove", false]
    ]) {
      const button = panelButton(label, action, id);
      button.disabled = disabled;
      button.setAttribute("aria-label", label + ": " + entry.title);
      actions.append(button);
    }
    row.append(info, actions);
    fragment.append(row);
  }
  dialog.querySelector("[data-basket-items]").replaceChildren(fragment);
  dialog.querySelector("[data-basket-dialog-count]").textContent =
    basket.sheetCount + "/5 Druckseiten ausgewählt (maximal 5).";
  dialog.querySelector("[data-basket-empty]").hidden = basket.ids.length !== 0;
  dialog.querySelector("[data-basket-clear]").disabled = basket.ids.length === 0;
  dialog.querySelector("[data-basket-zip-prepare]").disabled = basket.ids.length === 0 || zipBusy;
}

function setUnavailable(message) {
  resetZip();
  if (summary) {
    summary.disabled = true;
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

function commitBasket(next, message, action = null, id = null) {
  try {
    writeStoredBasketIds(next.ids);
  } catch {
    setUnavailable("Die Drucksammlung ist in diesem Tab nicht verfügbar.");
    return false;
  }
  resetZip();
  basket = next;
  syncSummary();
  syncButtons();
  renderDialog();
  if (dialog?.open) {
    const button = [...dialog.querySelectorAll("[data-basket-action]")].find(
      (candidate) => candidate.dataset.basketAction === action && candidate.dataset.basketId === id && !candidate.disabled
    );
    (button || dialog.querySelector("[data-basket-action=close]"))?.focus();
  }
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
  dialog = createDialog();
  window.addEventListener("pagehide", resetZip);
  summary?.addEventListener("click", () => {
    if (summary.disabled || typeof dialog.showModal !== "function") return;
    renderDialog();
    dialog.showModal();
  });

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
    renderDialog();
    if (summary && typeof dialog.showModal === "function") summary.disabled = false;
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
