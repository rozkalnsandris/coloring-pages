// #199 adapter from the verified book output bundle into the shared #206
// print decode/canvas/footer pipeline. It does not fetch, render a new cover,
// attach DOM, persist personal text, download, print, or record analytics.
import { BOOK_COVER_A4_CONTRACT, validateBookCoverPngStructure } from "./book-cover-a4-contract.mjs";
import { parseBookCoverPngStructure } from "./book-cover-png-parser.mjs";
import { assertCanonicalA4Png, MAX_ZIP_INPUT_BYTES } from "./print-zip-store.mjs";

export const LOCAL_BOOK_COVER_PRINT_URL = "local:book-cover";
const MAX_SHEETS = 5;

function sameArtworkPage(left, right) {
  return left && right &&
    left.activityId === right.activityId &&
    left.pageIndex === right.pageIndex &&
    left.pageCount === right.pageCount &&
    left.printUrl === right.printUrl;
}

function dimensions(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  return Object.freeze({
    width: view.getUint32(16, false),
    height: view.getUint32(20, false),
  });
}

function checkedBundle(bundle) {
  if (!bundle || typeof bundle !== "object" || bundle.disposed === true ||
      typeof bundle.dispose !== "function" ||
      !bundle.plan || !Array.isArray(bundle.plan.artworkPages) ||
      !Array.isArray(bundle.plan.sheets) ||
      typeof bundle.plan.coverEnabled !== "boolean" ||
      !Number.isInteger(bundle.plan.artworkSheetCount) ||
      !Number.isInteger(bundle.plan.sheetCount) ||
      bundle.plan.artworkSheetCount < 1 ||
      bundle.plan.sheetCount < 1 ||
      bundle.plan.sheetCount > MAX_SHEETS ||
      bundle.plan.artworkPages.length !== bundle.plan.artworkSheetCount ||
      bundle.plan.sheets.length !== bundle.plan.sheetCount ||
      !Array.isArray(bundle.artworkDownloads) ||
      bundle.artworkDownloads.length !== bundle.plan.artworkSheetCount) {
    throw new TypeError("Complete undisposed book output bundle required");
  }
  if (bundle.plan.sheetCount !==
      bundle.plan.artworkSheetCount + (bundle.plan.coverEnabled ? 1 : 0)) {
    throw new Error("Book output sheet count mismatch");
  }
  return bundle;
}

function checkedCover(bundle) {
  if (!bundle.plan.coverEnabled) {
    if (bundle.coverPng !== null) {
      throw new TypeError("Coverless book must not retain cover PNG bytes");
    }
    return null;
  }
  if (!(bundle.coverPng instanceof Uint8Array) || bundle.coverPng.byteLength === 0) {
    throw new TypeError("Verified cover PNG bytes required");
  }
  assertCanonicalA4Png(bundle.coverPng);
  const summary = parseBookCoverPngStructure(bundle.coverPng);
  if (!validateBookCoverPngStructure(summary).ok) {
    throw new TypeError("Book cover PNG structure is not exact A4 RGB 300 DPI");
  }
  const { width, height } = BOOK_COVER_A4_CONTRACT;
  if (summary.width !== width || summary.height !== height) {
    throw new TypeError("Book cover must remain portrait A4");
  }
  const planned = bundle.plan.sheets[0];
  if (!planned || planned.kind !== "cover" ||
      planned.sheetNumber !== 1 ||
      planned.sheetCount !== bundle.plan.sheetCount ||
      planned.orientation !== "portrait") {
    throw new TypeError("Book cover plan changed");
  }
  return bundle.coverPng;
}

export function prepareBookPrintMediaFromBundle(bundle) {
  const value = checkedBundle(bundle);
  const cover = checkedCover(value);
  const pages = [];
  const sheets = [];
  let totalBytes = 0;
  let offset = 0;

  if (cover) {
    const coverPage = Object.freeze({
      kind: "cover",
      activityId: "book-cover",
      pageIndex: 1,
      pageCount: 1,
      printUrl: LOCAL_BOOK_COVER_PRINT_URL,
    });
    totalBytes += cover.byteLength;
    if (totalBytes > MAX_ZIP_INPUT_BYTES) {
      throw new RangeError("Book print PNG budget exceeded");
    }
    pages.push(coverPage);
    sheets.push(Object.freeze({
      page: coverPage,
      bytes: cover,
      width: BOOK_COVER_A4_CONTRACT.width,
      height: BOOK_COVER_A4_CONTRACT.height,
      orientation: "portrait",
    }));
    offset = 1;
  }

  for (let index = 0; index < value.plan.artworkSheetCount; index++) {
    const page = value.plan.artworkPages[index];
    const planned = value.plan.sheets[index + offset];
    const download = value.artworkDownloads[index];

    if (!page || planned?.kind !== "artwork" ||
        planned.sheetNumber !== index + 1 + offset ||
        planned.sheetCount !== value.plan.sheetCount ||
        !sameArtworkPage(planned, page) ||
        !download || download.url !== page.printUrl ||
        !(download.bytes instanceof Uint8Array) || download.bytes.byteLength === 0) {
      throw new TypeError("Changed or incomplete book artwork media");
    }

    assertCanonicalA4Png(download.bytes);
    const { width, height } = dimensions(download.bytes);
    totalBytes += download.bytes.byteLength;
    if (totalBytes > MAX_ZIP_INPUT_BYTES) {
      throw new RangeError("Book print PNG budget exceeded");
    }

    pages.push(page);
    sheets.push(Object.freeze({
      page,
      bytes: download.bytes,
      width,
      height,
      orientation: width > height ? "landscape" : "portrait",
    }));
  }

  if (pages.length !== value.plan.sheetCount ||
      sheets.length !== value.plan.sheetCount) {
    throw new Error("Book print media set is incomplete");
  }

  const frozenPages = Object.freeze(pages.slice());
  const plan = Object.freeze({
    coverEnabled: value.plan.coverEnabled,
    sheetCount: frozenPages.length,
    pages: frozenPages,
    imageUrls: Object.freeze(frozenPages.map(page => page.printUrl)),
  });

  return Object.freeze({
    plan,
    sheets: Object.freeze(sheets),
  });
}
