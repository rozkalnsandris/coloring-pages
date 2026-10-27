// #199 pure German status/label model for "Mein Malbuch erstellen".
// Consumes the validated preview plan + cursor only. No DOM, storage, network,
// rendering, ZIP, download, analytics, personal-text output, or print effects.
import { MAX_BASKET_SHEETS } from "./print-basket-selection.mjs";

function checkedPlan(plan) {
  if (!plan || typeof plan !== "object" || Array.isArray(plan) ||
      typeof plan.coverEnabled !== "boolean" ||
      !Number.isInteger(plan.artworkSheetCount) || plan.artworkSheetCount < 1 ||
      !Number.isInteger(plan.sheetCount) || plan.sheetCount < 1 ||
      plan.sheetCount > MAX_BASKET_SHEETS ||
      plan.sheetCount !== plan.artworkSheetCount + (plan.coverEnabled ? 1 : 0)) {
    throw new TypeError("Valid book preview plan required");
  }
  return plan;
}

function checkedCursor(plan, cursor) {
  if (!cursor || typeof cursor !== "object" || Array.isArray(cursor) ||
      !Number.isInteger(cursor.sheetNumber) ||
      cursor.sheetCount !== plan.sheetCount ||
      cursor.sheetNumber < 1 || cursor.sheetNumber > plan.sheetCount ||
      cursor.hasPrevious !== (cursor.sheetNumber > 1) ||
      cursor.hasNext !== (cursor.sheetNumber < plan.sheetCount)) {
    throw new TypeError("Preview cursor must match the plan");
  }
  return cursor;
}

export function buildBookPreviewLabels(plan, cursor) {
  const checked = checkedPlan(plan);
  const current = checkedCursor(checked, cursor);

  const selectionText = checked.coverEnabled
    ? `${checked.sheetCount} von ${MAX_BASKET_SHEETS} Druckseiten (1 Deckblatt + ${checked.artworkSheetCount} Ausmalseiten)`
    : `${checked.sheetCount} von ${MAX_BASKET_SHEETS} Druckseiten`;

  return Object.freeze({
    selectionText,
    pageText: `Seite ${current.sheetNumber} von ${current.sheetCount}`,
    previousLabel: "Zurück",
    nextLabel: "Weiter",
    previousDisabled: !current.hasPrevious,
    nextDisabled: !current.hasNext,
  });
}
