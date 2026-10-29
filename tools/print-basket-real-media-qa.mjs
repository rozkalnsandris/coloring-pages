// Local-only #199 real-media staging harness.
// Served only by tools/print-basket-real-media-qa-server.py. It does not change
// production release flags and is never visitor/LIVE/mobile-memory/paper proof.
import { reconcileBasket } from "../js/print-basket-selection.mjs";
import {
  BOOK_COVER_BROWSER_RENDER_OPTIONS,
} from "../js/book-output-release-gate.mjs";
import { prepareCurrentBookOutputSession } from "../js/book-output-session.mjs";
import { printStagedDocumentInBasketHost } from "../js/print-basket-print-host.mjs";
import {
  auditQaPrivacySurfaces,
  buildQaReceipt,
  captureQaEnvironment,
  createQaAuditedFetch,
  createQaPrivacyCanary,
  privacyAuditPass,
  stageQaReceiptDownload,
} from "./print-basket-real-media-qa-receipt.mjs";

const ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const MAX_PUBLIC_PNG_BYTES = 32 * 1024 * 1024;
const PNG_SIGNATURE = [137, 80, 78, 71, 13, 10, 26, 10];

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

export function parseCanonicalA4PngHeader(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.byteLength < 29) {
    throw new TypeError("PNG bytes required");
  }
  if (PNG_SIGNATURE.some((value, index) => bytes[index] !== value)) {
    throw new Error("PNG signature mismatch");
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const ihdrLength = view.getUint32(8, false);
  const ihdrType = String.fromCharCode(bytes[12], bytes[13], bytes[14], bytes[15]);
  if (ihdrLength !== 13 || ihdrType !== "IHDR") {
    throw new Error("PNG IHDR missing");
  }
  const width = view.getUint32(16, false);
  const height = view.getUint32(20, false);
  const bitDepth = bytes[24];
  const colorType = bytes[25];
  const orientation =
    width === 2480 && height === 3508 ? "portrait" :
    width === 3508 && height === 2480 ? "landscape" :
    null;
  if (!orientation || bitDepth !== 8 || colorType !== 2) {
    throw new Error("Public print PNG is not canonical RGB8 A4");
  }
  return Object.freeze({ width, height, bitDepth, colorType, orientation });
}

function checkedOrigin(origin) {
  if (typeof origin !== "string") throw new TypeError("origin required");
  const url = new URL(origin);
  if (!["http:", "https:"].includes(url.protocol) ||
      url.username || url.password ||
      url.origin !== origin ||
      url.pathname !== "/" ||
      url.search || url.hash) {
    throw new TypeError("exact browser origin required");
  }
  return url.origin;
}

async function sha256Hex(bytes, cryptoRef) {
  if (!cryptoRef?.subtle || typeof cryptoRef.subtle.digest !== "function") {
    throw new Error("SHA-256 browser capability unavailable");
  }
  const digest = new Uint8Array(await cryptoRef.subtle.digest("SHA-256", bytes));
  return [...digest].map(value => value.toString(16).padStart(2, "0")).join("");
}

export async function collectPublicMediaEvidence(
  basket,
  {
    origin,
    fetcher = globalThis.fetch,
    cryptoRef = globalThis.crypto,
    signal,
  } = {},
) {
  if (!basket || !Array.isArray(basket.pages) || !basket.pages.length ||
      typeof fetcher !== "function") {
    throw new TypeError("complete staging basket and fetcher required");
  }
  const site = checkedOrigin(origin);
  const evidence = [];

  for (const page of basket.pages) {
    if (signal?.aborted) throw new Error("QA media audit aborted");
    const url = site + page.printUrl;
    const response = await fetcher(url, {
      cache: "no-store",
      credentials: "omit",
      redirect: "error",
      signal,
    });
    if (!response || response.status !== 200 ||
        response.redirected || response.url !== url ||
        typeof response.arrayBuffer !== "function") {
      throw new Error("Public print PNG response is not exact HTTP 200");
    }
    const mime = response.headers?.get?.("content-type")?.split(";")[0]?.trim();
    if (mime !== "image/png") {
      throw new Error("Public print media MIME is not image/png");
    }
    const declared = response.headers?.get?.("content-length");
    if (declared !== null && declared !== undefined && declared !== "") {
      const length = Number(declared);
      if (!Number.isSafeInteger(length) || length < 1 || length > MAX_PUBLIC_PNG_BYTES) {
        throw new Error("Public print PNG content length outside QA bound");
      }
    }

    const bytes = new Uint8Array(await response.arrayBuffer());
    if (!bytes.byteLength || bytes.byteLength > MAX_PUBLIC_PNG_BYTES) {
      throw new Error("Public print PNG bytes outside QA bound");
    }
    const header = parseCanonicalA4PngHeader(bytes);
    const sha256 = await sha256Hex(bytes, cryptoRef);
    evidence.push(Object.freeze({
      activityId: page.activityId,
      pageIndex: page.pageIndex,
      pageCount: page.pageCount,
      printUrl: page.printUrl,
      httpStatus: 200,
      mime: "image/png",
      bytes: bytes.byteLength,
      sha256,
      width: header.width,
      height: header.height,
      orientation: header.orientation,
    }));
  }

  return Object.freeze(evidence);
}

