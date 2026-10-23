// #206 bounded browser-side source for a future basket print session.
// A call prepares a detached, ordered, text-branded A4 document; it never
// mounts pages, enables a button, opens a print dialog, or records analytics.
import { readStoredBasketIds } from "./print-basket-storage.mjs";
import { prepareBasketPrintMedia } from "./print-basket-print-media.mjs";
import { stagePreparedBasketPrintDocument } from "./print-basket-print-staged-document.mjs";

function sameIds(a, b) {
  return Array.isArray(a) && Array.isArray(b) &&
    a.length === b.length && a.every((v, i) => typeof v === "string" && v === b[i]);
}

function samePages(a, b) {
  return Array.isArray(a) && Array.isArray(b) &&
    a.length === b.length && a.every((p, i) => p &&
      p.activityId === b[i].activityId &&
      p.pageIndex === b[i].pageIndex &&
      p.pageCount === b[i].pageCount &&
      p.printUrl === b[i].printUrl);
}

function checkedOrigin(origin) {
  if (typeof origin !== "string") throw new TypeError("Explicit site origin required");
  const url = new URL(origin);
  if (!["https:", "http:"].includes(url.protocol) ||
      url.username || url.password || url.origin !== origin ||
      url.pathname !== "/" || url.search || url.hash) {
    throw new TypeError("Canonical site origin required");
  }
  return url.origin;
}

// Caller supplies the current UI basket snapshot. It must not write storage
// or silently reconcile withdrawn activities. Freshly re-read sessionStorage
// both before network work and after all PNGs have been validated and decoded.
// A selection change during any await discards ALL detached canvases on failure.
export async function stageCurrentBasketPrintSession(
  previousBasket, {
    origin = globalThis.location?.origin,
    readIds = readStoredBasketIds,
    fetcher = globalThis.fetch,
    decode,
    blobFactory,
    documentRef = globalThis.document,
    signal,
  } = {},
) {
  if (typeof readIds !== "function" || typeof fetcher !== "function") {
    throw new TypeError("Browser selection and fetch capabilities required");
  }
  const site = checkedOrigin(origin);
  if (signal?.aborted) throw new Error("Print session aborted");
  const initialIds = readIds();
  if (!sameIds(initialIds, previousBasket?.ids)) {
    throw new Error("Drucksammlung changed; review selection before printing");
  }

  let staged;
  try {
    const url = site + "/catalog.json";
    const response = await fetcher(url, {
      cache: "no-store", credentials: "omit", mode: "same-origin",
      redirect: "error", signal,
    });
    if (signal?.aborted) throw new Error("Print session aborted");
    if (!response || response.status !== 200 || response.redirected ||
        response.url !== url || typeof response.json !== "function") {
      throw new Error("Fresh public catalogue unavailable");
    }
    const freshCatalog = await response.json();
    if (signal?.aborted) throw new Error("Print session aborted");
    if (!Array.isArray(freshCatalog)) throw new TypeError("Fresh catalogue array required");

    // The shared plan enforces a nonempty immutable, published and ordered
    // 1-5 sheet snapshot; the PNG reader is bounded, same-origin and CRC/A4
    // checked. Do not replace this path with thumbnails or private originals.
    const prepared = await prepareBasketPrintMedia(
      initialIds, freshCatalog, previousBasket, { origin: site, fetcher, signal },
    );
    if (signal?.aborted) throw new Error("Print session aborted");
    staged = await stagePreparedBasketPrintDocument(prepared, {
      decode, blobFactory, documentRef, signal,
    });
    if (signal?.aborted ||
        !sameIds(readIds(), initialIds) ||
        !sameIds(previousBasket?.ids, initialIds) ||
        previousBasket?.sheetCount !== staged.plan.sheetCount ||
        !Array.isArray(previousBasket?.droppedIds) ||
        previousBasket.droppedIds.length !== 0 ||
        !samePages(previousBasket?.pages, staged.plan.pages)) {
      throw new Error("Print selection changed during preparation");
    }
    return staged;
  } catch (error) {
    try { staged?.dispose(); } catch { /* already failed, best effort release */ }
    throw error;
  }
}
