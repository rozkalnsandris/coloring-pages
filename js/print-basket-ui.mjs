import { addBasketActivity, clearBasket, expandBasketForExport, moveBasketActivity, removeBasketActivity } from "./print-basket-selection.mjs";
import { readStoredBasketIds, restoreStoredBasket, writeStoredBasketIds } from "./print-basket-storage.mjs";
import { prepareBasketPngZip } from "./print-basket-zip-fetch.mjs";
import { stageBasketZipDownloadLink } from "./print-basket-zip-link.mjs";
import { createBookCoverState, setBookCoverEnabled, updateBookCoverText } from "./book-cover-state.mjs";
import { buildBookPreviewPlan } from "./book-preview-plan.mjs";
import { createBookPreviewCursor, moveBookPreviewCursor, setBookPreviewSheet } from "./book-preview-navigation.mjs";
import { buildBookPreviewDisplay } from "./book-preview-media.mjs";
import {
  BOOK_COVER_BROWSER_RENDER_OPTIONS,
  BOOK_OUTPUT_RELEASE,
  planBookOutputControls,
} from "./book-output-release-gate.mjs";
import { prepareCurrentBookOutputSession } from "./book-output-session.mjs";

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
let previewPlan = null;
let previewCursor = null;
let bookCover = createBookCoverState();

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

function bookSheetCount() {
  return basket.sheetCount + (bookCover.enabled ? 1 : 0);
}

