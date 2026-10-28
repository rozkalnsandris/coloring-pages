// #199 inert, source-only cover capacity model for "Mein Malbuch erstellen".
// Reuse #206's canonical catalogue validation and five-physical-A4-sheet limit.
// No cover rendering, personal text, storage, download or visitor print action.
import { MAX_BASKET_SHEETS, reconcileBasket } from "./print-basket-selection.mjs";

export function planBookSheetCapacity(savedIds, freshCatalog, { coverEnabled = false } = {}) {
  if (typeof coverEnabled !== "boolean") {
    throw new TypeError("Cover flag must be a boolean");
  }
  // Never silently drop withdrawn, duplicate, malformed or over-limit activities
  // when preparing a book. Each Cut & Paste activity remains one atomic block.
  const basket = reconcileBasket(savedIds, freshCatalog);
  if (basket.droppedIds.length) {
    throw new Error("Incomplete book selection; review the published catalogue");
  }
  if (coverEnabled && basket.sheetCount === 0) {
    throw new RangeError("A cover needs at least one selected artwork sheet");
  }
  const coverSheetCount = coverEnabled ? 1 : 0;
  const totalSheetCount = basket.sheetCount + coverSheetCount;
  if (totalSheetCount > MAX_BASKET_SHEETS) {
    throw new RangeError("Cover would exceed five physical A4 sheets");
  }
  // This is capacity evidence only, never proof that the cover PNG or printing
  // has passed mobile, browser, or physical-paper QA.
  return Object.freeze({
    activityCount: basket.ids.length,
    artworkSheetCount: basket.sheetCount,
    coverSheetCount,
    totalSheetCount,
    remainingSheetSlots: MAX_BASKET_SHEETS - totalSheetCount,
    maxSheetCount: MAX_BASKET_SHEETS,
  });
}
