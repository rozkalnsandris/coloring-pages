// Shared source-only selection model for #206. No browser UI, fetch, storage or export side effects.
// Import only after the five-sheet basket's print/ZIP path passes separate review.
export const MAX_BASKET_SHEETS = 5;
const MAX_ACTIVITY_PAGES = 12;
const ACTIVITY_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
// Accept only public, same-site print PNGs scoped to the matching catalogue ID.
// Print-N supports multi-page activities; hash-suffixed names permit immutable repairs.
const PUBLIC_PRINT_PNG = /^\/?media\/([a-z0-9]+(?:-[a-z0-9]+)*)\/print(?:-[a-z0-9]+|\.[a-f0-9]{64})?\.png$/;

function safeId(value) {
  return typeof value === "string" && ACTIVITY_ID.test(value);
}

function printPages(entry) {
  if (!entry || !safeId(entry.id) || typeof entry.title !== "string" || !entry.title.trim()) {
    return null;
  }
  // An explicitly present but empty/malformed pages[] is invalid: never use a
  // legacy top-level print to hide an incomplete multi-page activity.
  const multiPage = Object.hasOwn(entry, "pages");
  const urls = multiPage
    ? Array.isArray(entry.pages) && entry.pages.length > 0
      ? entry.pages.map((page) => page?.print)
      : []
    : [entry.print];
  if (!urls.length || urls.length > MAX_ACTIVITY_PAGES) return null;

  const unique = new Set();
  const canonicalUrls = [];
  for (const url of urls) {
    if (typeof url !== "string") return null;
    const match = PUBLIC_PRINT_PNG.exec(url);
    if (!match || match[1] !== entry.id) return null;
    // Relative catalogue paths must resolve identically on /tiere, detail.html,
    // and every other route. Reject both spellings of the same PNG as duplicates.
    const canonicalUrl = url.startsWith("/") ? url : `/${url}`;
    if (unique.has(canonicalUrl)) return null;
    unique.add(canonicalUrl);
    canonicalUrls.push(canonicalUrl);
  }
  return canonicalUrls.map((printUrl, index) => ({
    activityId: entry.id,
    pageIndex: index + 1,
    pageCount: canonicalUrls.length,
    printUrl,
  }));
}

function catalogueIndex(catalog) {
  if (!Array.isArray(catalog)) throw new TypeError("Fresh catalogue array required");
  const counts = new Map();
  for (const entry of catalog) {
    if (safeId(entry?.id)) counts.set(entry.id, (counts.get(entry.id) || 0) + 1);
  }
  const index = new Map();
  for (const entry of catalog) {
    // Duplicate catalogue IDs are ambiguous even when one entry is malformed.
    if (counts.get(entry?.id) !== 1) continue;
    const pages = printPages(entry);
    if (pages) index.set(entry.id, pages);
  }
  return index;
}

// Reconcile saved IDs against the FRESH published catalogue. Caller must not
// persist a reconciliation after a catalogue fetch failure; this function
// explicitly throws instead of making a failed fetch look like an empty list.
export function reconcileBasket(savedIds, catalog) {
  if (!Array.isArray(savedIds)) throw new TypeError("Basket IDs must be an array");
  const index = catalogueIndex(catalog);
  const seen = new Set();
  const ids = [], pages = [], droppedIds = [];
  for (const id of savedIds) {
    const candidate = index.get(id);
    if (!safeId(id) || seen.has(id) || !candidate || pages.length + candidate.length > MAX_BASKET_SHEETS) {
      droppedIds.push(id);
      continue;
    }
    seen.add(id);
    ids.push(id);
    pages.push(...candidate);
  }
  return { ids, pages, sheetCount: pages.length, droppedIds };
}

// Adding is idempotent. Failure never evicts an already selected activity.
export function addBasketActivity(savedIds, activityId, catalog) {
  const current = reconcileBasket(savedIds, catalog);
  const index = catalogueIndex(catalog);
  const candidate = index.get(activityId);
  if (!safeId(activityId) || !candidate) return { ...current, ok: false, reason: "unavailable" };
  if (current.ids.includes(activityId)) return { ...current, ok: true, reason: "already-selected" };
  if (current.sheetCount + candidate.length > MAX_BASKET_SHEETS) {
    return { ...current, ok: false, reason: "limit" };
  }
  return {
    ...current,
    ids: [...current.ids, activityId],
    pages: [...current.pages, ...candidate],
    sheetCount: current.sheetCount + candidate.length,
    ok: true,
    reason: "added",
  };
}

export function removeBasketActivity(savedIds, activityId, catalog) {
  const current = reconcileBasket(savedIds, catalog);
  return reconcileBasket(current.ids.filter((id) => id !== activityId), catalog);
}

// Move entire activities, never the individual pages inside a Cut & Paste set.
export function moveBasketActivity(savedIds, activityId, direction, catalog) {
  const current = reconcileBasket(savedIds, catalog);
  if (direction !== -1 && direction !== 1) throw new RangeError("Direction must be -1 or 1");
  const index = current.ids.indexOf(activityId);
  const nextIndex = index + direction;
  if (index < 0 || nextIndex < 0 || nextIndex >= current.ids.length) return current;
  const ids = [...current.ids];
  [ids[index], ids[nextIndex]] = [ids[nextIndex], ids[index]];
  return reconcileBasket(ids, catalog);
}

export function clearBasket() {
  return { ids: [], pages: [], sheetCount: 0, droppedIds: [] };
}

// A future exporter must re-fetch the catalogue and actual PNG bytes, reject
// dropped IDs, verify every file and allow a final action only after ALL pass.
// These page URLs are NOT verified PNG bytes or a claim of LIVE availability.
export function expandBasketForExport(savedIds, catalog) {
  const current = reconcileBasket(savedIds, catalog);
  if (!current.ids.length || current.droppedIds.length) {
    throw new Error("Incomplete or empty basket; review selection before export");
  }
  return current.pages;
}
