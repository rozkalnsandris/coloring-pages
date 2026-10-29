// Local-only #199 real-media staging harness.
// This file is served only by tools/print-basket-real-media-qa-server.py.
// It does not change production release flags and must never be treated as
// visitor, LIVE, mobile-memory or physical-paper approval.
import { reconcileBasket } from "/js/print-basket-selection.mjs";
import {
  BOOK_COVER_BROWSER_RENDER_OPTIONS,
} from "/js/book-output-release-gate.mjs";
import { prepareCurrentBookOutputSession } from "/js/book-output-session.mjs";
import { printStagedDocumentInBasketHost } from "/js/print-basket-print-host.mjs";

const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function parseActivityIds(value) {
  if (typeof value !== "string") throw new TypeError("ID input must be text");
  const ids = value.split(/[\s,]+/).map(x => x.trim()).filter(Boolean);
  if (!ids.length || ids.length > 5 || ids.some(id => !ID.test(id))) {
    throw new Error("Bitte 1–5 gültige veröffentlichte Aktivitäts-IDs eingeben.");
  }
  if (new Set(ids).size !== ids.length) {
    throw new Error("Aktivitäts-IDs dürfen nicht doppelt vorkommen.");
  }
  return Object.freeze(ids);
}

export function buildStagingBasket(ids, catalog) {
  const basket = reconcileBasket(ids, catalog);
  if (
    basket.ids.length !== ids.length ||
    basket.droppedIds.length !== 0 ||
    basket.sheetCount < 1 ||
    basket.sheetCount > 5
  ) {
    throw new Error("Auswahl ist im frischen Katalog nicht vollständig als 1–5 A4-Seiten verfügbar.");
  }
  return basket;
}

export function publicEvidence(basket, { mode = "validate", coverEnabled = false } = {}) {
  if (!basket || !Array.isArray(basket.ids) || !Array.isArray(basket.pages)) {
    throw new TypeError("Valid staging basket required");
  }
  return Object.freeze({
    schema: "ausmalwiese.book-real-media-staging-evidence.v1",
    status: "STAGING ONLY",
    mode,
    origin: globalThis.location?.origin || null,
    activityIds: Object.freeze([...basket.ids]),
    artworkSheetCount: basket.sheetCount,
    coverEnabled: Boolean(coverEnabled),
    totalSheetCount: basket.sheetCount + (coverEnabled ? 1 : 0),
    pages: Object.freeze(basket.pages.map(page => Object.freeze({
      activityId: page.activityId,
      pageIndex: page.pageIndex,
      pageCount: page.pageCount,
      printUrl: page.printUrl,
    }))),
  });
}

function coverState() {
  return Object.freeze({
    enabled: document.querySelector("#qa-cover-enabled").checked,
    title: document.querySelector("#qa-cover-title").value,
    name: document.querySelector("#qa-cover-name").value,
  });
}

async function freshBasket() {
  const ids = parseActivityIds(document.querySelector("#qa-ids").value);
  const response = await fetch("/catalog.json", {
    cache: "no-store",
    credentials: "omit",
    redirect: "error",
  });
  if (!response.ok || response.redirected || response.url !== location.origin + "/catalog.json") {
    throw new Error("Frischer Katalog ist nicht verfügbar.");
  }
  const catalog = await response.json();
  return { ids, basket: buildStagingBasket(ids, catalog) };
}

function renderEvidence(basket, mode, coverEnabled) {
  const evidence = publicEvidence(basket, { mode, coverEnabled });
  document.querySelector("#qa-evidence").textContent = JSON.stringify(evidence, null, 2);
}

function setStatus(message) {
  document.querySelector("#qa-status").textContent = message;
}

let activeZip = null;
let controller = null;
let busy = false;

function resetTransient() {
  controller?.abort();
  controller = null;
  busy = false;
  if (activeZip) {
    try { activeZip.link.remove(); } catch {}
    try { activeZip.dispose(); } catch {}
    activeZip = null;
  }
  document.querySelector("#qa-download").replaceChildren();
}

async function validateSelection() {
  if (busy) return;
  busy = true;
  resetTransient();
  busy = true;
  try {
    const { basket } = await freshBasket();
    const cover = coverState();
    const total = basket.sheetCount + (cover.enabled ? 1 : 0);
    if (total > 5) throw new Error("Deckblatt würde die 5-Seiten-Grenze überschreiten.");
    renderEvidence(basket, "validate", cover.enabled);
    setStatus("STAGING CHECK: Auswahl ist im frischen öffentlichen Katalog vollständig.");
  } catch (error) {
    document.querySelector("#qa-evidence").textContent = "";
    setStatus("FAIL/BLOCKED: " + (error?.message || "Unbekannter Fehler."));
  } finally {
    busy = false;
  }
}

async function stage(mode) {
  if (busy) return;
  resetTransient();
  busy = true;
  controller = new AbortController();
  const localController = controller;
  try {
    const { ids, basket } = await freshBasket();
    const cover = coverState();
    if (basket.sheetCount + (cover.enabled ? 1 : 0) > 5) {
      throw new Error("Deckblatt würde die 5-Seiten-Grenze überschreiten.");
    }

    const session = await prepareCurrentBookOutputSession(
      basket,
      cover,
      {
        mode,
        origin: location.origin,
        readIds: () => [...ids],
        fetcher: globalThis.fetch,
        signal: localController.signal,
        documentRef: document,
        fonts: document.fonts,
        coverRenderOptions: BOOK_COVER_BROWSER_RENDER_OPTIONS,
      },
    );

    if (mode === "zip") {
      activeZip = session.resource;
      activeZip.link.textContent = "Staging-ZIP speichern";
      activeZip.link.setAttribute("aria-label", "Staging-ZIP speichern");
      document.querySelector("#qa-download").replaceChildren(activeZip.link);
      renderEvidence(basket, "zip", cover.enabled);
      setStatus(
        "STAGING PASS: ZIP wurde aus frischen öffentlichen Print-PNGs vorbereitet. " +
        "Dies ist kein Visitor- oder Release-PASS."
      );
    } else {
      const result = printStagedDocumentInBasketHost(session.resource, {
        documentRef: document,
        signal: localController.signal,
      });
      renderEvidence(basket, "print", cover.enabled);
      setStatus(
        "STAGING PRINT DIALOG CLOSED: " + result.sheetCount +
        " A4-Seite(n) waren vorbereitet. Preview/Schließen ist kein physischer Druck-PASS."
      );
    }
  } catch (error) {
    setStatus("FAIL/BLOCKED: " + (error?.message || "Unbekannter Fehler."));
  } finally {
    if (controller === localController) controller = null;
    busy = false;
  }
}

function clearDraft() {
  resetTransient();
  document.querySelector("#qa-ids").value = "";
  document.querySelector("#qa-cover-enabled").checked = false;
  document.querySelector("#qa-cover-title").value = "Mein Ausmalbuch";
  document.querySelector("#qa-cover-name").value = "";
  document.querySelector("#qa-evidence").textContent = "";
  setStatus("Entwurf gelöscht. Titel/Name wurden nicht gespeichert.");
}

function startHarness() {
  document.querySelector("#qa-validate").addEventListener("click", () => { void validateSelection(); });
  document.querySelector("#qa-zip").addEventListener("click", () => { void stage("zip"); });
  document.querySelector("#qa-print").addEventListener("click", () => { void stage("print"); });
  document.querySelector("#qa-clear").addEventListener("click", clearDraft);
  window.addEventListener("pagehide", resetTransient);
}

if (typeof document !== "undefined") startHarness();