function syncSummary() {
  if (!summary) return;
  const total = bookSheetCount();
  const count = summary.querySelector("[data-basket-count]");
  if (count) count.textContent = total + "/" + MAX_SHEETS + " Seiten";
  summary.setAttribute(
    "aria-label",
    "Meine Drucksammlung (" + total + "/" + MAX_SHEETS + " Seiten)"
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


function resetPreview() {
  previewPlan = null;
  previewCursor = null;
  if (!dialog) return;
  const panel = dialog.querySelector("[data-basket-preview]");
  if (panel) panel.hidden = true;
  const image = dialog.querySelector("[data-basket-preview-image]");
  if (image) {
    image.removeAttribute("src");
    image.alt = "";
    image.hidden = false;
  }
  const cover = dialog.querySelector("[data-basket-preview-cover]");
  const coverTitle = dialog.querySelector("[data-basket-preview-cover-title]");
  const coverName = dialog.querySelector("[data-basket-preview-cover-name]");
  if (cover) cover.hidden = true;
  if (coverTitle) coverTitle.textContent = "";
  if (coverName) coverName.textContent = "";
  const page = dialog.querySelector("[data-basket-preview-page]");
  if (page) page.textContent = "";
  const previous = dialog.querySelector("[data-basket-preview-previous]");
  const next = dialog.querySelector("[data-basket-preview-next]");
  if (previous) previous.disabled = true;
  if (next) next.disabled = true;
}

function renderPreview() {
  if (!dialog || !previewPlan || !previewCursor) return;
  const display = buildBookPreviewDisplay(previewPlan, previewCursor, catalog);
  const panel = dialog.querySelector("[data-basket-preview]");
  const image = dialog.querySelector("[data-basket-preview-image]");
  const cover = dialog.querySelector("[data-basket-preview-cover]");
  const coverTitle = dialog.querySelector("[data-basket-preview-cover-title]");
  const coverName = dialog.querySelector("[data-basket-preview-cover-name]");
  const page = dialog.querySelector("[data-basket-preview-page]");
  const previous = dialog.querySelector("[data-basket-preview-previous]");
  const next = dialog.querySelector("[data-basket-preview-next]");
  if (!panel || !image || !cover || !coverTitle || !coverName || !page || !previous || !next) {
    throw new Error("Preview controls unavailable");
  }

  if (display.content.kind === "cover") {
    image.removeAttribute("src");
    image.alt = "";
    image.hidden = true;
    cover.hidden = false;
    coverTitle.textContent = display.content.title;
    coverName.textContent = display.content.name ? "Für " + display.content.name : "";
    coverName.hidden = !display.content.name;
  } else {
    const entry = catalogById.get(display.content.activityId);
    if (!entry) throw new Error("Preview activity unavailable");
    cover.hidden = true;
    coverTitle.textContent = "";
    coverName.textContent = "";
    image.hidden = false;
    image.src = display.content.previewUrl;
    image.alt = display.content.pageCount > 1
      ? entry.title + ", Seite " + display.content.pageIndex + " von " + display.content.pageCount
      : entry.title;
  }

  page.textContent = display.pageText;
  previous.textContent = display.previous.label;
  previous.disabled = display.previous.disabled;
  next.textContent = display.next.label;
  next.disabled = display.next.disabled;
  panel.hidden = false;
}

function openPreview() {
  try {
    previewPlan = buildBookPreviewPlan(basket.ids, catalog, bookCover);
    previewCursor = createBookPreviewCursor(previewPlan);
    renderPreview();
    dialog?.querySelector("#basket-preview-title")?.focus();
  } catch {
    resetPreview();
    announce("Die Vorschau ist gerade nicht verfügbar. Bitte Auswahl prüfen.");
  }
}

function refreshOpenPreview() {
  if (!previewPlan || !previewCursor) return;
  const sheetNumber = previewCursor.sheetNumber;
  previewPlan = buildBookPreviewPlan(basket.ids, catalog, bookCover);
  previewCursor = setBookPreviewSheet(
    previewPlan,
    Math.min(sheetNumber, previewPlan.sheetCount),
  );
  renderPreview();
}

function movePreview(direction) {
  try {
    if (!previewPlan || !previewCursor) return;
    previewCursor = moveBookPreviewCursor(previewPlan, previewCursor, direction);
    renderPreview();
  } catch {
    resetPreview();
    announce("Die Vorschau konnte nicht aktualisiert werden. Bitte neu öffnen.");
  }
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
  if (prepare) {
    const controls = planBookOutputControls({
      basketSheetCount: basket.sheetCount,
      coverEnabled: bookCover.enabled,
      busy: false,
    });
    prepare.disabled = !controls.zipEnabled;
  }
  const cancel = dialog?.querySelector("[data-basket-zip-cancel]");
  if (cancel) cancel.disabled = true;
}

async function prepareZip() {
  const initialControls = planBookOutputControls({
    basketSheetCount: basket.sheetCount,
    coverEnabled: bookCover.enabled,
    busy: zipBusy,
  });
  if (!dialog?.open || !initialControls.zipEnabled) return;

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
    let staged;

    if (bookCover.enabled) {
      // This branch is unreachable while the canonical production release flag
      // is false. Keep the full fresh-catalogue/session gate ready for a later
      // separately reviewed release without changing the existing coverless path.
      if (!BOOK_OUTPUT_RELEASE.coveredZip) {
        throw new Error("Covered ZIP release gate is closed");
      }
      const session = await prepareCurrentBookOutputSession(
        basket,
        bookCover,
        {
          mode: "zip",
          origin: window.location.origin,
          signal: controller.signal,
          coverRenderOptions: BOOK_COVER_BROWSER_RENDER_OPTIONS,
        },
      );
      staged = session.resource;
      if (epoch !== zipEpoch || controller.signal.aborted || !dialog.open) {
        staged.dispose();
        return;
      }
    } else {
      const selectedIds = readStoredBasketIds();
      if (JSON.stringify(selectedIds) !== JSON.stringify(basket.ids)) {
        throw new Error("Selection changed in sessionStorage");
      }
      const response = await fetch("/catalog.json", {
        cache: "no-store",
        credentials: "omit",
        redirect: "error",
        signal: controller.signal,
      });
      if (!response.ok || response.redirected) {
        throw new Error("Fresh catalogue unavailable");
      }
      const catalogFresh = await response.json();
      const pages = expandBasketForExport(selectedIds, catalogFresh);
      if (pages.length !== basket.sheetCount ||
          pages.some((page, index) =>
            page.activityId !== basket.pages[index]?.activityId ||
            page.pageIndex !== basket.pages[index]?.pageIndex ||
            page.printUrl !== basket.pages[index]?.printUrl)) {
        throw new Error("Published selection changed; review before export");
      }
      const zip = await prepareBasketPngZip(pages, {
        origin: window.location.origin,
        signal: controller.signal,
      });
      if (epoch !== zipEpoch || controller.signal.aborted || !dialog.open) return;
      if (JSON.stringify(readStoredBasketIds()) !== JSON.stringify(selectedIds) ||
          JSON.stringify(basket.ids) !== JSON.stringify(selectedIds)) {
        throw new Error("Selection changed during ZIP preparation");
      }
      staged = stageBasketZipDownloadLink(zip);
    }

    try {
      const slot = dialog.querySelector("[data-basket-zip-link]");
      if (!slot) throw new Error("ZIP destination missing");
      staged.link.className = "basket-zip-download";
      slot.replaceChildren(staged.link);
      stagedZip = staged;
    } catch (error) {
      staged.dispose();
      throw error;
    }
    message.textContent = "ZIP bereit. Mit „Als ZIP speichern“ herunterladen.";
  } catch {
    if (epoch === zipEpoch && dialog.open && !controller.signal.aborted) {
      message.textContent = "ZIP konnte nicht vorbereitet werden. Bitte Auswahl prüfen und erneut versuchen.";
    }
  } finally {
    if (epoch === zipEpoch) {
      zipBusy = false;
      zipController = null;
      const controls = planBookOutputControls({
        basketSheetCount: basket.sheetCount,
        coverEnabled: bookCover.enabled,
        busy: false,
      });
      prepare.disabled = !controls.zipEnabled;
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

  const coverControls = document.createElement("section");
  coverControls.className = "basket-cover-controls";
  coverControls.dataset.basketCoverControls = "";
  coverControls.setAttribute("aria-labelledby", "basket-cover-title");
  const coverHeading = document.createElement("h3");
  coverHeading.id = "basket-cover-title";
  coverHeading.textContent = "Deckblatt";
  const coverToggleLabel = document.createElement("label");
  coverToggleLabel.className = "basket-cover-toggle";
  const coverToggle = document.createElement("input");
  coverToggle.type = "checkbox";
  coverToggle.dataset.basketCoverToggle = "";
  const coverToggleText = document.createElement("span");
  coverToggleText.textContent = "Deckblatt hinzufügen";
  coverToggleLabel.append(coverToggle, coverToggleText);
  const coverHint = document.createElement("p");
  coverHint.className = "basket-dialog-note";
  coverHint.textContent = "Das Deckblatt zählt als eine von 5 A4-Druckseiten.";
  const coverFields = document.createElement("div");
  coverFields.className = "basket-cover-fields";
  const coverTitleLabel = document.createElement("label");
  coverTitleLabel.htmlFor = "basket-cover-title-input";
  coverTitleLabel.textContent = "Titel auf dem Deckblatt (optional)";
  const coverTitleInput = document.createElement("input");
  coverTitleInput.id = "basket-cover-title-input";
  coverTitleInput.type = "text";
  coverTitleInput.dataset.basketCoverTitle = "";
  coverTitleInput.setAttribute("autocomplete", "off");
  const coverNameLabel = document.createElement("label");
  coverNameLabel.htmlFor = "basket-cover-name-input";
  coverNameLabel.textContent = "Name auf dem Deckblatt (optional)";
  const coverNameInput = document.createElement("input");
  coverNameInput.id = "basket-cover-name-input";
  coverNameInput.type = "text";
  coverNameInput.dataset.basketCoverName = "";
  coverNameInput.setAttribute("autocomplete", "off");
  const coverPrivacy = document.createElement("p");
  coverPrivacy.className = "basket-dialog-note";
  coverPrivacy.textContent = "Titel und Name werden nicht gespeichert.";
  coverFields.append(coverTitleLabel, coverTitleInput, coverNameLabel, coverNameInput, coverPrivacy);
  coverControls.append(coverHeading, coverToggleLabel, coverHint, coverFields);

  const previewOpen = panelButton("Vorschau", "preview");
  previewOpen.dataset.basketPreviewOpen = "";
  previewOpen.disabled = true;
  const preview = document.createElement("section");
  preview.className = "basket-book-preview";
  preview.dataset.basketPreview = "";
  preview.hidden = true;
  preview.setAttribute("aria-labelledby", "basket-preview-title");
  const previewHeading = document.createElement("h3");
  previewHeading.id = "basket-preview-title";
  previewHeading.tabIndex = -1;
  previewHeading.textContent = "Vorschau";
  const previewPage = document.createElement("p");
  previewPage.dataset.basketPreviewPage = "";
  previewPage.setAttribute("role", "status");
  previewPage.setAttribute("aria-live", "polite");
  const previewFrame = document.createElement("figure");
  previewFrame.className = "basket-preview-frame";
  const previewImage = document.createElement("img");
  previewImage.dataset.basketPreviewImage = "";
  previewImage.alt = "";
  previewImage.decoding = "async";
  const previewCover = document.createElement("div");
  previewCover.className = "basket-preview-cover";
  previewCover.dataset.basketPreviewCover = "";
  previewCover.hidden = true;
  const previewCoverTitle = document.createElement("strong");
  previewCoverTitle.dataset.basketPreviewCoverTitle = "";
  const previewCoverName = document.createElement("p");
  previewCoverName.dataset.basketPreviewCoverName = "";
  previewCover.append(previewCoverTitle, previewCoverName);
  previewFrame.append(previewImage, previewCover);
  const previewControls = document.createElement("div");
  previewControls.className = "basket-preview-controls";
  const previewPrevious = panelButton("Zurück", "preview-previous");
  previewPrevious.dataset.basketPreviewPrevious = "";
  previewPrevious.disabled = true;
  const previewNext = panelButton("Weiter", "preview-next");
  previewNext.dataset.basketPreviewNext = "";
  previewNext.disabled = true;
  previewControls.append(previewPrevious, previewNext);
  preview.append(previewHeading, previewPage, previewFrame, previewControls);
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
  node.append(header, count, list, empty, coverControls, previewOpen, preview, clear, printAction, zipPrepare, zipCancel, zipLink, zipStatus, note);
  document.body.append(node);

  node.addEventListener("click", (event) => {
    const button = event.target.closest("[data-basket-action]");
    if (!button || button.disabled || !node.contains(button)) return;
    const action = button.dataset.basketAction;
    const id = button.dataset.basketId;
    if (action === "close") return node.close();
    if (action === "preview") { openPreview(); return; }
    if (action === "preview-previous") { movePreview(-1); return; }
    if (action === "preview-next") { movePreview(1); return; }
    if (action === "prepare-zip") { void prepareZip(); return; }
    if (action === "cancel-zip") {
      resetZip();
      node.querySelector("[data-basket-zip-status]").textContent = "Abgebrochen.";
      return;
    }
    if (action === "clear") {
      if (basket.ids.length || bookCover.enabled) {
        bookCover = createBookCoverState();
        commitBasket(clearBasket(), "Drucksammlung geleert.");
      }
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
  node.addEventListener("change", (event) => {
    const control = event.target;
    if (!control?.dataset || !Object.hasOwn(control.dataset, "basketCoverToggle")) return;
    try {
      bookCover = setBookCoverEnabled(bookCover, Boolean(control.checked), basket.ids, catalog);
      resetZip();
      resetPreview();
      syncSummary();
      renderDialog();
      announce(bookCover.enabled ? "Deckblatt hinzugefügt." : "Deckblatt entfernt.");
    } catch (error) {
      control.checked = bookCover.enabled;
      announce(
        basket.ids.length === 0
          ? "Wähle zuerst mindestens eine Druckseite aus."
          : "Maximal 5 A4-Druckseiten. Für ein Deckblatt muss zuerst eine Druckseite entfernt werden."
      );
    }
  });
  node.addEventListener("input", (event) => {
    const control = event.target;
    if (!control?.dataset) return;
    if (Object.hasOwn(control.dataset, "basketCoverTitle")) {
      bookCover = updateBookCoverText(bookCover, { title: control.value });
    } else if (Object.hasOwn(control.dataset, "basketCoverName")) {
      bookCover = updateBookCoverText(bookCover, { name: control.value });
    } else {
      return;
    }
    try {
      refreshOpenPreview();
    } catch {
      resetPreview();
      announce("Die Vorschau konnte nicht aktualisiert werden. Bitte neu öffnen.");
    }
  });
  node.addEventListener("close", () => { resetPreview(); });
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
  const total = bookSheetCount();
  dialog.querySelector("[data-basket-dialog-count]").textContent = bookCover.enabled
    ? total + "/5 Druckseiten ausgewählt (1 Deckblatt + " + basket.sheetCount + " " +
      (basket.sheetCount === 1 ? "Ausmalseite)." : "Ausmalseiten).")
    : total + "/5 Druckseiten ausgewählt (maximal 5).";
  dialog.querySelector("[data-basket-empty]").hidden = basket.ids.length !== 0;
  dialog.querySelector("[data-basket-clear]").disabled = basket.ids.length === 0;
  const coverToggle = dialog.querySelector("[data-basket-cover-toggle]");
  const coverTitle = dialog.querySelector("[data-basket-cover-title]");
  const coverName = dialog.querySelector("[data-basket-cover-name]");
  if (coverToggle) coverToggle.checked = bookCover.enabled;
  if (coverTitle) {
    coverTitle.value = bookCover.title;
    coverTitle.disabled = !bookCover.enabled;
  }
  if (coverName) {
    coverName.value = bookCover.name;
    coverName.disabled = !bookCover.enabled;
  }
  const outputControls = planBookOutputControls({
    basketSheetCount: basket.sheetCount,
    coverEnabled: bookCover.enabled,
    busy: zipBusy,
  });
  const zipPrepare = dialog.querySelector("[data-basket-zip-prepare]");
  zipPrepare.disabled = !outputControls.zipEnabled;
  const zipStatus = dialog.querySelector("[data-basket-zip-status]");
  if (!zipBusy) zipStatus.textContent = outputControls.zipStatus;
  dialog.querySelector("[data-basket-preview-open]").disabled = basket.ids.length === 0;
}

function setUnavailable(message) {
  resetZip();
  resetPreview();
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
  resetPreview();
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

  if (!selected && bookCover.enabled) {
    try {
      setBookCoverEnabled(bookCover, true, next.ids, catalog);
    } catch {
      announce("Maximal 5 A4-Druckseiten. Diese Malvorlage passt mit Deckblatt nicht mehr in deine Auswahl.");
      return;
    }
  }

  let message = selected
    ? entry.title + " wurde aus der Drucksammlung entfernt."
    : entry.title + " wurde zur Drucksammlung hinzugefügt.";
  if (selected && bookCover.enabled && next.ids.length === 0) {
    bookCover = setBookCoverEnabled(bookCover, false, next.ids, catalog);
    message += " Das Deckblatt wurde ebenfalls entfernt.";
  }
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
