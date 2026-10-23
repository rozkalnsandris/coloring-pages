// Source-only ordered cross-activity print plan for #206.
// No fetch, DOM, canvas, window.print, storage writes, download or LIVE side effects.
// This is NOT a print-ready signal. A later, separately reviewed loader must
// validate/decode every public A4 PNG before enabling one visitor-clicked print.
import { expandBasketForExport, MAX_BASKET_SHEETS } from "./print-basket-selection.mjs";

function sameIds(left, right) {
  return Array.isArray(left) && Array.isArray(right) &&
    left.length === right.length &&
    left.every((id, index) => typeof id === "string" && id === right[index]);
}

function samePage(left, right) {
  return left && right &&
    left.activityId === right.activityId &&
    left.pageIndex === right.pageIndex &&
    left.pageCount === right.pageCount &&
    left.printUrl === right.printUrl;
}

// savedIds are the newly read tab-scoped IDs, freshCatalog is a new successful
// /catalog.json response, and previousBasket is the on-screen selection.
// Requiring ALL three rejects stale sessionStorage, changed URLs and reordered
// or partially withdrawn multi-page activities without changing the basket.
export function buildBasketPrintPlan(savedIds, freshCatalog, previousBasket) {
  if (!previousBasket || !sameIds(savedIds, previousBasket.ids) ||
      !Array.isArray(previousBasket.pages) ||
      !Array.isArray(previousBasket.droppedIds) ||
      previousBasket.droppedIds.length !== 0 ||
      !Number.isInteger(previousBasket.sheetCount) ||
      previousBasket.sheetCount < 1 ||
      previousBasket.sheetCount > MAX_BASKET_SHEETS ||
      previousBasket.pages.length !== previousBasket.sheetCount) {
    throw new TypeError("Unchanged, nonempty current basket snapshot required");
  }

  // The shared catalogue validator enforces unique published activity IDs,
  // canonical same-site /media/<id>/print*.png, atomic pages[] and the 5-sheet cap.
  const freshPages = expandBasketForExport(savedIds, freshCatalog);
  if (freshPages.length !== previousBasket.sheetCount ||
      freshPages.some((page, index) => !samePage(page, previousBasket.pages[index]))) {
    throw new Error("Published print pages changed; review the basket again");
  }

  // Clone and freeze to prevent asynchronous preview/render steps from
  // silently changing the precise set of sheets offered for printing.
  const pages = Object.freeze(freshPages.map((page) => Object.freeze({
    activityId: page.activityId,
    pageIndex: page.pageIndex,
    pageCount: page.pageCount,
    printUrl: page.printUrl,
  })));
  return Object.freeze({
    activityCount: savedIds.length,
    sheetCount: pages.length,
    pages,
    imageUrls: Object.freeze(pages.map((page) => page.printUrl)),
  });
}
