// #199 pure DOM-agnostic preview view model for "Mein Malbuch erstellen".
// Combines the validated preview plan/cursor with German status labels. Personal
// cover text stays in-memory in cover content only. No DOM, HTML parsing,
// storage, network, rendering, ZIP, download, analytics, or print side effects.
import { buildBookPreviewLabels } from "./book-preview-labels.mjs";

function checkedActiveItem(plan, sheetNumber) {
  if (!plan || typeof plan !== "object" || Array.isArray(plan) ||
      !Array.isArray(plan.items) || plan.items.length !== plan.sheetCount) {
    throw new TypeError("Valid ordered book preview items required");
  }
  const item = plan.items[sheetNumber - 1];
  if (!item || typeof item !== "object" || Array.isArray(item) ||
      item.sheetNumber !== sheetNumber ||
      item.sheetCount !== plan.sheetCount ||
      (item.kind !== "cover" && item.kind !== "artwork")) {
    throw new TypeError("Active preview item does not match the cursor");
  }
  return item;
}

function coverContent(plan, item) {
  if (!plan.coverEnabled || item.sheetNumber !== 1 ||
      typeof item.title !== "string" || typeof item.name !== "string") {
    throw new TypeError("Valid in-memory cover preview item required");
  }
  return Object.freeze({
    kind: "cover",
    title: item.title,
    name: item.name,
  });
}

function artworkContent(item) {
  if (typeof item.activityId !== "string" ||
      !Number.isInteger(item.pageIndex) || item.pageIndex < 1 ||
      !Number.isInteger(item.pageCount) || item.pageCount < item.pageIndex ||
      typeof item.printUrl !== "string") {
    throw new TypeError("Valid artwork preview item required");
  }
  return Object.freeze({
    kind: "artwork",
    activityId: item.activityId,
    pageIndex: item.pageIndex,
    pageCount: item.pageCount,
    printUrl: item.printUrl,
  });
}

export function buildBookPreviewView(plan, cursor) {
  // This call is also the canonical validation for sheet-count/navigation labels.
  const labels = buildBookPreviewLabels(plan, cursor);
  const item = checkedActiveItem(plan, cursor.sheetNumber);
  const content = item.kind === "cover"
    ? coverContent(plan, item)
    : artworkContent(item);

  return Object.freeze({
    selectionText: labels.selectionText,
    pageText: labels.pageText,
    previous: Object.freeze({
      label: labels.previousLabel,
      disabled: labels.previousDisabled,
    }),
    next: Object.freeze({
      label: labels.nextLabel,
      disabled: labels.nextDisabled,
    }),
    content,
  });
}