export function publicEvidence(
  basket,
  {
    mode = "validate",
    coverEnabled = false,
    publicMedia = [],
  } = {},
) {
  if (!basket || !Array.isArray(basket.ids) || !Array.isArray(basket.pages) ||
      !Array.isArray(publicMedia)) {
    throw new TypeError("Valid staging basket/evidence required");
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
    publicMedia: Object.freeze(publicMedia.map(item => Object.freeze({ ...item }))),
  });
}

function coverState() {
  return Object.freeze({
    enabled: document.querySelector("#qa-cover-enabled").checked,
    title: document.querySelector("#qa-cover-title").value,
    name: document.querySelector("#qa-cover-name").value,
  });
}

async function freshContext(fetcher) {
  const response = await fetcher("/qa/context.json", {
    cache: "no-store",
    credentials: "omit",
    redirect: "error",
  });
  if (!response.ok || response.redirected ||
      response.url !== location.origin + "/qa/context.json") {
    throw new Error("QA source context is unavailable.");
  }
  const value = await response.json();
  if (!value || value.status !== "STAGING ONLY" ||
      typeof value.sourceSha !== "string" ||
      !/^[a-f0-9]{40}$/.test(value.sourceSha) ||
      typeof value.publicOrigin !== "string") {
    throw new Error("QA source context is invalid.");
  }
  return value;
}

async function freshBasket(fetcher) {
  const ids = parseActivityIds(document.querySelector("#qa-ids").value);
  const response = await fetcher("/catalog.json", {
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

function resourceEntryCount() {
  try {
    const entries = performance.getEntriesByType("resource");
    return Array.isArray(entries) ? entries.length : 0;
  } catch {
    return 0;
  }
}

function setStatus(message) {
  document.querySelector("#qa-status").textContent = message;
}

let activeZip = null;
let activeReceipt = null;
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
  if (activeReceipt) {
    try { activeReceipt.link.remove(); } catch {}
    try { activeReceipt.dispose(); } catch {}
    activeReceipt = null;
  }
  document.querySelector("#qa-download").replaceChildren();
  document.querySelector("#qa-receipt-download").replaceChildren();
}

function publishReceipt(receipt) {
  document.querySelector("#qa-evidence").textContent = JSON.stringify(receipt, null, 2);
  activeReceipt = stageQaReceiptDownload(receipt);
  document.querySelector("#qa-receipt-download").replaceChildren(activeReceipt.link);
}

function operationPrivacy(tokens, startIndex) {
  return auditQaPrivacySurfaces(tokens, {
    locationRef: location,
    documentRef: document,
    sessionStorageRef: globalThis.sessionStorage,
    localStorageRef: globalThis.localStorage,
    performanceRef: globalThis.performance,
    resourceStartIndex: startIndex,
  });
}

async function validateSelection() {
  if (busy) return;
  resetTransient();
  busy = true;
  controller = new AbortController();
  const localController = controller;
  const cover = coverState();
  const tokens = cover.enabled ? [cover.title, cover.name].filter(Boolean) : [];
  const requestAudit = [];
  const startIndex = resourceEntryCount();
  const auditedFetch = createQaAuditedFetch(globalThis.fetch, {
    origin: location.origin,
    tokens,
    entries: requestAudit,
  });

  try {
    const sourceContext = await freshContext(auditedFetch);
    const { basket } = await freshBasket(auditedFetch);
    const total = basket.sheetCount + (cover.enabled ? 1 : 0);
    if (total > 5) throw new Error("Deckblatt würde die 5-Seiten-Grenze überschreiten.");
    const media = await collectPublicMediaEvidence(basket, {
      origin: location.origin,
      fetcher: auditedFetch,
      cryptoRef: globalThis.crypto,
      signal: localController.signal,
    });
    const evidence = publicEvidence(basket, {
      mode: "validate",
      coverEnabled: cover.enabled,
      publicMedia: media,
    });
    const privacy = operationPrivacy(tokens, startIndex);
    const receipt = buildQaReceipt({
      sourceContext,
      environment: captureQaEnvironment(),
      publicEvidence: evidence,
      requestAudit,
      privacyAudit: privacy,
      outcome: {
        mode: "validate",
        result: "STAGING PASS",
        note: "Public PNG bytes, SHA-256 and canonical A4 geometry recorded.",
      },
    });
    publishReceipt(receipt);
    setStatus(
      "STAGING CHECK: Öffentliche Print-PNGs sind vollständig; Receipt ist speicherbar."
    );
  } catch (error) {
    document.querySelector("#qa-evidence").textContent = "";
    setStatus("FAIL/BLOCKED: " + (error?.message || "Unbekannter Fehler."));
  } finally {
    if (controller === localController) controller = null;
    busy = false;
  }
}

async function stage(mode) {
  if (busy) return;
  resetTransient();
  busy = true;
  controller = new AbortController();
  const localController = controller;
  const cover = coverState();
  const tokens = cover.enabled ? [cover.title, cover.name].filter(Boolean) : [];
  const requestAudit = [];
  const startIndex = resourceEntryCount();
  const auditedFetch = createQaAuditedFetch(globalThis.fetch, {
    origin: location.origin,
    tokens,
    entries: requestAudit,
  });

  try {
    const sourceContext = await freshContext(auditedFetch);
    const { ids, basket } = await freshBasket(auditedFetch);
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
        fetcher: auditedFetch,
        signal: localController.signal,
        documentRef: document,
        fonts: document.fonts,
        coverRenderOptions: BOOK_COVER_BROWSER_RENDER_OPTIONS,
      },
    );

    let note;
    if (mode === "zip") {
      activeZip = session.resource;
      activeZip.link.textContent = "Staging-ZIP speichern";
      activeZip.link.setAttribute("aria-label", "Staging-ZIP speichern");
      document.querySelector("#qa-download").replaceChildren(activeZip.link);
      note = "ZIP was staged from the reviewed output session.";
      setStatus(
        "STAGING PASS: ZIP wurde vorbereitet. Dies ist kein Visitor- oder Release-PASS."
      );
    } else {
      const result = printStagedDocumentInBasketHost(session.resource, {
        documentRef: document,
        signal: localController.signal,
      });
      note = result.sheetCount + " A4 sheet(s) were staged before the print dialog closed.";
      setStatus(
        "STAGING PRINT DIALOG CLOSED: " + result.sheetCount +
        " A4-Seite(n) waren vorbereitet. Dies ist kein physischer Druck-PASS."
      );
    }

    const evidence = publicEvidence(basket, {
      mode,
      coverEnabled: cover.enabled,
    });
    const privacy = operationPrivacy(tokens, startIndex);
    const receipt = buildQaReceipt({
      sourceContext,
      environment: captureQaEnvironment(),
      publicEvidence: evidence,
      requestAudit,
      privacyAudit: privacy,
      outcome: {
        mode,
        result: "STAGING PASS",
        note,
      },
    });
    publishReceipt(receipt);
  } catch (error) {
    setStatus("FAIL/BLOCKED: " + (error?.message || "Unbekannter Fehler."));
  } finally {
    if (controller === localController) controller = null;
    busy = false;
  }
}

