// #206 source-only decode gate for a previously validated 1–5-sheet print set.
// This neither renders paper sheets nor enables any print or download action.
// Caller must first use prepareBasketPrintMedia with the fresh catalogue.
import { assertCanonicalA4Png, MAX_ZIP_INPUT_BYTES } from "./print-zip-store.mjs";

const MAX_SHEETS = 5;
const validA4 = (width, height) =>
  (width === 2480 && height === 3508) ||
  (width === 3508 && height === 2480);

function checkedSheets(prepared) {
  const plan = prepared?.plan;
  const sheets = prepared?.sheets;
  if (!plan || !Array.isArray(plan.pages) ||
      !Number.isInteger(plan.sheetCount) ||
      plan.sheetCount < 1 || plan.sheetCount > MAX_SHEETS ||
      !Array.isArray(sheets) || sheets.length !== plan.sheetCount ||
      plan.pages.length !== plan.sheetCount ||
      !Array.isArray(plan.imageUrls) || plan.imageUrls.length !== plan.sheetCount) {
    throw new TypeError("A complete ordered print-media preflight is required");
  }
  let inputBytes = 0;
  const urls = new Set();
  for (let index = 0; index < sheets.length; index++) {
    const sheet = sheets[index], page = plan.pages[index];
    if (!sheet || !page || sheet.page !== page ||
        typeof page.printUrl !== "string" ||
        page.printUrl !== plan.imageUrls[index] ||
        urls.has(page.printUrl) ||
        !(sheet.bytes instanceof Uint8Array) ||
        !Number.isInteger(sheet.width) || !Number.isInteger(sheet.height) ||
        !validA4(sheet.width, sheet.height) ||
        sheet.orientation !== (sheet.width > sheet.height ? "landscape" : "portrait")) {
      throw new TypeError("Changed or incomplete ordered A4 print sheet");
    }
    inputBytes += sheet.bytes.byteLength;
    if (inputBytes > MAX_ZIP_INPUT_BYTES) throw new RangeError("Print PNG budget exceeded");
    assertCanonicalA4Png(sheet.bytes);
    const view = new DataView(
      sheet.bytes.buffer, sheet.bytes.byteOffset, sheet.bytes.byteLength,
    );
    if (view.getUint32(16, false) !== sheet.width ||
        view.getUint32(20, false) !== sheet.height) {
      throw new TypeError("Print PNG metadata does not match file dimensions");
    }
    urls.add(page.printUrl);
  }
  return sheets;
}

function safeClose(bitmap) {
  try { bitmap?.close?.(); } catch { /* Best effort after decoded resource ownership. */ }
}

// ImageBitmap decoding is deliberately sequential, never one Promise.all per
// 35 MB A4 raster. Abort is checked after the awaiting decoder, so a late
// decode completion also closes ALL successfully created bitmaps.
export async function decodeBasketPrintMedia(
  prepared,
  { decode = globalThis.createImageBitmap, blobFactory = (bytes) =>
    new Blob([bytes], { type: "image/png" }), signal } = {},
) {
  if (signal?.aborted) throw new Error("Print image decoding aborted");
  const sheets = checkedSheets(prepared); // Validate the whole batch before decoding.
  if (typeof decode !== "function" || typeof blobFactory !== "function") {
    throw new TypeError("Browser image decoder is unavailable");
  }
  const owned = [];
  let released = false;
  const release = () => {
    if (released) return;
    released = true;
    for (const bitmap of owned) safeClose(bitmap);
    owned.length = 0;
  };

  try {
    const decoded = [];
    for (const sheet of sheets) {
      if (signal?.aborted) throw new Error("Print image decoding aborted");
      const blob = blobFactory(sheet.bytes);
      if (!blob || blob.type !== "image/png" || blob.size !== sheet.bytes.byteLength) {
        throw new TypeError("Print decoder input must preserve PNG bytes");
      }
      const bitmap = await decode(blob);
      if (!bitmap || typeof bitmap.close !== "function") {
        safeClose(bitmap);
        throw new TypeError("Decoded image cannot be released");
      }
      owned.push(bitmap);
      if (signal?.aborted) throw new Error("Print image decoding aborted");
      if (bitmap.width !== sheet.width || bitmap.height !== sheet.height) {
        throw new TypeError("Decoded A4 image dimensions differ from PNG");
      }
      decoded.push(Object.freeze({
        page: sheet.page,
        width: sheet.width,
        height: sheet.height,
        orientation: sheet.orientation,
        bitmap,
      }));
    }
    return Object.freeze({
      plan: prepared.plan,
      sheets: Object.freeze(decoded),
      get released() { return released; },
      release,
    });
  } catch (error) {
    release();
    throw error;
  }
}
