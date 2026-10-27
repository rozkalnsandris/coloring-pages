// #199 pure ordered preview plan for "Mein Malbuch erstellen".
// Reuses the canonical #206 published-page expansion and #199 five-sheet cover capacity.
// No DOM, fetch, storage, rendering, ZIP, download, or print side effects.
import { expandBasketForExport } from "./print-basket-selection.mjs";
import { planBookSheetCapacity } from "./book-cover-capacity.mjs";

function checkedCoverState(state) {
  if (!state || typeof state !== "object" || Array.isArray(state) ||
      typeof state.enabled !== "boolean" ||
      typeof state.title !== "string" ||
      typeof state.name !== "string") {
    throw new TypeError("Valid in-memory book cover state required");
  }
  return state;
}

export function buildBookPreviewPlan(savedIds, freshCatalog, coverState) {
  const cover = checkedCoverState(coverState);
  const capacity = planBookSheetCapacity(savedIds, freshCatalog, {
    coverEnabled: cover.enabled,
  });
  const artworkPages = expandBasketForExport(savedIds, freshCatalog);

  if (artworkPages.length !== capacity.artworkSheetCount) {
    throw new Error("Preview page count changed; review the selection again");
  }

  const total = capacity.totalSheetCount;
  const items = [];
  if (cover.enabled) {
    // Keep text as literal in-memory data. A later DOM renderer must use a
    // text-safe API and separately pass font/layout/privacy/A4 acceptance.
    items.push(Object.freeze({
      kind: "cover",
      sheetNumber: 1,
      sheetCount: total,
      title: cover.title,
      name: cover.name,
    }));
  }

  const offset = cover.enabled ? 1 : 0;
  artworkPages.forEach((page, index) => {
    items.push(Object.freeze({
      kind: "artwork",
      sheetNumber: index + 1 + offset,
      sheetCount: total,
      activityId: page.activityId,
      pageIndex: page.pageIndex,
      pageCount: page.pageCount,
      printUrl: page.printUrl,
    }));
  });

  return Object.freeze({
    coverEnabled: cover.enabled,
    activityCount: capacity.activityCount,
    artworkSheetCount: capacity.artworkSheetCount,
    sheetCount: total,
    items: Object.freeze(items),
  });
}