async function runPrivacyCanary() {
  if (busy) return;
  resetTransient();
  busy = true;
  controller = new AbortController();
  const localController = controller;
  const canary = createQaPrivacyCanary(globalThis.crypto);
  const tokens = [canary.title, canary.name];
  const requestAudit = [];
  const startIndex = resourceEntryCount();
  const auditedFetch = createQaAuditedFetch(globalThis.fetch, {
    origin: location.origin,
    tokens,
    entries: requestAudit,
  });

  try {
    const sourceContext = await freshContext(auditedFetch);
    const { ids, basket } = await freshBasket(auditedFetch);
    if (basket.sheetCount + 1 > 5) {
      throw new Error("Datenschutz-Canary benötigt eine freie Deckblatt-Seite.");
    }

    const session = await prepareCurrentBookOutputSession(
      basket,
      Object.freeze({
        enabled: true,
        title: canary.title,
        name: canary.name,
      }),
      {
        mode: "zip",
        origin: location.origin,
        readIds: () => [...ids],
        fetcher: auditedFetch,
        signal: localController.signal,
        documentRef: document,
        fonts: document.fonts,
        coverRenderOptions: BOOK_COVER_BROWSER_RENDER_OPTIONS,
      },
    );
    session.resource.dispose();

    const privacy = operationPrivacy(tokens, startIndex);
    if (!privacyAuditPass(privacy)) {
      throw new Error("Datenschutz-Canary konnte nicht vollständig als lokal bestätigt werden.");
    }
    const evidence = publicEvidence(basket, {
      mode: "privacy-canary",
      coverEnabled: true,
    });
    const receipt = buildQaReceipt({
      sourceContext,
      environment: captureQaEnvironment(),
      publicEvidence: evidence,
      requestAudit,
      privacyAudit: privacy,
      outcome: {
        mode: "privacy-canary",
        result: "STAGING PASS",
        note: "Synthetic cover canary stayed out of audited request URLs, storage and resource URLs.",
      },
    });
    publishReceipt(receipt);
    setStatus(
      "STAGING PRIVACY PASS: Synthetischer Deckblatt-Canary blieb außerhalb der geprüften Netzwerk-/Storage-Flächen."
    );
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
  document.querySelector("#qa-privacy").addEventListener("click", () => { void runPrivacyCanary(); });
  document.querySelector("#qa-clear").addEventListener("click", clearDraft);
  window.addEventListener("pagehide", resetTransient);
}

if (typeof document !== "undefined") startHarness();
