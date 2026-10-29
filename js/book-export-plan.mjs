// #199 pure cover-aware export/print ordering plan for "Mein Malbuch".
// Reuses #206's fresh-catalogue basket print plan and #199 five-sheet capacity.
// It deliberately omits visitor title/name and performs no rendering, fetch,
// storage, ZIP creation, DOM work, download, printing or telemetry.
import { planBookSheetCapacity } from "./book-cover-capacity.mjs";
import { buildBasketPrintPlan } from "./print-basket-print-plan.mjs";

function checkedCoverState(state) {
  if (!state || typeof state !== "object" || Array.isArray(state) ||
      typeof state.enabled !== "boolean" ||
      typeof state.title !== "string" ||
      typeof state.name !== "string") {
    throw new TypeError("Valid in-memory book cover state required");
  }
  return state;
}

export function buildBookExportPlan(
  savedIds,
  freshCatalog,
  previousBasket,
  coverState,
) {
  const cover = checkedCoverState(coverState);
  const artwork = buildBasketPrintPlan(savedIds, freshCatalog, previousBasket);
  const capacity = planBookSheetCapacity(savedIds, freshCatalog, {
    coverEnabled: cover.enabled,
  });

  if (capacity.activityCount !== artwork.activityCount ||
      capacity.artworkSheetCount !== artwork.sheetCount) {
    throw new Error("Book export selection changed; review the basket again");
  }

  const sheets = [];
  if (cover.enabled) {
    sheets.push(Object.freeze({
      kind: "cover",
      sheetNumber: 1,
      sheetCount: capacity.totalSheetCount,
      orientation: "portrait",
    }));
  }

  const offset = cover.enabled ? 1 : 0;
  artwork.pages.forEach((page, index) => {
    sheets.push(Object.freeze({
      kind: "artwork",
      sheetNumber: index + 1 + offset,
      sheetCount: capacity.totalSheetCount,
      activityId: page.activityId,
      pageIndex: page.pageIndex,
      pageCount: page.pageCount,
      printUrl: page.printUrl,
    }));
  });

  if (sheets.length !== capacity.totalSheetCount) {
    throw new Error("Book export sheet count mismatch");
  }

  return Object.freeze({
    coverEnabled: cover.enabled,
    activityCount: capacity.activityCount,
    artworkSheetCount: capacity.artworkSheetCount,
    sheetCount: capacity.totalSheetCount,
    artworkPages: artwork.pages,
    sheets: Object.freeze(sheets),
  });
}
