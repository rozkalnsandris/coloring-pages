// #199 pure preview-media resolver for "Mein Malbuch erstellen".
// Artwork preview UI must use published watermarked preview.webp / preview-N.webp,
// never full-resolution print PNGs as display media. No DOM, storage, fetch,
// rendering, ZIP, download, analytics, or print side effects.
import { buildBookPreviewView } from "./book-preview-view.mjs";

const ACTIVITY_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const PUBLIC_PRINT_PNG = /^\/?media\/([a-z0-9]+(?:-[a-z0-9]+)*)\/print(?:-[a-z0-9]+|\.[a-f0-9]{64})?\.png$/;
const SINGLE_PREVIEW = /^\/?media\/([a-z0-9]+(?:-[a-z0-9]+)*)\/preview\.webp$/;
const MULTI_PREVIEW = /^\/?media\/([a-z0-9]+(?:-[a-z0-9]+)*)\/preview-([1-9][0-9]*)\.webp$/;

function canonical(value, pattern, activityId, pageIndex = null) {
  if (typeof value !== "string") return null;
  const match = pattern.exec(value);
  if (!match || match[1] !== activityId) return null;
  if (pageIndex !== null && Number(match[2]) !== pageIndex) return null;
  return value.startsWith("/") ? value : `/${value}`;
}

function uniqueEntry(catalog, activityId) {
  if (!Array.isArray(catalog) || typeof activityId !== "string" ||
      !ACTIVITY_ID.test(activityId)) {
    throw new TypeError("Fresh catalogue and valid activity ID required");
  }
  const matches = catalog.filter((entry) => entry?.id === activityId);
  if (matches.length !== 1) {
    throw new Error("Preview catalogue entry is missing or ambiguous");
  }
  return matches[0];
}

function validatedPreviewPages(entry, expectedPageCount) {
  const id = entry.id;
  if (Object.hasOwn(entry, "pages")) {
    if (!Array.isArray(entry.pages) ||
        entry.pages.length !== expectedPageCount ||
        expectedPageCount < 1) {
      throw new Error("Preview activity page count changed");
    }
    return entry.pages.map((page, index) => {
      const pageIndex = index + 1;
      const printUrl = canonical(page?.print, PUBLIC_PRINT_PNG, id);
      const previewUrl = canonical(page?.preview, MULTI_PREVIEW, id, pageIndex);
      if (!printUrl || !previewUrl) {
        throw new Error("Published multipage preview media is invalid");
      }
      return Object.freeze({ printUrl, previewUrl });
    });
  }

  if (expectedPageCount !== 1) {
    throw new Error("Legacy preview cannot represent multiple pages");
  }
  const printUrl = canonical(entry.print, PUBLIC_PRINT_PNG, id);
  const previewUrl = canonical(entry.preview, SINGLE_PREVIEW, id);
  if (!printUrl || !previewUrl) {
    throw new Error("Published single-page preview media is invalid");
  }
  return [Object.freeze({ printUrl, previewUrl })];
}

export function buildBookPreviewDisplay(plan, cursor, freshCatalog) {
  const view = buildBookPreviewView(plan, cursor);
  if (view.content.kind === "cover") {
    return Object.freeze({
      ...view,
      content: Object.freeze({ ...view.content }),
    });
  }

  const content = view.content;
  const entry = uniqueEntry(freshCatalog, content.activityId);
  const pages = validatedPreviewPages(entry, content.pageCount);
  const page = pages[content.pageIndex - 1];
  if (!page || page.printUrl !== content.printUrl) {
    throw new Error("Preview media no longer matches the selected print page");
  }

  return Object.freeze({
    selectionText: view.selectionText,
    pageText: view.pageText,
    previous: view.previous,
    next: view.next,
    content: Object.freeze({
      kind: "artwork",
      activityId: content.activityId,
      pageIndex: content.pageIndex,
      pageCount: content.pageCount,
      previewUrl: page.previewUrl,
    }),
  });
}
